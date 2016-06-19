# coding: utf-8
__author__ = 'david'

import json
import os
from StringIO import StringIO
import sys
import time
import unittest

from mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

os.environ['ACME_ENV'] = 'Testing'
os.environ['CELERY_RESULT_BACKEND'] = 'amqp://guest:guest@142.4.215.94:5672//'
os.environ['CELERY_BROKER_URL'] = 'amqp://guest:guest@142.4.215.94:5672//'

from acme_orders import app, celery
from acme_orders.config.general_config import Config         
from acme_orders.models import get_session, init_engine, Order
from acme_orders.service import import_cvs_orders


class manageTestCase(unittest.TestCase):  

    def setUp(self):
        self.app = app.test_client()    
        self.config = Config.factory('Testing') 
        self.init_db()                
        
                
    def tearDown(self):
        self.reset_validators()
        session = get_session()

        for order_id in self.inserted_orders:
            session.query(Order).filter_by(id=order_id).delete()
            session.commit()
    
    # Tests for View
    def test_list_imported_orders(self):
        rv = self.app.get('/acme_orders/api/v1/orders')
        orders = json.loads(rv.data)   
        assert len(orders['result']) == 7 


    def test_limited_list_imported_orders(self):
        rv = self.app.get('/acme_orders/api/v1/orders?limit=1')
        orders = json.loads(rv.data)   
        assert len(orders['result']) == 1


    def test_list_imported_orders_offset(self):
        rv = self.app.get('/acme_orders/api/v1/orders?offset=1')
        orders = json.loads(rv.data)   
        assert len(orders['result']) == 6
        assert orders['result'][0]['id'] == 2 


    def test_list_imported_orders_limit_offset(self):
        rv = self.app.get('/acme_orders/api/v1/orders?offset=2&limit=2')
        orders = json.loads(rv.data)   
        assert len(orders['result']) == 2
        assert orders['result'][0]['id'] == 3


    def test_list_imported_orders_invalid_offset(self):
        rv = self.app.get('/acme_orders/api/v1/orders?offset=ab')
        result = json.loads(rv.data)   
        
        assert result['message'] == 'offset must be a number!'
        assert result['status_code'] == 402

    
    def test_list_imported_orders_invalid_limit(self):
        rv = self.app.get('/acme_orders/api/v1/orders?limit=ab')
        result = json.loads(rv.data)   
        
        assert result['message'] == 'limit must be a number! '
        assert result['status_code'] == 402


    def test_get_order(self):
        rv = self.app.get('/acme_orders/api/v1/orders/1')
        orders = json.loads(rv.data)   
        assert orders['result']['id'] == 1 


    def test_upload_csv(self):
        order_list = [
            ['id|name|email|state|zipcode|birthday'],
            ['2|Sammus Aran|metalgear@yeahoo.com|NY|10033|May 17', '1978'],
            ['8|Toddy Pinheiro|toddynho.pinheiro@gmail.com|NY|10033|Jun 18', '1988'],
        ]

        celery.conf.update(CELERY_ALWAYS_EAGER=True,)
        with patch('acme_orders.service.csv.reader') as reader_mock: 
            reader_mock.return_value = order_list
            rv = self.app.put('/acme_orders/api/v1/orders/import', 
                               data=dict(csv_file=(StringIO('testing'), 
                                  'orders.csv')
            ))

            time.sleep(4)
            result = json.loads(rv.data)
            os.remove('/tmp/{}.csv'.format(result['uuid']))
            assert result['message'] == 'starting importing proccess'

            rv = self.app.get('/acme_orders/api/v1/orders')
            orders = json.loads(rv.data)['result']
            assert len(orders) == 8
            self.inserted_orders.append(8)
            assert orders[7]['name'] == 'Toddy Pinheiro'

    
    def test_get_status_success(self):
        with patch('acme_orders.service.import_cvs_orders.AsyncResult') as result_mock:
            tmp_file = open('/tmp/acme_testing.csv', 'w')
            tmp_file.close()

            info = {
                'current': '0',
                'msg': 'waiting',
                'file_name': '/tmp/acme_testing.csv'
            }

            task = type("Task", (),  {'info': info, 'status': 'SUCCESS', 'state': 'SUCCESS'})
            result_mock.return_value = task

            rv = self.app.get('/acme_orders/api/v1/orders/import/status?task_id=testing')
            task_status_result = json.loads(rv.data)['result']
            assert task_status_result['status'] == 'SUCCESS'


    def test_get_status_progress(self):
        with patch('acme_orders.service.import_cvs_orders.AsyncResult') as result_mock:
            info = {
                'current': '0',
                'msg': 'waiting'
            }

            task = type("Task", (),  {'info': info, 'status': 'PROGRESS', 'state': 'PROGRESS'})
            result_mock.return_value = task

            rv = self.app.get('/acme_orders/api/v1/orders/import/status?task_id=testing')
            task_status_result = json.loads(rv.data)['result']
            assert task_status_result['status'] == 'PROGRESS'


    def test_get_status_pending(self):
        with patch('acme_orders.service.import_cvs_orders.AsyncResult') as result_mock:
            info = {
                'current': '0',
                'msg': 'waiting'
            }

            task = type("Task", (),  {'info': None})
            result_mock.return_value = task

            rv = self.app.get('/acme_orders/api/v1/orders/import/status?task_id=testing')
            task_status_result = json.loads(rv.data)['result']
            assert task_status_result['status'] == 'PENDING'
    

    #  Tests for template
    def test_index(self):
        """@todo use selenium for tests in frontend"""

        rv = self.app.get('/acme_orders')
        assert rv.data.count('<title>Acme Wines</title>') > 0

    
    # Tests for error handler
    def test_not_found_handler(self):
        rv = self.app.get('/acme_orders/api/v2/pipocas')
        tags = json.loads(rv.data)
        assert tags['message'] == 'endpoint not found'
        assert tags['status_code'] == 404

    
    #  Tests for service 
    def test_import_cvs_orders(self):
        celery.conf.update(CELERY_ALWAYS_EAGER=True,)
        
        with app.test_request_context('/test'):
            csv_file_name = 'resources/test_orders.csv'
            task = import_cvs_orders.apply_async(args=[csv_file_name, 'testing'])
            time.sleep(4)
            rv = self.app.get('/acme_orders/api/v1/orders')
            orders = json.loads(rv.data)['result']                
                
            assert len(orders) == 10
            self.inserted_orders.extend([9, 10, 11])


    def test_import_cvs_one_order(self):
        with app.test_request_context('/test'):
            csv_file_name = 'resources/one_record.csv'
            task = import_cvs_orders.apply(args=[csv_file_name, 'testing'], throw=True)
            rv = self.app.get('/acme_orders/api/v1/orders')
            orders = json.loads(rv.data)['result']                
                
            assert len(orders) == 8
            self.inserted_orders.append(12)


    def test_import_cvs_empty_file(self):
        with app.test_request_context('/test'):
            csv_file_name = 'resources/empty_file.csv'
            task = import_cvs_orders.apply(args=[csv_file_name, 'testing'], throw=True)
            rv = self.app.get('/acme_orders/api/v1/orders')
            orders = json.loads(rv.data)['result']                
                
            assert len(orders) == 7
    

    def test_import_cvs_only_header(self):
        with app.test_request_context('/test'):
            csv_file_name = 'resources/only_header.csv'
            task = import_cvs_orders.apply(args=[csv_file_name, 'testing'], throw=True)
            rv = self.app.get('/acme_orders/api/v1/orders')
            orders = json.loads(rv.data)['result']                
                
            assert len(orders) == 7


    # Tests for model validators
    def test_validate_zipcode_sum_success(self):
        self.setup_validators(['zipcode_sum'])
        order = Order(zipcode='11197')
        order.validate()
        
        assert not order.errors


    def test_validate_zipcode_sum_fail(self):
        self.setup_validators(['zipcode_sum'])
        order = Order(zipcode='11199')
        order.validate()
        
        assert order.errors[0]['rule'] == 'zipcode_sum'
        assert order.errors[0]['message'] == 'Your zipcode sum is too large'


    def test_validate_zipcode_length_success(self):
        self.setup_validators(['zipcode_length'])
        order = Order(zipcode='111111111')
        order2 = Order(zipcode='11111*1111')
        order.validate()
        order2.validate()
        
        assert not order.errors
        assert not order2.errors


    def test_validate_zipcode_length_fail(self):
        self.setup_validators(['zipcode_length'])
        order = Order(zipcode='1119945')
        order.validate()
        
        assert order.errors[0]['rule'] == 'zipcode_length'
        assert order.errors[0]['message'] == 'incorrect zipcode length'


    def test_validate_allowed_state_success(self):
        self.setup_validators(['allowed_state'])
        order = Order(state='NY')
        order.validate()
        
        assert not order.errors
        
    
    def test_validate_allowed_state_fail(self):
        self.setup_validators(['allowed_state'])
        order = Order(state='NJ')
        order.validate()
        
        assert order.errors[0]['rule'] == 'allowed_state'
        assert order.errors[0]['message'] == "We don't ship to NJ"


    def test_validate_config_allowed_state(self):
        app.config['INVALID_STATES'] = ['NY', 'PA', 'MS', 'IL', 'ID', 'OR']
        self.setup_validators(['allowed_state'])
        order_ny = Order(state='NY')
        order_nj = Order(state='NJ')
        order_ct = Order(state='CT')
        order_ny.validate()
        order_nj.validate()
        order_ct.validate()

        assert order_ny.errors[0]['rule'] == 'allowed_state'
        assert order_ny.errors[0]['message'] == "We don't ship to NY"

        assert not order_nj.errors
        assert not order_ct.errors
        
        app.config['INVALID_STATES'] = ['NJ', 'CT', 'PA', 'MS', 'IL', 'ID', 'OR']


    def test_validate_email_pattern_success(self):
        self.setup_validators(['email_pattern'])
        order = Order(email='daveksp@gmail.com')
        order.validate()
        
        assert not order.errors


    def test_validate_email_pattern_fail(self):
        self.setup_validators(['email_pattern'])
        order = Order(email='daveksp-gmail.com')
        order2 = Order(email='daveksp;@gmail.com')
        order.validate()
        order2.validate()
        
        assert order.errors[0]['rule'] == 'email_pattern'
        assert order.errors[0]['message'] == "incorrect email pattern"

        assert order2.errors[0]['rule'] == 'email_pattern'
        assert order2.errors[0]['message'] == "incorrect email pattern"


    def test_validate_email_state_success(self):
        self.setup_validators(['email_state'])
        order = Order(email='daveksp@gmail.com', state='NY')
        order.validate()
        
        assert not order.errors


    def test_validate_email_state_fail(self):
        self.setup_validators(['email_state'])
        order = Order(email='daveksp@test.net', state='NY')
        order.validate()
        
        assert order.errors[0]['rule'] == 'email_state'
        assert order.errors[0]['message'] == "users from NY can't have .net email address"


    def test_validate_allowed_age_success(self):
        self.setup_validators(['allowed_age'])
        order = Order(birthday='Nov 9 1985')
        order.validate()
        
        assert not order.errors


    def test_validate_allowed_age_fail(self):
        self.setup_validators(['allowed_age'])
        order = Order(birthday='Jan 9 1996')
        order.validate()
        
        assert order.errors[0]['rule'] == 'allowed_age'
        assert order.errors[0]['message'] == "you must be at least 21 years old for ordering alcohoolic drinks"

    # Tests for config class
    def test_config_wrong_type(self):
        with self.assertRaises(TypeError):
            config = Config.factory('NonExistentType')
            app.config.from_object(config)    


    # Util methods    
    def init_db(self):        
        init_engine(self.config.DB_URI, echo=self.config.SQL_ALCHEMY_ECHO, client_encoding='utf8')
        self.inserted_orders = []

        orders = [
            Order(name='David Pinheiro', email='daveksp@gmail.com', id=1, state='NY', zipcode='10033', birthday='Nov 9 1985'),
            Order(name='Raphael Walker', email='rapha@gmail.com', id=2, state='NY', zipcode='10033', birthday='Apr 12 1955'),
            Order(name='Phill Spancer', email='phill.spancer@gmail.com', id=3, state='PA', zipcode='99999', birthday='Aug 1 1980'),
            Order(name='Peter Quill', email='peter.quill@gog.com', id=4, state='AZ', zipcode='10033', birthday='Dec 3 2003'),
            Order(name='Vito Corleone', email='vito.corleone@godfather.net', id=5, state='NY', zipcode='10033', birthday='Dec 15 1940'),
            Order(name='Carl Fisherman', email='carl.twd;@amc.net', id=6, state='MD', zipcode='10121', birthday='Feb 10 1990'),
            Order(name='Marcela Bouth', email='bouthmarcela@hotmail.com', id=7, state='MD', zipcode='1012184', birthday='Oct 27 1983'),
        ]
        
        session = get_session()
        for order in orders:
            order.validate()
            session.add(order)
            session.commit()
            self.inserted_orders.append(order.id)
        
    def setup_validators(self, validators):
        undesired_validators = [indice for indice, validator in enumerate(app.config['VALIDATORS']) if validator['rule'] not in validators]
        for validator_indice in undesired_validators:
            app.config['VALIDATORS'][validator_indice]['activated'] = False 


    def reset_validators(self):
        app.config['VALIDATORS'] = [
            {'rule': 'allowed_state', 'activated': True},
            {'rule': 'email_pattern', 'activated': True},
            {'rule': 'zipcode_sum', 'activated': True},
            {'rule': 'zipcode_length', 'activated': True},
            {'rule': 'email_state', 'activated': True},
            {'rule': 'allowed_age', 'activated': True}
        ]

if __name__ == '__main__':
	unittest.main()