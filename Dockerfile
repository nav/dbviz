FROM python:3.9-alpine

WORKDIR /srv

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIPENV_VENV_IN_PROJECT 1

COPY Pipfile Pipfile.lock /srv/

RUN set -eux \
  && apk add --no-cache --virtual .build-deps build-base \
    libressl-dev libffi-dev gcc musl-dev python3-dev mariadb-dev \
  && pip install --upgrade pipenv

RUN pipenv install --dev

COPY ./src /srv/dbviz

WORKDIR /srv/dbviz

CMD pipenv run uvicorn main:app --host 0.0.0.0 --port 8000

