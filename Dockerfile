ARG PYTHON_VERSION=3.11.1-alpine3.16
FROM python:$PYTHON_VERSION AS builder
WORKDIR /

RUN apk add --no-cache g++ curl
RUN mkdir -p /root/.ssh
RUN python -m venv .venv \
	&& .venv/bin/pip install --no-cache-dir -U pip==22.3.1

COPY requirements.txt .
RUN .venv/bin/pip install --no-cache-dir -r ./requirements.txt
COPY . /bidding

FROM python:$PYTHON_VERSION
WORKDIR /bidding

RUN apk --no-cache add  curl
COPY --from=builder /bidding /bidding
COPY --from=builder /.venv /.venv
EXPOSE 8000


ENV PATH="/.venv/bin:$PATH"
ENV PYTHONPATH /srv/avis/

ENTRYPOINT ["python3", "entrypoint.py"]