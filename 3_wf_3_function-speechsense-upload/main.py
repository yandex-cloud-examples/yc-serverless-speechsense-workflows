import os

from model.entry import Entry
from processors.speechsense_processor import SpeechSenseUploader
from processors.src_processor import SrcProcessor
from setup_logger import logger
import traceback
from jsonschema import validate
import requests
import time
import json


def check_env_variables() -> dict:
    """
    Проверка, что заданы все необходимые переменные среды
    :return: словарь с требуемыми переменными
    """
    OS_VARS = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
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


LOCKBOX_API = "https://payload.lockbox.api.cloud.yandex.net/lockbox/v1/secrets/"

LOCKBOX_SECRET_SCHEMA = {
    "type": "object",
    "properties": {
        "speechsense_connection_id": {"type": "string"},
        "speechsense_api_key": {"type": "string"},
        "speechsense_file_format": {"type": "string"}
    },
    "required": ["speechsense_connection_id", "speechsense_api_key", "speechsense_file_format"]
}


def get_secret(token: str, secret_id: str) -> dict:
    url = f"{LOCKBOX_API}{secret_id}/payload"
    headers = {"Authorization": f"Bearer {token}"}

    connected, num, r = False, 5, None
    for i in range(num):
        try:
            r = requests.get(url=url, headers=headers)
            if r.status_code not in [200, 404]:
                time.sleep(5)
            else:
                connected = True
                break
        except requests.exceptions.ConnectionError as e:
            logger.error(str(e) + traceback.format_exc())
            pass
    if connected:
        payload = r.json()
        if 'entries' not in payload:
            raise Exception(
                f'secret {secret_id} not found! Please, check metadata in LockBox and public.source_system table')
        dct = {x['key']: x['textValue'] for x in payload['entries']}
        validate(dct, LOCKBOX_SECRET_SCHEMA)
        return dct
    else:
        raise Exception(f"Can't get lockbox secret in {num} times.")


def handler(event, context):
    """
    Точка входа облачной функции
    :param event:
    :param context:
    :return:
    """

    results = {"talk_id": None, "additional_metadata": None, "upload_error": None}

    os_args = check_env_variables()

    bucket_key = {'key': os_args['AWS_ACCESS_KEY_ID'], 'textValue': os_args['AWS_SECRET_ACCESS_KEY']}

    src_processor = SrcProcessor(bucket_name=os_args['BUCKET_NAME'],
                                 bucket_key=bucket_key)
    sp_loader = SpeechSenseUploader(src_processor=src_processor)

    try:

        e = Entry(event)
        logger.debug(f"uploading {e}")
        results.update(e.to_dict())
        speechsense_settings = get_secret(token=context.token['access_token'], secret_id=e.lockbox_secret_id)
        result = sp_loader.upload(e.to_dict(), e.file_url, speechsense_settings)
        results.update({'talk_id': result.talk_id})

    except Exception as e:
        logger.error(f"error occurred while uploading entry {event}")
        logger.error(f"traceback: {traceback.format_exc()}")
        results.update({'upload_error': f'{str(e)}, Traceback: {traceback.format_exc()}'})

    return results
