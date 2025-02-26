#!/bin/bash

set -e
set -u

. ./options.sh

echo "processing workflow ${WORKFLOW_NAME}..."
#check workflow exists
res=$(yc serverless workflow list --format json | jq -r -c ".workflows[]? | select( .name == \"${WORKFLOW_NAME}\") | .id")

if [ -z "${res}" ]; then
  echo "workflow doesn't exists - proceeding"
  export WF_OP="create"
else
  echo "workflow already exists - updating"
  export WF_OP="update"
fi

#obtaining workflow functions ids:
export VERIFY_FUNCTION_ID=$(yc serverless function list --format json-rest | jq -r -c ".[] | select( .name == \"${VERIFY_FUNCTION_NAME}\") | .id")
export METADATA_FUNCTION_ID=$(yc serverless function list --format json-rest | jq -r -c ".[] | select( .name == \"${METADATA_FUNCTION}\") | .id")
export SPEECHSENSE_UPLOAD_FUNCTION_ID=$(yc serverless function list --format json-rest | jq -r -c ".[] | select( .name == \"${SPEECHSENSE_FUNCTION}\") | .id")

envsubst '${VERIFY_FUNCTION_ID}, ${METADATA_FUNCTION_ID}, ${SPEECHSENSE_UPLOAD_FUNCTION_ID} ${BUCKET_NAME}' <../wf.template.yawl >wf.yawl

#creating function version
yc serverless workflow ${WF_OP} \
  --name=${WORKFLOW_NAME} \
  --yaml-spec=./wf.yawl \
  --service-account-id=${ACCOUNT_ID} \
  --format json-rest
