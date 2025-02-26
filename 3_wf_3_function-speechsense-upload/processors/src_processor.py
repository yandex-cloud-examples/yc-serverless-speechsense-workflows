# source_processor.py
from urllib.parse import urlparse

import boto3
import requests

from setup_logger import logger

boto_session = None


class GetFileException(Exception):
    pass


def get_file_url(file_url: str) -> bytes:
    """
    Получение содержимого файла
    :param file_url: ссылка на файл
    :return: бинарное содержимое файла
    """
    tries = 0
    while tries < 3:
        try:
            resp = requests.get(file_url)
            if 200 <= resp.status_code < 300:
                if len(resp.content) == 0:
                    logger.error(f'Content by url {file_url} is empty!')
                    raise Exception(f'Content by url {file_url} is empty!')

                return resp.content
            else:
                logger.error(f'Error during fetch audio, got code {resp.status_code}')
                tries += 1
        except Exception as e:
            logger.error(f'Error during fetch file: {e}')
            tries += 1
            continue

    raise Exception(f"Failed to fetch file bytes in {tries} tries!")


class SrcProcessor:
    REGION_NAME = "ru-central1"
    S3_ENDPOINT = "https://storage.yandexcloud.net"

    def __init__(
            self,
            bucket_name: str = None,
            bucket_key: dict = None
    ):

        if bucket_name is not None:
            self.bucket_name = bucket_name

        if bucket_key is None:
            self.bucket_key = {}
        else:
            self.bucket_key = bucket_key

    def get_file(self, file_url: str) -> bytes:
        audio_func = {
            "http": get_file_url,
            "https": get_file_url,
            "bucket": self.get_file_s3
        }
        protocol = urlparse(file_url).scheme.lower()
        if protocol not in audio_func.keys():
            err_msg = f"unable to download {file_url}: protocol '{protocol}' not supported. Should be one of {list(audio_func.keys())}"
            raise GetFileException(err_msg)

        try:
            audio_bytes = audio_func[protocol](file_url)
        except Exception as e:
            err_msg = f"Skipping audio {file_url} due to error {e}"
            raise GetFileException(err_msg)

        return audio_bytes

    def get_boto_session(self) -> boto3.session.Session:
        global boto_session
        if boto_session is not None:
            return boto_session

        # initialize boto session
        boto_session = boto3.session.Session(
            aws_access_key_id=self.bucket_key['key'],
            aws_secret_access_key=self.bucket_key['textValue'],
            region_name=self.REGION_NAME
        )
        return boto_session

    def get_file_s3(self, object_url: str) -> bytes:
        """
        Получение содержимого аудио-файла из yandex cloud бакета
        :param object_url: полный путь к объекту в бакете с указанием протокола bucket (ex. bucket://src/speechsense/data/my_file.mp3)
        :return: бинарное содержимое файла
        """
        # инициализация сессии и клиента
        s3 = self.get_boto_session().client(
            "s3", endpoint_url=self.S3_ENDPOINT)

        # исключаем префикс 'bucket://'
        parsed_url = urlparse(object_url)
        object_key = parsed_url.hostname + parsed_url.path

        # получаем объект
        get_object_response = s3.get_object(Bucket=self.bucket_name, Key=object_key)
        return get_object_response['Body'].read()
