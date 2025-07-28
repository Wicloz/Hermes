FROM python:alpine

RUN apk add --no-cache firefox geckodriver
RUN apk add --no-cache py3-psycopg2 py3-mysqlclient

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -Ur /app/requirements.txt

COPY ./ /app/

WORKDIR /app/
ENTRYPOINT [ "python3", "-u", "/app/hermes.py" ]
