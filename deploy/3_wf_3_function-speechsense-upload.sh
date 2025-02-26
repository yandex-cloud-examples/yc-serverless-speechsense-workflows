#!/bin/bash

set -e
set -u

. ./options.sh

echo "processing function ${SPEECHSENSE_FUNCTION}..."
export PG_HOST=$(yc managed-postgresql host list --cluster-name ${PG_NAME} --format json-rest | jq -r -c '.[] | select( .role == "MASTER") | .name')
export PG_CONNECTION_ID=$(yc serverless mdbproxy list --format json-rest | jq -r -c ".[] | select( .name == \"${PG_CONNECTION_NAME}\") | .id")

#check function exists
res=$(yc serverless function list --format json-rest | jq -r -c ".[] | select( .name == \"${SPEECHSENSE_FUNCTION}\") | .id")

if [ -z "${res}" ]; then
  echo "function doesn't exists - creating"
  yc serverless function create --name ${SPEECHSENSE_FUNCTION}
else
  echo "function already exists - proceeding with creating function version"
fi

#count number of function versions
v_num=$(yc serverless function version list --function-name ${SPEECHSENSE_FUNCTION} --format json-rest | jq -r -c '. | length')

if [ $v_num -gt 10 ]; then
  echo "too many function versions - recreating function"
  yc serverless function delete --name ${SPEECHSENSE_FUNCTION}
  yc serverless function create --name ${SPEECHSENSE_FUNCTION}
fi

#creating function version
yc serverless function version create \
  --function-name=${SPEECHSENSE_FUNCTION} \
  --runtime=python312 \
  --entrypoint=main.handler \
  --memory=2048m \
  --execution-timeout=600s \
  --source-path=../3_wf_3_function-speechsense-upload \
  --service-account-id=${ACCOUNT_ID} \
  --environment=PG_CONNECTION_ID=${PG_CONNECTION_ID} \
  --environment=PG_USER=${PG_USER} \
  --environment=AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
  --environment=AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
  --environment=BUCKET_NAME=${BUCKET_NAME} \
  --format json-rest
