# acme_orders
<a href='https://coveralls.io/github/daveksp/acme_orders?branch=master'><img src='https://coveralls.io/repos/github/daveksp/acme_orders/badge.svg?branch=master' alt='Coverage Status' /></a>
ABOUT THIS PROKECT:

    - This project uses celery and RabbitMQ as Broker. I've setup a rabbitMq docker container in 142.4.215.94, to make easy for you to test the project without further configuration.

    - As a Flask Pattern, the config file was described as different types of Class (Development, Testing and Production). They are placed in config/general_config.py 

RUNNING:

    - requirements.txt is placed in acme_orders/resources/
    
    - to start up the project, execute this command in the root directory: resources/script/wsgi_start.sh 142.4.215.94 Production

NEXT STEPS:

    - Use Babbel as a I18n provider, thus moving all the system's messages to a unique place, making easy to reuse and getting the translations.

    - Apply Rotating Logs with FileHandlers.

    - Use an ELK Suite (Elastic Search, Logstash and Kibana), routing our logs to this suite would bring us the possibility of extracting data from our logs. The api's endpoints are ready to receive an uuid for each request. Through this uuid, it's simple for us to identify in which micro service the request failed and where in this module we should take a look.
    
    - Setup CORS for enabling calls from an especific address. As this is just a test, doesn't make sense to restrict, so our current config is '/*'.

    - The import process is saving the csv file into /tmp and passing it's path to celery task. It's not a good think if we want to scale to more celery nodes in different machines. In this case, it'd be a good idea to upload the file to somewhere as an Amazon S3 bucket.

    - Apply a Basic Auth. This way we encode user and password with base64 and send it in the header, providing a simple protection to our api.  
