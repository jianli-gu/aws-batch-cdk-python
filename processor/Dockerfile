FROM python:3.8-slim-buster

RUN apt-get update -y
RUN pip install --upgrade pip
RUN pip install boto3 pandas click

WORKDIR /code
COPY process_data.py /code
