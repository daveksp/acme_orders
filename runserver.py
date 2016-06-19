import sys

from acme_orders import app

# EXECUTING THROUGH python call
# export ACME_ENV=Development
# celery worker -A tagger.celery --loglevel=debug &  --> start celery
# export CELERY_RESULT_BACKEND and  CELERY_BROKER_URL
# python runserver.py DevelopmentConfig

# it's faster for you just run resources/scripts/wsgi_start.sh ip_for_celery_broker enviroment[Testing, Development, Production]


if __name__ == '__main__':    
    app.run('0.0.0.0')
