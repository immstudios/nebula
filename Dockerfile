FROM python:3.10-bullseye

RUN apt-get update
RUN apt-get -y install \
    libmemcached-dev \
    cifs-utils \
    zlib1g-dev \
    build-essential \
    mediainfo \
    curl

# Build deps (ffmpeg)

RUN curl https://raw.githubusercontent.com/immstudios/installers/master/install.ffmpeg.sh | bash \
  && rm -rf /tmp/install.ffmpeg.sh

# Nebula codebase

RUN mkdir -p /opt/nebula
COPY . /opt/nebula
WORKDIR /opt/nebula

# Python deps

RUN pip install -U pip && pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

CMD ["./nebula.py"]
