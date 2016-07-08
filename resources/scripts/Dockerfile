FROM python:2.7

RUN mkdir -p /opt/app/

WORKDIR /opt/app
COPY acme_orders/ /opt/app/
RUN ls /opt/app
RUN pip install -r resources/requirements.txt

EXPOSE 8089

ENV C_FORCE_ROOT true

CMD ["resources/scripts/wsgi_start.sh", "142.4.215.94", "Production" ]