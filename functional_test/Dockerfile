FROM python:3.9-alpine

RUN apk upgrade
RUN apk add --no-cache git gcc python3-dev musl-dev

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

RUN apk del git gcc python3-dev musl-dev
