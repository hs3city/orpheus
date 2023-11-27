FROM python:3.11-slim

COPY pyproject.toml poetry.lock /src/orpheus/

WORKDIR /src/orpheus

RUN apt-get update \
&& apt-get install -y --no-install-recommends build-essential=12.9 \
&& rm -rf /var/lib/apt/lists/* \
&& pip install --no-cache-dir poetry==1.7.1 \
&& poetry install

COPY . /src/orpheus/

CMD ["poetry", "run", "python", "bot.py"]
