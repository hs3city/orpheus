FROM python:3.12-slim

COPY pyproject.toml poetry.lock /src/orpheus/

WORKDIR /src/orpheus

RUN apt-get update \
&& apt-get install -y --no-install-recommends build-essential \
&& rm -rf /var/lib/apt/lists/* \
&& pip install --no-cache-dir poetry==1.7.1 \
&& poetry install

COPY . /src/orpheus/

CMD ["poetry", "run", "python", "bot.py"]
