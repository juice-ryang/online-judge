FROM python:latest
ENV PYTHONUNBUFFERED 1
ADD requirements.txt /
RUN pip install -r requirements.txt
