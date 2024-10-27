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

rm ffmpeg-N-117481-g02306cbfee-linux64-gpl.tar.xz || true
rm ffmpeg-N-117481-g02306cbfee-linux64-gpl || true
wget https://github.com/yt-dlp/FFmpeg-Builds/releases/download/autobuild-2024-10-12-18-07/ffmpeg-N-117481-g02306cbfee-linux64-gpl.tar.xz
tar -xf ffmpeg-N-117481-g02306cbfee-linux64-gpl.tar.xz

exec $cmd

