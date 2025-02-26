from yandex.cloud.serverless.workflows.v1 import execution_service_pb2
from yandex.cloud.serverless.workflows.v1 import execution_service_pb2_grpc
from yandex.cloud.serverless.workflows.v1 import execution_pb2
import grpc
import json
import uuid
import os
from setup_logger import logger

WF_ENDPOINT = "serverless-workflows.api.cloud.yandex.net:443"


def prepare_grpc_stub() -> execution_service_pb2_grpc.ExecutionServiceStub:
    creds = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel(WF_ENDPOINT, creds, options=[('grpc.max_send_message_length', 128 * 1024 * 1024)])

    return execution_service_pb2_grpc.ExecutionServiceStub(channel)


def prepare_grpc_meta(token: str) -> tuple:
    return ('authorization', f'Bearer {token}'), ('x-client-request-id', str(uuid.uuid4()))


def check_env_variables() -> dict:
    """
    Проверка, что заданы все необходимые переменные среды
    :return: словарь с требуемыми переменными
    """
    OS_VARS = ['WORKFLOW_ID']
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


def handler(event, context):
    os_args = check_env_variables()

    if 'messages' in event:
        logger.info('processing trigger event')
        logger.debug(event['messages'])
        file_paths = list(map(lambda x: x['details']['object_id'], event['messages']))
    else:
        raise Exception('unable to call function - not a trigger event')

    input_data = execution_pb2.ExecutionInput(
        input_json=json.dumps({'metadataPath': file_paths}, sort_keys=False, indent=4, ensure_ascii=False))

    request = execution_service_pb2.StartExecutionRequest(workflow_id=os_args['WORKFLOW_ID'], input=input_data)

    talk_service_stub = prepare_grpc_stub()
    talk_service_stub.Start(request=request, metadata=prepare_grpc_meta(context.token["access_token"]))
