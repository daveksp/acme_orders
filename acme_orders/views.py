__author__ = 'david'

import ast
import csv
from datetime import datetime
import json
import os
import uuid

from flask import jsonify, make_response, request, render_template, url_for
from flask.ext.babel import gettext
from flask.ext.restful import marshal ,reqparse, Resource
from flask_restful.inputs import boolean, regex
from werkzeug.datastructures import FileStorage

from acme_orders import app, api, celery
from acme_orders.services import importer, order  
from acme_orders.logger.log import create_logger, log
from acme_orders.models import get_session, Order
from acme_orders.util import create_base_response, is_allowed_file

logger = create_logger(__name__)

class OrderAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('limit', type=int, required=False, 
                                   location='args', help=gettext('limit_help_msg'))
        
        self.reqparse.add_argument('offset', type=int, required=False, 
                                   location='args', help=gettext('offset_help_msg'))
        
        self.reqparse.add_argument('uuid', type=str, required=False, location='args')
        
        self.reqparse.add_argument('valid', type=boolean, required=False, location='args', 
                                   help=gettext('valid_help_msg'))
        
        self.reqparse.add_argument('state', type=regex('^[a-zA-Z]{2}$'), required=False, location='args', 
                                   help=gettext('state_help_msg'))
        
        super(OrderAPI, self).__init__()

    
    def get(self, order_id=None):
        args = self.reqparse.parse_args()
        response = create_base_response()
        desired_fields = ['id', 'valid', 'name']
        allowed_filters = ['valid', 'state']
        
        if not order_id:
            filters = {}
            limit = args['limit']
            offset = args['offset']
            
            filters = ({_filter: args[_filter] 
                for _filter in allowed_filters if args[_filter] is not None})

            response['result'] = order.get_order_list(limit=limit, offset=offset, filters=filters)
        else:
            response['result'] = order.get_order_by_id(order_id)

        log(logger, response['uuid'], response)
        return jsonify(response)



class ImporterAPI(Resource):

    def __init__(self):
        csv_file_help_msg = 'a csv file is required'

        self.reqparse = reqparse.RequestParser()
        if request.method == 'PUT':
            self.reqparse.add_argument('csv_file', type=FileStorage, 
                                       required=True, location='files', 
                                       help=gettext('csv_file_help_msg'))

        self.reqparse.add_argument('uuid', type=str, required=False, 
                                   location='args')

        super(ImporterAPI, self).__init__()

    
    def put(self):
        args = self.reqparse.parse_args()
        response = create_base_response()
        csv_file = args['csv_file']

        if not is_allowed_file(csv_file.filename):
            response['status_code'] = 402
            response['message'] = gettext('file_extension_not_allowed_msg')
            return make_response(jsonify(response), response['status_code'])       

        tmp_file_name = '/tmp/{}.csv'.format(response['uuid']) 
        csv_file.save(tmp_file_name)

        task = importer.import_cvs_orders.apply_async(args=[tmp_file_name, response['uuid']])
        response['message'] = gettext('import_starting_msg')

        log(logger, response['uuid'], response)
        return make_response(jsonify(response), response['status_code'], {
            'location': url_for('importer_status', task_id=task.id)})


    def get(self, task_id):
        args = self.reqparse.parse_args()
        response = create_base_response()

        task = importer.import_cvs_orders.AsyncResult(task_id)
        if task.info is not None:
            if task.status == 'SUCCESS':
                os.remove(task.info.get('file_name'))

            result = dict(status=task.state, current=task.info.get('current'),
                          message=task.info.get('msg'))
    
        else:
            result = dict(status='PENDING', current=0,
                          message=gettext('import_starting_msg'))

        response['result'] = result
        log(logger, response['uuid'], response)
        return jsonify(response)



@app.route('/acme_orders')
def init_page():
    return render_template('index.html')
    

@app.errorhandler(404)
def not_found(error):
    """handler for not_found error"""
    
    response = create_base_response()
    response['status_code'] = 404
    response['message'] = gettext('endpoint_not_found_error_msg')
    log(logger, response['uuid'], response, level='error')
    return jsonify(response), response['status_code']
