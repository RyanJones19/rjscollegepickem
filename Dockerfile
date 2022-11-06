FROM python:3.7

ENV DB_USER='YOUR_USERNAME' \
    DB_PASSWORD='YOUR_PASSWORD' \
    DB_HOST='YOUR_HOST' \
    DB_PORT='YOUR_PORT' \
    DB_NAME='YOUR_DB_NAME' \
    SECRET_KEY='YOUR_DB_SECRET' \
    SPORTS_DATA_API_KEY='YOUR_API_KEY' \
    SPORTS_RADAR_API_KEY='YOUR_API_KEY'

WORKDIR /app

COPY project /app

COPY requirements.docker /app/requirements.docker

RUN pip install -r /app/requirements.docker

ENV FLASK_APP=app

WORKDIR /

CMD ["flask","run","-h","0.0.0.0","-p","443","--cert=YOUR_CERT","--key=YOUR_KEY"]
