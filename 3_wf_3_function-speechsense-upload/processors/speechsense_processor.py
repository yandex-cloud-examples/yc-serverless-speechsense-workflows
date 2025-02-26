# speechsense_processor.py
import json
import uuid
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from yandex.cloud.speechsense.v1 import audio_pb2
from yandex.cloud.speechsense.v1 import talk_service_pb2
from yandex.cloud.speechsense.v1 import talk_service_pb2_grpc
from yandex.cloud.speechsense.v1 import text_pb2

from setup_logger import logger
from processors.src_processor import SrcProcessor


def prepare_grpc_meta(token: str) -> tuple:
    return ('authorization', f'Api-Key {token}'), ('x-client-request-id', str(uuid.uuid4()))


class SpeechSenseUploader:

    SPEECHSENSE_ENDPOINTS = {"preprod": "api.speechsense.cloud-preprod.yandex.net:443",
                             "prod": "api.speechsense.yandexcloud.net:443",
                             "talk-analytics": "api.talk-analytics.yandexcloud.net:443"}
    SPEECHSENSE_AUDIO_FORMATS = {'mp3': audio_pb2.ContainerAudio.ContainerAudioType.CONTAINER_AUDIO_TYPE_MP3,
                                 'wav': audio_pb2.ContainerAudio.ContainerAudioType.CONTAINER_AUDIO_TYPE_WAV,
                                 'ogg': audio_pb2.ContainerAudio.ContainerAudioType.CONTAINER_AUDIO_TYPE_OGG_OPUS}

    def __init__(
            self,
            src_processor: SrcProcessor,
            speechsense_env: str = "prod"
    ):

        if speechsense_env not in self.SPEECHSENSE_ENDPOINTS.keys():
            raise ValueError(f"undefined {speechsense_env} Should be one of {list(self.SPEECHSENSE_ENDPOINTS.keys())}")
        self.speechsense_env = speechsense_env
        self.src_processor = src_processor
        self.talk_service_stub = self.prepare_grpc_stub()

    def prepare_grpc_stub(self) -> talk_service_pb2_grpc.TalkServiceStub:

        endpoint = self.SPEECHSENSE_ENDPOINTS[self.speechsense_env]
        creds = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel(endpoint, creds, options=[('grpc.max_send_message_length', 128 * 1024 * 1024)])

        return talk_service_pb2_grpc.TalkServiceStub(channel)

    def upload(self, metadata_fields: dict, file_url: str, settings: dict):
        if settings['speechsense_file_format'] == 'text':
            return self.upload_text(metadata_fields, file_url, settings)
        else:
            return self.upload_audio(metadata_fields, file_url, settings)

    def upload_audio(self, metadata_fields: dict, file_url: str, settings: dict):

        metadata = talk_service_pb2.TalkMetadata(connection_id=settings['speechsense_connection_id'],
                                                 fields=metadata_fields)
        content = audio_pb2.AudioRequest(
            audio_metadata=audio_pb2.AudioMetadata(
                container_audio=audio_pb2.ContainerAudio(
                    container_audio_type=self.SPEECHSENSE_AUDIO_FORMATS[settings['speechsense_file_format']])
            ),
            audio_data=audio_pb2.AudioChunk(data=self.src_processor.get_file(file_url))
        )

        # Формирование запроса к API
        request = talk_service_pb2.UploadTalkRequest(metadata=metadata, audio=content)

        return self.talk_service_stub.Upload(request, metadata=prepare_grpc_meta(settings['speechsense_api_key']))

    def upload_text(self, metadata_fields: dict, file_url: str, settings: dict):

        logger.debug(metadata_fields)

        metadata = talk_service_pb2.TalkMetadata(
            connection_id=str(settings['speechsense_connection_id']),
            fields=metadata_fields)
        content = text_pb2.TextContent(messages=self.get_text_messages(metadata_fields, file_url))

        # Формирование запроса к API
        request = talk_service_pb2.UploadTextRequest(
            metadata=metadata,
            text_content=content
        )

        return self.talk_service_stub.UploadText(request, metadata=prepare_grpc_meta(settings['speechsense_api_key']))

    def get_text_messages(self, metadata_fields: dict, file_url: str):

        text_data = json.loads(self.src_processor.get_file(file_url))['messages']
        # fix user_id field

        user_id = str(metadata_fields['client_id'])
        operator_id = str(metadata_fields['operator_id'])

        text_data = list(
            map(
                lambda x: {'user_id' if str(k).lower() == 'userid' else k: v for k, v in x.items()},
                text_data))
        # меняем все user_id кроме самого клиента на operator_id из метаданных
        text_data = list(
            map(
                lambda x: {k: operator_id if k == 'user_id' and str(v) != user_id else str(v) for k, v in x.items()},
                text_data))

        message_list = []
        for message in text_data:
            timestamp = Timestamp()
            timestamp.FromJsonString(value=str(message['timestamp']))
            message_proto = text_pb2.Message(
                user_id=str(message['user_id']),
                text=text_pb2.TextPayload(text=str(message['text'])),
                timestamp=timestamp
            )
            message_list.append(message_proto)
        return message_list
