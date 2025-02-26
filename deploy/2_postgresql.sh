#!/bin/bash

set -e
set -u

echo "processing managed-postgresql cluster ${PG_NAME}..."
# check cluster exists
res_pg=$(yc managed-postgresql cluster list --format json-rest | jq -r -c ".[] | select( .name == \"${PG_NAME}\") | .id")

if [ -z "${res_pg}" ]; then
  echo "postgresql cluster doesn't exists - creating"
  yc managed-postgresql cluster create \
   --name ${PG_NAME} \
   --environment production \
   --network-name default \
   --resource-preset s2.micro \
   --host zone-id=ru-central1-a,subnet-name=default-ru-central1-a \
   --disk-type network-hdd \
   --disk-size 256 \
   --user name=${PG_USER},password="${PG_PASSWORD}" \
   --database name=${PG_DATABASE},owner=${PG_USER} \
   --websql-access \
   --serverless-access
else
  echo "cluster already exists - proceeding"
fi

# check serverless connection exists
res_cnx=$(yc serverless mdbproxy list --format json-rest | jq -r -c ".[] | select( .name == \"${PG_CONNECTION_NAME}\") | .id")

if [ -z "${res_cnx}" ]; then
  echo "postgresql serverless connection doesn't exists - creating"
  yc serverless mdbproxy create postgresql \
   --name=${PG_CONNECTION_NAME} \
   --cluster-name=${PG_NAME} \
   --database=${PG_DATABASE} \
   --user=${PG_USER} \
   --password="${PG_PASSWORD}"
else
  echo "postgresql serverless connection already exists - proceeding"
fi

# check viewer user exists
res_viewer=$(yc managed-postgresql user list --cluster-name ${PG_NAME} --format json-rest | jq -r -c ".[] | select( .name == \"${PG_VIEWER_USER}\") | .name")
if [ -z "${res_viewer}" ]; then
  echo "postgresql viewer user doesn't exists - creating"
  yc managed-postgresql user create "${PG_VIEWER_USER}" \
   --cluster-name="${PG_NAME}" \
   --grants="${PG_DATABASE}" \
   --permissions=${PG_DATABASE} \
   --password="${PG_PASSWORD}"
else
  echo "postgresql viewer user already exists - proceeding"
fi