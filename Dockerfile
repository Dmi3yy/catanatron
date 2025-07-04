FROM python:3.12

WORKDIR /app

RUN pip install --upgrade pip

COPY . .
RUN pip install -e .[web]

EXPOSE 5001

ENV DATABASE_URL=postgresql://catanatron:victorypoint@db:5432/catanatron_db
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=1
ENV FLASK_APP=catanatron.web/catanatron.web
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001

CMD flask run