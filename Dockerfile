FROM python:alpine

RUN apk add --no-cache firefox geckodriver

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -Ur /app/requirements.txt

COPY ./ /app/

WORKDIR /app/
ENTRYPOINT [ "python3", "-u", "/app/hermes.py" ]
