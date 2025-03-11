# upload.py
import os
from command import Command, LogUploadErrors, LogCorruptedRecords, LogCorruptedFile, CheckRecordsUploaded, \
    MarkRecordsUploaded, GetSpeechSenseKey
import psycopg2
import time
import traceback
from setup_logger import logger
from datetime import datetime


global cnx

def check_env_variables() -> dict:
    """
    Проверка, что заданы все необходимые переменные среды
    :return: словарь с требуемыми переменными
    """
    OS_VARS = ['PG_CONNECTION_ID', 'PG_USER']
    args = {}

    for k in OS_VARS:
        val = os.getenv(k)
        if val is None or str(val) == "":
            raise Exception(
                f"missing required function environment variable {k}, all variables should be set and non-empty: "
                f"{str(OS_VARS)}")
        else:
            args.update({k: val})

    return args


def connect(database, user, password, host):
    """
    Пробуем соединиться с базой данных 7 раз с задержкой в 5 секунд
    :return: соединение
    """
    sql = """SELECT 1;"""
    connected, num, connection, error_msg = False, 0, None, None
    while num < 7 and not connected:
        try:
            conn = psycopg2.connect(database=database,
                                    user=user,
                                    password=password,
                                    host=host,
                                    port=6432,
                                    sslmode="require")

            with conn.cursor() as cursor:
                logger.info(f"SQL: {sql}")
                cursor.execute(sql)
                result = cursor.fetchall()
                logger.info(f"result: {result}")
                cursor.close()

            connected = True
            connection = conn
        except Exception as e:
            num += 1
            logger.error(f"[{datetime.now().isoformat()}] Sleep for 5s: {e}")
            time.sleep(5.0)
            error_msg = str(e) + traceback.format_exc()
    if connected:
        return connection
    else:
        raise Exception(f"Can't connect to repository in {num} times. Last error: {error_msg}")


# Словарь для хранения соответствия action и классов команд
command_mapping = {
    "log_corrupted_file": LogCorruptedFile,
    "log_corrupted_records": LogCorruptedRecords,
    "log_upload_errors": LogUploadErrors,
    "get_speechsense_key": GetSpeechSenseKey,
    "mark_records_uploaded": MarkRecordsUploaded,
    "check_records_uploaded": CheckRecordsUploaded
}


# Фабрика команд через словарь
def get_command(action, data, request_id) -> Command:
    command_class = command_mapping.get(action)
    if not command_class:
        raise ValueError(f"Unknown action: {action}")
    return command_class(data=data, request_id=request_id)


def handler(event, context):
    """
    Точка входа облачной функции
    :param event:
    :param context:
    :return:
    """

    logger.info(event)

    if 'action' not in event:
        logger.error(f"action not specified or not in list {command_mapping.keys()}")
        raise Exception(f"action not specified or not in list {command_mapping.keys()}")

    if 'data' not in event:
        logger.error("missing required input data")
        raise Exception("missing required input data")

    os_args = check_env_variables()

    pg_connection_id = os_args['PG_CONNECTION_ID']
    pg_user = os_args['PG_USER']

    connection = connect(database=pg_connection_id,
                         user=pg_user,
                         password=context.token["access_token"],
                         host=f"{pg_connection_id}.postgresql-proxy.serverless.yandexcloud.net")

    with connection.cursor() as cursor:
        # Получаем команду в зависимости от action
        command = get_command(action=event['action'], data=event['data'], request_id=context.request_id)
        # Выполняем команду
        result = command.execute(cursor)
        if not result:
            result = {}
        connection.commit()
        cursor.close()

    connection.close()

    return result
