#!/bin/bash

cd /opt/app/acme_orders

OLD_TAG=$(docker images | grep acme_orders | awk '{print $2}')
TAG=`echo 1 + $OLD_TAG | bc`
echo "$TAG"

docker build -t acme_orders:$TAG -f acme_orders/resources/scripts/Dockerfile .
docker run -d -p 8089:8089 acme_orders:$TAG