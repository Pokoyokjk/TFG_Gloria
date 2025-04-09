FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.6.12 /uv /uvx /bin/

LABEL org.opencontainers.image.source=https://github.com/gsi-upm/segb
LABEL org.opencontainers.image.description="Semantic Ethical Glass Box (SEGB) Server"
LABEL org.opencontainers.image.authors="Grupo de Sistemas Inteligentes - Universidad Politécnica de Madrid"
LABEL org.opencontainers.image.documentation="https://segb.readthedocs.io/"
LABEL org.opencontainers.image.licenses=MIT

EXPOSE 5000

WORKDIR /app
ADD uv.lock uv.lock
ADD pyproject.toml pyproject.toml

RUN uv sync --frozen

ADD log_conf.yaml log_conf.yaml

RUN mkdir /logs

COPY ./server /app

CMD [ "uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers", "--log-config", "log_conf.yaml" ]