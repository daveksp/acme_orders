__author__ = 'david'
"""
Created on 06/17/2016

@author David Pinheiro

@summary:
    - Config
        - ProductionConfig
        - DevelopmentConfig
        - TestingConfig

Module responsible for provinding configuration details according to
especific Enviroment Types such as Production, Testing and Development.
"""


class Config(object):
    DB_MIGRATE = True
    DB_URI = ''
    SQL_ALCHEMY_ECHO = False
    ALLOWED_EXTENSIONS = set(['csv'])

    SECRET_KEY = '\xae\xdc\xa0\xb6\xbf\x843\xe5EELd\x99\x07Tt\x92\x16\xa5\xddj\xf0@\xe8'
    USERNAME = 'admin'
    PASSWORD = 'admin'
    NEW_RELIC_INI_PATH = 'resources/newrelic.ini'

    DEBUG = True
    TESTING = True

    LOG_NAME = 'acme_orders.log'
    LOG_LOCATION = '/var/log/acme/'

    LANGUAGES = {
        'en': 'English',
        'pt': 'Portuguese'
    }

    ALLOWED_AGE = 21
    INVALID_STATES = ['NJ', 'CT', 'PA', 'MS', 'IL', 'ID', 'OR']
    VALIDATORS = [
        {'rule': 'allowed_state', 'activated': True},
        {'rule': 'email_pattern', 'activated': True},
        {'rule': 'zipcode_sum', 'activated': True},
        {'rule': 'zipcode_length', 'activated': True},
        {'rule': 'email_state', 'activated': True},
        {'rule': 'allowed_age', 'activated': True}
    ]

    @staticmethod
    def factory(type):
        """Factory method for handling Config's subclasses creation

        Classes are wrapped inside method for preventing them to be
        directly instanciated. Re-assign desired variables that
        should assume different values inside each subclass.

        @param type: subclass name

        @raise TypeError: When provinding a non existent subclass name
        """

        type = type + 'Config'

        class ProductionConfig(Config):
            DB_URI = 'postgres://acme_wine:acme_wine@142.4.215.94:5432/acme_orders'
            DEBUG = False
            SQL_ALCHEMY_ECHO = False 


        class DevelopmentConfig(Config):
            DB_URI = 'postgres://acme_wine:acme_wine@142.4.215.94:5432/acme_orders'

        class TestingConfig(Config):
            DB_URI = 'postgres://acme_wine:acme_wine@142.4.215.94:5432/acme_orders_test'
            SQL_ALCHEMY_ECHO = False
            LOG_LOCATION = 'log/'

        subclasses = Config.__subclasses__()
        types = [subclass.__name__ for subclass in subclasses]

        if type not in types:
            raise TypeError('Invalid Enviroment Type. Possible values : ProductionConfig, DevelopmentConfig, TestingConfig')
        else:
            return eval(type + '()')
