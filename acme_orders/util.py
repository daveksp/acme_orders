__author__ = 'david'

import functools
import uuid

from flask import request

from acme_orders import app
from acme_orders.logger.log import create_logger, log

logger = create_logger(__name__)


def create_base_response():
    uuid_value = request.args.get('uuid')

    if uuid_value is None:
        uuid_value = uuid.uuid4()
    
    response = dict(result=[], status_code=200, uuid=uuid_value, message='')
    log(logger, response['uuid'], 'starting request', params=request.args)

    return response
    

def is_allowed_file(filename):
    return ('.' in filename 
    	   and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS'])