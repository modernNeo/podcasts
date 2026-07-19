FROM python:3.14.6-alpine
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

# Your environment is attempting to compile Pillow (the Python imaging library) from source,
# but your underlying system is missing the development files for zlib (and likely libjpeg).
RUN apk add gcc musl-dev zlib-dev jpeg-dev

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r db-requirements.txt

RUN apk add curl

CMD ["./wait-for-postgres.sh", "./run_docker.sh"]
#CMD ["sh"]
