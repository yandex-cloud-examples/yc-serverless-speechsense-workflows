import json

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from setup_logger import logger

SCHEMA = {
    "type": "object",
    "properties": {
        "source_system_id": {"type": "string"},
        "bucket_folder": {"type": "string"},
        "metadata": {"type": "array"}
    },
    "required": ["source_system_id", "bucket_folder", "metadata"]
}

METADATA_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "operator_id": {"type": "string"},
        "operator_name": {"type": "string"},
        "client_id": {"type": "string"},
        "client_name": {"type": "string"},
        "date": {"type": "string"},
        "direction_outgoing": {"type": "string", "enum": ["0", "1"]},
        "language": {"type": "string"},
        "file_name": {"type": "string"}
    },
    "required": ["id", "operator_name", "operator_id", "client_name", "client_id", "date",
                 "direction_outgoing", "language", "file_name"]
}


def handler(event, context):
    logger.info(event)

    # возвращаем словарь с эелементами:
    # schema_error: включаем event и ошибку при неправильной структуре
    # corrupted_records: включаем записи и ошибку для записей с неправильной структурой
    # file: event с записями в правильной структуре

    try:
        # проверка общей схемы файла
        validate(event, SCHEMA)
    except ValidationError as e:
        logger.error(f"error while validating: wrong file structure: {e}")
        return {'error': e.message}

        # оставляем только корректные записи
    record = {}
    corrupted_records = []

    for m in event['metadata']:
        try:
            validate(m, METADATA_SCHEMA)
            if m['id'] in record:
                raise Exception('duplicate record in file - already submitted for upload')
            record.update({m['id']: m})
        except Exception as e:
            logger.error(f"error while validating: wrong metadata entry: {e}")
            corrupted_records.append(
                {"record": json.dumps(m, sort_keys=False, indent=4, ensure_ascii=False), "schema_error": repr(e)})

    return {"source_system_id": event['source_system_id'],
            "bucket_folder": event['bucket_folder'],
            'corrupted_records': corrupted_records,
            'metadata': list(record.values())}
