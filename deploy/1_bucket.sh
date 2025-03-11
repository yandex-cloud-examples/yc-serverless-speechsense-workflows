#!/bin/bash

set -e
set -u

echo "processing bucket ${BUCKET_NAME}..."
# check bucket exists
res_b=$(yc storage bucket list --format json-rest | jq -r -c ".[] | select( .name == \"${BUCKET_NAME}\") | .id")

if [ -z "${res_b}" ]; then
  echo "bucket ${BUCKET_NAME} doesn't exists - creating"
  yc storage bucket create --name ${BUCKET_NAME}
else
  echo "bucket already exists - proceeding"
fi