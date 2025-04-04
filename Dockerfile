FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.6.12 /uv /uvx /bin/

LABEL org.opencontainers.image.source=https://github.com/gsi-upm/amor-segb
LABEL org.opencontainers.image.description="AMOR-SEGB server"
LABEL org.opencontainers.image.authors="Grupo de Sistemas Inteligentes - Universidad Politécnica de Madrid"
LABEL org.opencontainers.image.documentation="https://amor-segb.readthedocs.io/"
LABEL org.opencontainers.image.licenses=MIT

EXPOSE 5000

WORKDIR /app
ADD uv.lock uv.lock
ADD pyproject.toml pyproject.toml

RUN uv sync --frozen

COPY ./server/src /app

CMD ["uv", "run", "fastapi", "run", "main.py", "--port", "5000"]