#!/bin/bash

set -e
set -u

. ./options.sh


echo "processing function ${VERIFY_FUNCTION_NAME}..."
#check function exists
res=$(yc serverless function list --format json-rest | jq -r -c ".[] | select( .name == \"${VERIFY_FUNCTION_NAME}\") | .id")

if [ -z "${res}" ]; then
  echo "function doesn't exists - creating"
  yc serverless function create --name ${VERIFY_FUNCTION_NAME}
else
  echo "function already exists - proceeding with creating function version"
fi

#count number of function versions
v_num=$(yc serverless function version list --function-name ${VERIFY_FUNCTION_NAME} --format json-rest | jq -r -c '. | length')

if [ $v_num -gt 10 ]; then
  echo "too many function versions - recreating function"
  yc serverless function delete --name ${VERIFY_FUNCTION_NAME}
  yc serverless function create --name ${VERIFY_FUNCTION_NAME}
fi

#creating function version
yc serverless function version create \
  --function-name=${VERIFY_FUNCTION_NAME} \
  --runtime=python312 \
  --entrypoint=main.handler \
  --memory=2048m \
  --execution-timeout=600s \
  --source-path=../3_wf_2_function-verify-file \
  --service-account-id=${ACCOUNT_ID} \
  --format json-rest
