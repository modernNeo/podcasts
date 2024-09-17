#!/bin/bash

# PURPOSE: used be jenkins to launch Wall_e to the CSSS PROD Discord Guild

set -e -o xtrace
# https://stackoverflow.com/a/5750463/7734535

export COMPOSE_PROJECT_NAME="podcasts_site"

export prod_container_name="${COMPOSE_PROJECT_NAME}_app"
export prod_container_puller_name="${COMPOSE_PROJECT_NAME}_one_off_puller"
export prod_container_db_name="${COMPOSE_PROJECT_NAME}_db"
export docker_compose_file="CI/docker-compose.yml"
export prod_image_name_lower_case=$(echo "$prod_container_name" | awk '{print tolower($0)}')
export prod_puller_image_name_lower_case=$(echo "$prod_container_puller_name" | awk '{print tolower($0)}')

docker rm -f ${prod_container_name} || true
docker rm -f ${prod_container_puller_name} || true
docker image rm -f $(docker images  | grep -i "${prod_image_name_lower_case}" | awk '{print $3}') || true
docker image rm -f $(docker images  | grep -i "${prod_puller_image_name_lower_case}" | awk '{print $3}') || true
docker volume create --name="${COMPOSE_PROJECT_NAME}_logs"
docker compose -f "${docker_compose_file}" up -d

sleep 20

container_failed=$(docker ps -a -f name=${prod_container_name} --format "{{.Status}}" | head -1)
container_db_failed=$(docker ps -a -f name=${prod_container_db_name} --format "{{.Status}}" | head -1)

if [[ "${container_failed}" != *"Up"* ]]; then
    docker logs ${prod_container_name}
    exit 1
fi

if [[ "${container_db_failed}" != *"Up"* ]]; then
    docker logs ${prod_container_db_name}
    exit 1
fi
