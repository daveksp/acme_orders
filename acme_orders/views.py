__author__ = 'david'

import ast
import csv
from datetime import datetime
import json
import os
import uuid

from flask import jsonify, request, render_template, url_for

from acme_orders import app, celery, service
from acme_orders.logger.log import create_logger, log
from acme_orders.models import get_session, Order

logger = create_logger(__name__)


def create_response_base(uuid_value):
    if uuid_value is None:
        uuid_value = uuid.uuid4()
    return dict(result=[], status_code=500, uuid=uuid_value, message='')



@app.route('/acme_orders/api/v1/orders', methods=['GET'])
def list_imported_orders():
    limit = request.args.get('limit')
    offset = request.args.get('offset')

    response = create_response_base(request.args.get('uuid'))
    log(logger, response['uuid'], 'starting request', params=request.args)
    level = 'info'
    response['status_code'] = 200
    desired_fields = ['id', 'valid', 'name']

    if limit is not None and not limit.isdigit():
        response['message'] = 'limit must be a number! '
        response['status_code'] = 402
    if offset is not None and not offset.isdigit():
        response['message'] += 'offset must be a number!'
        response['status_code'] = 402
    
    if response['status_code'] == 200:
        session = get_session()
        query = session.query(Order)
        query = query.limit(limit) if limit else query
        query = query.offset(offset) if offset else query

        orders = query.all()

        response['result'] = ([
            {field: getattr(order, field) for field in desired_fields} 
                for order in orders
        ])

    log(logger, response['uuid'], response, level=level)
    return jsonify(response), response['status_code']


@app.route('/acme_orders/api/v1/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    response = create_response_base(request.args.get('uuid'))
    log(logger, response['uuid'], 'starting request', params=request.args)
    level = 'info'
    response['status_code'] = 200
    desired_fields = [
        'id', 'valid', 'name', 'email', 'state', 
        'zipcode', 'errors', 'birthday'
    ]

    session = get_session()
    order = session.query(Order).filter(Order.id==order_id).first()

    imported_orders = {field: getattr(order, field) for field in desired_fields} 
    imported_orders['birthday'] = imported_orders['birthday'].strftime("%B %d, %Y") 

    response['result'] = imported_orders
    log(logger, response['uuid'], response, level=level)
    return jsonify(response), response['status_code']


@app.route('/acme_orders/api/v1/orders/import', methods=['PUT'])
def upload_csv():
    csv_file = request.files.get('csv_file')
    
    response = create_response_base(request.args.get('uuid'))
    log(logger, response['uuid'], 'starting request', params=request.args)
    level = 'info'
    response['status_code'] = 200

    tmp_file_name = '/tmp/{}.csv'.format(response['uuid']) 
    csv_file.save(tmp_file_name)

    task = service.import_cvs_orders.apply_async(args=[tmp_file_name, response['uuid']])
    response['message'] = 'starting importing proccess'
        
    log(logger, response['uuid'], response, level=level)
    return jsonify(response), response['status_code'], {
        'location': url_for('get_status') + '?task_id=' + task.id}


@app.route('/acme_orders/api/v1/orders/import/status', methods=['GET'])
def get_status():
    response = create_response_base(request.args.get('uuid')) 
    log(logger, response['uuid'], 'starting request', params=request.args)
    level = 'info'
    response['status_code'] = 200

    task_id = request.args.get('task_id')
    task = service.import_cvs_orders.AsyncResult(task_id)
    if task.info is not None:
        if task.status == 'SUCCESS':
            os.remove(task.info.get('file_name'))

        result = dict(status=task.state, current=task.info.get('current'),
                      message=task.info.get('msg'))
    
    else:
        result = dict(status='PENDING', current=0,
                      message='starting importing proccess')

    

    response['result'] = result
    log(logger, response['uuid'], response, level=level)
    return jsonify(response), response['status_code']


@app.route('/acme_orders')
def init_page():
    return render_template('index.html')
    

@app.errorhandler(404)
def not_found(error):
    """handler for not_found error"""

    response = create_response_base(request.args.get('uuid')) 
    log(logger, response['uuid'], 'starting request', params=request.args)

    response['status_code'] = 404
    response['message'] = 'endpoint not found'
    log(logger, response['uuid'], response, level='error')
    return jsonify(response), response['status_code']
