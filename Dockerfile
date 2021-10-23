FROM python:3.8-slim

ADD pyproject.toml poetry.lock /src/orpheus/

WORKDIR /src/orpheus

RUN pip install poetry && poetry install

ADD . /src/orpheus/

CMD poetry run python bot.py