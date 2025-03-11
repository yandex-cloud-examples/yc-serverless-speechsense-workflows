#!/bin/bash

set -e
set -u

echo "processing function ${WORKFLOW_CALL_FUNCTION}..."
#obtaining workflow_id
WORKFLOW_ID=$(yc serverless workflow list --format json | jq -r -c ".workflows[] | select( .name == \"${WORKFLOW_NAME}\") | .id")

#check function exists
res=$(yc serverless function list --format json-rest | jq -r -c ".[] | select( .name == \"${WORKFLOW_CALL_FUNCTION}\") | .id")

if [ -z "${res}" ]; then
  echo "function doesn't exists - creating"
  yc serverless function create --name ${WORKFLOW_CALL_FUNCTION}
else
  echo "function already exists - proceeding with creating function version"
fi

#count number of function versions
v_num=$(yc serverless function version list --function-name ${WORKFLOW_CALL_FUNCTION} --format json-rest | jq -r -c '. | length')

if [ $v_num -gt 10 ]; then
  echo "too many function versions - recreating function"
  yc serverless function delete --name ${WORKFLOW_CALL_FUNCTION}
  yc serverless function create --name ${WORKFLOW_CALL_FUNCTION}
fi

#creating function version
yc serverless function version create \
  --function-name=${WORKFLOW_CALL_FUNCTION} \
  --runtime=python312 \
  --entrypoint=main.handler \
  --memory=2048m \
  --execution-timeout=600s \
  --source-path=../4_function-workflow-call \
  --service-account-id=${ACCOUNT_ID} \
  --environment=WORKFLOW_ID=${WORKFLOW_ID} \
  --format json-rest
