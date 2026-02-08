# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get -y update && apt-get -y upgrade

RUN apt-get -y install git gcc python3-dev zip

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "tg_bot"]
