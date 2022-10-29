FROM python:3.7

WORKDIR /app

COPY project /app

COPY requirements.docker /app/requirements.docker

RUN pip install -r /app/requirements.docker

ENV FLASK_APP=app

WORKDIR /

CMD ["flask","run","-h","0.0.0.0","-p","8000"]
