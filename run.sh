#!/usr/bin/env bash

set -Eeuo pipefail
trap cleanup SIGINT SIGTERM ERR EXIT

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)

usage() {
  cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") [-h] --param1 value1 --param2 value2 ...

Script for preprocessing the data to upload it to DB.

Available options:

-h, --help             Print this help and exit
--host                 PostgreSQL host for upload data (default: rc1a-hlu228zf6yj3p5ao.mdb.yandexcloud.net)
--port                 PostgreSQL port for upload data (default: 6432)
--dbname               PostgreSQL dbname for upload data (default: TestDB)
--user                 PostgreSQL user for upload data (default: Anastasia)
--password             PostgreSQL password for upload data (default: )
--target_session_attrs PostgreSQL target_session_attrs for upload data (default: read-write)
--sslmode              PostgreSQL sslmode for upload data (set disable for local connection, default: verify-full)
--table_name           PostgreSQL table_name (default: final)
--path_to_data         PostgreSQL path_to_data (default: final.csv)
--numeric_categories   PostgreSQL numerate categories (default: 0)
EOF
  exit
}
cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
  # script cleanup here
}

msg() {
  echo >&2 -e "${1-}"
}

die() {
  local msg=$1
  local code=${2-1} # default exit status 1
  msg "$msg"
  exit "$code"
}
parse_params() {
  # default values of variables set from params
  host='rc1a-hlu228zf6yj3p5ao.mdb.yandexcloud.net'
  dbname='TestDB'
  port='6432'
  password=''
  target_session_attrs='read-write'
  sslmode='verify-full'
  path_to_data='final.csv'
  user='Anastasia'
  table_name='final'
  numeric_categories=0

  while :; do
    case "${1-}" in
    -h | --help) usage ;;

    --host)
      host="${2-}"
      shift
      ;;

    --dbname)
      dbname="${2-}"
      shift
      ;;

    --port)
      port="${2-}"
      shift
      ;;

    --user)
      user="${2-}"
      shift
      ;;

    --password)
      password="${2-}"
      shift
      ;;

    --target_session_attrs)
      target_session_attrs="${2-}"
      shift
      ;;
    --sslmode)
      sslmode="${2-}"
      shift
      ;;

    --table_name)
      table_name="${2-}"
      shift
      ;;

    --path_to_data)
      path_to_data="${2-}"
      shift
      ;;
    --numeric_categories)
      numeric_categories="${2-}"
      shift
      ;;

    -?*) die "Unknown option: $1" ;;
    *) break ;;
    esac
    shift
  done

  args=("$@")

  return 0
}

parse_params "$@"

pip3 install -r requirements.txt

mkdir -p ~/.postgresql
wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" -O ~/.postgresql/root.crt
chmod 0600 ~/.postgresql/root.crt

python3 main.py --host=${host} --port=${port} --dbname=${dbname} --user=${user} --password=${password} --sslmode=${sslmode} --target_session_attrs=${target_session_attrs} --path_to_data=${path_to_data} --table_name=${table_name}
