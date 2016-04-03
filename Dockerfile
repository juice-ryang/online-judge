FROM python:latest
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD requirements.txt /code/
WORKDIR /code
RUN pip install -r requirements.txt
ADD . /code/
