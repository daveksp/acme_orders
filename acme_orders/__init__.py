import os
import uuid

from celery import Celery
from flask import Flask, request
from flask.ext.babel import Babel
from flask.ext.restful import Api
from flask_cors import CORS

from config.general_config import Config

app = Flask(__name__, static_url_path='/templates/static/')
babel = Babel(app)
api = Api(app)

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
from acme_orders.views import ImporterAPI, OrderAPI


api.add_resource(OrderAPI, '/acme_orders/api/v1/orders', endpoint='orders')
api.add_resource(OrderAPI, '/acme_orders/api/v1/orders/<int:order_id>', endpoint='order')

api.add_resource(ImporterAPI, '/acme_orders/api/v1/orders/import', endpoint='importer')
api.add_resource(ImporterAPI, '/acme_orders/api/v1/orders/import/status/<task_id>', endpoint='importer_status')


# CONFIG CROSS ORIGIN REQUEST SHARING 
CORS(app, resources=r'/*', allow_headers='Content-Type', supports_credentials=True)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())
