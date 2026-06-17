#!/bin/sh
# wait-for-postgres.sh

# aquired from https://docs.docker.com/compose/startup-order/
set -e -o xtrace

cmd="$@"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

rm ffmpeg.tar.xz || true
rm ffmpeg || true

apt-get install -y curl

# 1. Fetch the exact filename/tag from the GitHub API, then download it
URL=$(curl -s https://api.github.com/repos/BtbN/FFmpeg-Builds/releases | grep -oE "https://github.com/BtbN/FFmpeg-Builds/releases/download/[^\"]+linux64-gpl.tar.xz" | head -n 1)
# 2. Download the file
wget "$URL" -O ffmpeg.tar.xz
tar -xf ffmpeg.tar.xz

rm deno.zip || true
rm deno || true
wget https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip -O deno.zip
unzip deno.zip

export FFMPEG_LOCATION_PATH="ffmpeg-master-latest-linux64-gpl/bin/ffmpeg"
export DENO_PATH='/src/app/deno'

exec $cmd

