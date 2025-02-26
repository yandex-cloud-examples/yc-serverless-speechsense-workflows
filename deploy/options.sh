#!/bin/bash

##################################################################################################################

read -r -p "Enter folder id [b1g5l1pqu2q4uh06lubk]: " FOLDER_ID
FOLDER_ID=${FOLDER_ID:-b1g5l1pqu2q4uh06lubk}
yc config set folder-id "${FOLDER_ID}" #идентификатор каталога в облаке
echo $FOLDER_ID

read -r -p "Enter service account name [ddolbin-sa-admin]: " ACCOUNT_NAME
ACCOUNT_NAME=${ACCOUNT_NAME:-ddolbin-sa-admin}
export ACCOUNT_NAME # имя сервисного аккаунта для запуска функций и потока
echo $ACCOUNT_NAME

export PREFIX=speechsense-upload

# переменные бакета
export BUCKET_NAME='ddolbin-bucket' # ${PREFIX}-bucket # название бакета для хранения файлов и метаданных
export METADATA_PATH='client_metadata' # путь к папке с метаданными в бакете

# переменные кластера метаданных postgresql
export PG_NAME=${PREFIX}-metadata # название кластера
export PG_DATABASE=uploader # название базы данных
export PG_USER=uploader # имя пользователя - владельца базы данных
export PG_VIEWER_USER=viewer # имя пользователя для просмотра метаданных
export PG_PASSWORD=up10@der # пароль пользователя

export PG_CONNECTION_NAME=${PREFIX}-metadata-connection # название прокси-соединения к кластеру

# переменные рабочего процесса
export METADATA_FUNCTION=metadata-processor # имя функции взаимодействия с кластером метаданных
export VERIFY_FUNCTION_NAME=verify-file # имя функции проверки прочитанного с S3 файла
export SPEECHSENSE_FUNCTION=speechsense-upload # имя функции загрузки файла в Speechsense
export WORKFLOW_NAME="wf-${PREFIX}" # имя потока

# имена сервисов
export WORKFLOW_CALL_FUNCTION=workflow-call # имя функции запуска потока
export TRIGGER_NAME=${WORKFLOW_CALL_FUNCTION}-trigger # имя триггера object-storage, вызывающего функцию WORKFLOW_CALL_FUNCTION

########################################## получение идентификатора сервисного аккаунта ##########################

#obtaining account id
ACCOUNT_ID=$(yc iam service-account list --format json | jq -r -c ".[] | select( .name == \"${ACCOUNT_NAME}\") | .id")
export ACCOUNT_ID

########################################## получение ключа доступа к S3 ##########################################
if [ ! -f ./access-key.json ]; then
    echo "creating static access key"
    yc iam access-key create --service-account-name ${ACCOUNT_NAME} --format json > ./access-key.json
fi
AWS_ACCESS_KEY_ID=$(cat access-key.json | jq -r -c ".access_key.key_id")
export AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY=$(cat access-key.json | jq -r -c ".secret")
export AWS_SECRET_ACCESS_KEY
