FROM --platform=linux/amd64 python:3.7

ENV DB_USER='YOUR_DB_USER' \
    DB_PASSWORD='YOUR_DB_PASSWORD' \
    DB_HOST='YOUR_DB_HOST' \
    DB_PORT='YOUR_DB_PORT' \
    DB_NAME='YOUR_DB_NAME' \
    SECRET_KEY='YOUR_DB_SECRET' \
    SPORTS_DATA_API_KEY='YOUR_SPORTS_DATA_API_KEY' \
    SPORTS_RADAR_API_KEY='YOUR_SPORTS_RADAR_API_KEY'

WORKDIR /app

COPY project /app

COPY requirements.docker /app/requirements.docker

RUN pip install -r /app/requirements.docker

ENV FLASK_APP=app

WORKDIR /

CMD ["flask","run","-h","0.0.0.0","-p","443","--cert=./app/certs/pickem.crt","--key=./app/certs/pickem.key"]
