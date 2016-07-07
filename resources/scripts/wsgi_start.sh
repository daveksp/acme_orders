#!/bin/sh

ps ax | grep -E "(celery)" | grep -v 'grep' | awk '{print $1}' | xargs kill -9
ps ax | grep -E "(acme_orders)" | grep -v 'grep' | awk '{print $1}' | xargs kill -9
sleep 1


IP=$(ip addr | grep 'state UP' -A2 | tail -n1 | awk '{print $2}' | cut -f1  -d'/')

export CELERY_RESULT_BACKEND="amqp://guest:guest@$1:5672//"
export CELERY_BROKER_URL="amqp://guest:guest@$1:5672//"
export ACME_ENV=$2

celery worker -A acme_orders.celery --loglevel=info &

uwsgi --http $IP:8089 --wsgi-file runserver.py --callable app --processes 4 --threads 2 --master --lazy --lazy-apps 
