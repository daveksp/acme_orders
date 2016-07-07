# coding: utf-8
__author__ = 'david'

from datetime import datetime, date
import json
import re

from celery.signals import task_prerun
from flask.ext.babel import gettext
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from acme_orders import app

Base = declarative_base()


# UTIL DB METHODS
def init_engine(uri, **kwargs):
    global engine
    global db_session

    engine = create_engine(uri, pool_size=5, convert_unicode=True, **kwargs)

    if app.config['DB_MIGRATE']:
        Base.metadata.create_all(engine)

    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    return engine


def get_session():
    return db_session


@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection when at request's end"""

    get_session().remove()


@task_prerun.connect
def on_task_init(*args, **kwargs):
    """process signal for handling database problems whithin celery tasks"""

    engine.dispose()


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    state = Column(String(2))
    zipcode = Column(String(12))
    _birthday = Column(Date)
    valid = Column(Boolean)
    _errors = Column(String)

    errors = []
    next = None

    @property
    def birthday(self):
        return self._birthday

    @birthday.setter
    def birthday(self, value):
        self._birthday = datetime.strptime(value, '%b %d %Y')

    @property
    def errors(self):
        return json.loads(self._errors)

    @errors.setter
    def errors(self, value):
        self._errors = json.dumps(value)

    def validate_zipcode_sum(self):
        handled_zipcode = re.sub(r'[^0-9 \n\.]', '', self.zipcode)
        zipcode_sum = sum(int(number) for number in handled_zipcode)
        if zipcode_sum > 20:
            return {
                'rule': 'zipcode_sum',
                'message': gettext('zipcode_sum_error_msg')
            }

        self.zipcode = handled_zipcode


    def validate_zipcode_length(self):
        handled_zipcode = re.sub(r'[^0-9 \n\.]', '', self.zipcode)
        length = len(handled_zipcode)
        if length != 5 and length != 9:
            return {
                'rule': 'zipcode_length',
                'message': gettext('zipcode_length_error_msg')
            }

        self.zipcode = handled_zipcode


    def validate_allowed_state(self):
        if self.state.upper() in app.config['INVALID_STATES']:
            return {
                'rule': 'allowed_state',
                'message': gettext('allowed_state_error_msg', state=self.state)
            }


    def validate_email_pattern(self):
        str_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+(\.[A-Za-z]{2,}){1,2}$'
        pattern = re.compile(str_pattern)
        if not pattern.match(self.email):
            return {
                'rule': 'email_pattern',
                'message': gettext('email_pattern_error_msg')
            }


    def validate_email_state(self):
        if self.state.upper() == 'NY' and self.email[-4:].lower() == '.net':
            return {
                'rule': 'email_state',
                'message': gettext('email_state_error_msg')
            }


    def validate_allowed_age(self):
        today = date.today()
        month_day_calculation = ((today.month, today.day) <
                                 (self.birthday.month, self.birthday.day))

        age = today.year - self.birthday.year - month_day_calculation
        if age < app.config['ALLOWED_AGE']:
            return {
                'rule': 'allowed_age',
                'message': gettext('allowed_age_error_msg')
            }


    def validate(self):
        errors = []
        self.valid = False
        if (self.next is not None
                and self.next.state == self.state
                and self.next.zipcode == self.zipcode):

            self.next.errors = errors
            self.next.valid = True

        activated_validators = ([validator['rule']
                                for validator in app.config['VALIDATORS']
                                if validator['activated']])

        for validator in activated_validators:
            response = getattr(self, 'validate_{}'.format(validator))()
            if response:
                errors.append(response)

        if not errors:
            self.valid = True
        self.errors = errors


    def __repr__(self):
        return ('''<Order(id:{}, name:{}, email:{}, state:{}, zipcode:{},
                   birthday:{}, valid:{}, errors:{})>'''
                .format(
                        self.id, self.name, self.email, self.state,
                        self.zipcode, self.birthday, self.valid, self.errors))
