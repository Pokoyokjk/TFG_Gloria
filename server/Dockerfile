FROM python:3.10-alpine

COPY requirements.txt requirements.txt
RUN apk add --no-cache gcc musl-dev linux-headers
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

ENV FLASK_APP=/app/app.py
ENV FLASK_RUN_HOST=0.0.0.0
EXPOSE 5000

CMD ["flask", "run", "--debug"]