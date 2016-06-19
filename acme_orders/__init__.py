import os

from celery import Celery
from flask import Flask, request
from flask_cors import CORS

from config.general_config import Config

app = Flask(__name__, static_url_path='/templates/static/')

celery = Celery(
    app.name,
    backend=os.environ['CELERY_RESULT_BACKEND'],
    broker=os.environ['CELERY_BROKER_URL']
)


try:
    enviroment = os.environ['ACME_ENV']
except KeyError as ex:
    enviroment = 'Testing'

config = Config.factory(enviroment)
app.config.from_object(config)

from acme_orders.models import init_engine
init_engine(app.config['DB_URI'], echo=app.config['SQL_ALCHEMY_ECHO'])

import acme_orders.views


# CONFIG CROSS ORIGIN REQUEST SHARING 
CORS(app, resources=r'/*', allow_headers='Content-Type', supports_credentials=True)