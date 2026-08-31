#!/bin/bash

# PURPOSE: used be jenkins to launch the podcast app

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

container_db_failed=$(docker ps -a -f name=${prod_container_db_name} --format "{{.Status}}" | head -1)

if [[ "${container_db_failed}" != *"Up"* ]]; then
    docker logs  --tail 50 ${prod_container_db_name}
    exit 1
fi


# 1. Loop until the container is no longer running
while [ "$(docker inspect -f '{{.State.Running}}' "$prod_container_name" 2>/dev/null)" = "true" ]; do
    docker logs  --tail 50 $prod_container_name
    sleep 2
done


# 2. Fetch the container's final exit code
EXIT_CODE=$(docker inspect -f '{{.State.ExitCode}}' "$prod_container_name" 2>/dev/null)

# 3. Check if the container exists and if it exited successfully
if [ -z "$EXIT_CODE" ]; then
    echo "Error: Container '$prod_container_name' does not exist."
    exit 1
elif [ "$EXIT_CODE" -eq 0 ]; then
    echo "Container finished successfully."
    exit 0
else
    echo "Container failed with exit code: $EXIT_CODE"
    docker logs  --tail 50 $prod_container_name
    exit "$EXIT_CODE"
fi