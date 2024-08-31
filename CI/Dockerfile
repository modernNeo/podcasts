FROM python:3.12.5-alpine
RUN apk update && apk add alpine-conf
RUN setup-timezone -z Canada/Pacific

EXPOSE 8000

EXPOSE 5432

RUN apk add postgresql

WORKDIR /src/app
COPY requirements.txt requirements.txt
COPY db-requirements.txt db-requirements.txt
COPY podcasts_site/podcasts podcasts
COPY podcasts_site/podcasts_site podcasts_site
COPY podcasts_site/manage.py manage.py
COPY CI/run_docker.sh run_docker.sh
COPY CI/wait-for-postgres.sh wait-for-postgres.sh

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r db-requirements.txt


CMD ["./wait-for-postgres.sh", "./run_docker.sh"]
#CMD ["sh"]
