#!/bin/bash

set -e
set -u

echo "processing trigger ${TRIGGER_NAME}..."
#check trigger exists
res_t=$(yc serverless trigger list --format json-rest | jq -r -c ".[] | select( .name == \"${TRIGGER_NAME}\") | .id")

if [ -n "${res_t}" ]; then
  echo "trigger already exists - recreating"
  yc serverless trigger delete --name ${TRIGGER_NAME}
fi

# creating trigger
yc serverless trigger create object-storage \
  --name="${TRIGGER_NAME}" \
  --bucket-id=${BUCKET_NAME} \
  --prefix="${METADATA_PATH}" \
  --suffix=".json" \
  --events='create-object' \
  --batch-size=100 \
  --batch-cutoff=0s \
  --invoke-function-name=${WORKFLOW_CALL_FUNCTION} \
  --invoke-function-service-account-id=${ACCOUNT_ID}