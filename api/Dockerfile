# Pull base image
FROM python:3.8

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /code

# Install dependencies
RUN pip install Django==3.1.7 \
    && pip install environs==9.3.2 \
    && pip install psycopg2==2.8.6 \
    && pip install djangorestframework==3.12.4 \
    && pip install django-cte==1.1.5 \
    && pip install drf-spectacular==0.14.0 \
    && pip install gunicorn==20.1.0

# Copy project
COPY . /code/