__author__ = 'david'

"""
Created on 06/17/2016

@author David Pinheiro

Module responsible for provinding access to methods that will be
executed as celery tasks. Flask doesn't support parallel process
so celery is the responsible for handling these requests in a
non-blocking way.
"""

import csv
from itertools import izip
import sys

import celery
from celery.contrib import rdb
from flask.ext.babel import gettext
from sqlalchemy.exc import IntegrityError

from acme_orders.logger.log import create_logger, log
from acme_orders.models import get_session, Order

logger = create_logger(__name__)


def read_orders(tmp_file_name):
    with open(tmp_file_name, 'rb') as csv_file:
        reader = csv.reader(csv_file)
        current_order = None
        order = None
        for indice, row in enumerate(reader):
            if indice == 0:
                header = row[0].split('|')
                continue
            
            if indice == 2:
                current_order = order

            row_values = ' '.join(row).split('|')
            order_map = {label:value for label, value in izip(header, row_values)} 
            order = Order(**order_map)

            if indice > 1 and current_order is not None:
                current_order.next = order
                yield current_order            
                current_order = order

        if current_order is None and order is not None:
            current_order = order
        
        if current_order is not None:
            yield current_order 
            


@celery.task(bind=True)
def import_cvs_orders(self, tmp_file_name, uuid):
    session = get_session()
    orders = read_orders(tmp_file_name)
    previous = None
    count = 0
     
    for order in orders:
        if not order.valid:
            order.validate()
    
        try:
            session.add(order)
            session.commit()
            count += 1
        except IntegrityError as e:
            session.rollback()
            log(logger, uuid, gettext('existent_id_error_msg'), params=str(order.id))
        
        self.update_state(
            state='PROGRESS', 
            meta={
                'current': count,
                'msg': gettext('import_progress_msg', count=count)
        })
    
    message = gettext('import_success_msg')
    return {'current': count, 'msg': message, 'file_name': tmp_file_name}
