#!/bin/bash

cd /opt/app/

OLD_TAG=$(docker images | grep acme_orders | awk '{print $2}')
if [ ! -z "$OLD_TAG"]; then
    TAG=`echo 1 + $OLD_TAG | bc`
else
    TAG=1.0
fi
echo "$TAG"

docker build -t acme_orders:$TAG -f acme_orders/resources/scripts/Dockerfile .
docker run -d --name acme_orders_$TAG -p 8089:8089 acme_orders:$TAG