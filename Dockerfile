FROM python:3.11.2

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update
RUN apt-get -y install binutils libproj-dev

RUN pip install --upgrade pip
RUN pip install --no-cache-dir wheel

RUN mkdir /app
WORKDIR /app
COPY . /app/

RUN pip install --upgrade pip
RUN pip install gunicorn

COPY . /requirements.txt/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]