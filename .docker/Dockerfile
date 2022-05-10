FROM python:3.9-alpine

RUN apk add --no-cache --virtual .build-deps gcc musl-dev build-base tzdata
COPY ./app/requirements.txt /tmp
RUN pip3 install --upgrade pip
RUN pip3 install -r /tmp/requirements.txt
COPY ./app/ /app/
WORKDIR /app

EXPOSE 5000

CMD ["python3", "/app/app.py"]
