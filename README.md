# acme_orders
<a href='https://coveralls.io/github/daveksp/acme_orders?branch=master'><img src='https://coveralls.io/repos/github/daveksp/acme_orders/badge.svg?branch=master' alt='Coverage Status' /></a>
<img src='https://travis-ci.org/daveksp/acme_orders.svg?branch=master' alt='Building Status' />

ABOUT THIS PROKECT:

    - This project uses celery and RabbitMQ as Broker. I've setup a rabbitMq docker container in 142.4.215.94, to make easy for you to test the project without further configuration.

    - As a Flask Pattern, the config file was described as different types of Class (Development, Testing and Production). They are placed in config/general_config.py 
    
    - I made small changes in the endpoints for providing additional information about the versions and for the case we want to run more than one instance with different versions, so now we have:
    
    - /acme_orders/api/v1/orders
    - /acme_orders/api/v1/orders/<order_id>
    - /acme_orders/api/v1/orders/import
    
    - I have also add other helpful endpoints, such as:
        - /acme_orders
            - gives you a html page with the upload form.
        
        - /acme_orders/api/v1/orders/import/status
            - gives you the upload status.
    
    - Case we have two records with same order_id, only the first one is going to be persisted to the database. As a possible solution, we could remove the order_id and let SQLAlchemy generate a new order_id value for this record.
    
RUNNING:

    - requirements.txt is placed in acme_orders/resources/
    
    - to start up the project, execute this command in the root directory: resources/script/wsgi_start.sh 142.4.215.94 Production
    
    - The project uses the port 8089

NEXT STEPS:

    - Use Babbel as a I18n provider, thus moving all the system's messages to a unique place, making easy to reuse and getting the translations.

    - Apply Rotating Logs with FileHandlers.

    - Use an ELK Suite (Elastic Search, Logstash and Kibana), routing our logs to this suite would bring us the possibility of extracting data from our logs. The api's endpoints are ready to receive an uuid for each request. Through this uuid, it's simple for us to identify in which micro service the request failed and where in this module we should take a look.
    
    - Setup CORS for enabling calls from an especific address. As this is just a test, doesn't make sense to restrict, so our current config is '/*'.

    - The import process is saving the csv file into /tmp and passing it's path to celery task. It's not a good think if we want to scale to more celery nodes in different machines. In this case, it'd be a good idea to upload the file to somewhere as an Amazon S3 bucket.

    - Apply a Basic Auth. This way we encode user and password with base64 and send it in the header, providing a simple protection to our api.  
    
    - Create a Continuous Integration Job for this project and automate the deploy process through tools such as Docker, ansible and/or puppet.
