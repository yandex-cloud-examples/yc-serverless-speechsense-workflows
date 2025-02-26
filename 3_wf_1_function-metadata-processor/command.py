from abc import abstractmethod, ABC
from jsonschema import validate
from datetime import datetime
from setup_logger import logger


# Базовый класс для команд
class Command(ABC):
    @property
    @abstractmethod
    def schema(self):
        pass

    @property
    @abstractmethod
    def sql(self):
        pass

    @abstractmethod
    def execute(self, cursor):
        pass

    def __init__(self, data, request_id):
        validate(data, self.schema)
        self.data = data
        self.request_id = request_id


# Конкретные команды
class LogCorruptedFile(Command):
    schema = {
        "type": "object",
        "properties": {
            "metadata_file_path": {"type": "string"},
            "schema_error": {"type": "string"},
        },
        "required": ["metadata_file_path", "schema_error"]
    }

    sql = """
    insert into public.errors(metadata_file_path, error, request_id, processed_dttm, type)
    values (%s, %s, %s, %s, %s)
    """

    def execute(self, cursor):
        value = (self.data['metadata_file_path'], self.data['schema_error'], self.request_id, str(datetime.now()), 'corrupted_file')
        logger.info(f"SQL: {cursor.mogrify(self.sql, value)}")
        cursor.execute(self.sql, value)


class LogCorruptedRecords(Command):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "metadata_file_path": {"type": "string"},
                "record": {"type": "string"},
                "schema_error": {"type": "string"}
            },
            "required": ["metadata_file_path", "record", "schema_error"]
        }

    }

    sql = """
    insert into public.errors(metadata_file_path, error, record, request_id, processed_dttm, type)
    values (%s, %s, %s, %s, %s, %s)
    """

    def execute(self, cursor):
        values = list(map(lambda e:
                          (
                              e['metadata_file_path'], e['schema_error'], e['record'], self.request_id,
                              str(datetime.now()), 'upload_error')
                          , self.data
                          )
                      )
        logger.info(f"SQL: {self.sql}")
        cursor.executemany(self.sql, values)


# TODO: добавить параметр тип ошибки и оставить один класс для вставки данных в public.errors
class LogUploadErrors(Command):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "metadata_file_path": {"type": "string"},
                "record": {"type": "string"},
                "upload_error": {"type": "string"}
            },
            "required": ["metadata_file_path", "record", "upload_error"]
        }
    }

    sql = """
    insert into public.errors(metadata_file_path, error, record, request_id, processed_dttm, type)
    values (%s, %s, %s, %s, %s, %s)
    """

    def execute(self, cursor):
        values = list(map(lambda e:
                          (
                              e['metadata_file_path'], e['upload_error'], e['record'], self.request_id,
                              str(datetime.now()), 'upload_error')
                          , self.data
                          )
                      )
        logger.info(f"SQL: {self.sql}")
        cursor.executemany(self.sql, values)


class GetSpeechSenseKey(Command):
    schema = {
        "type": "object",
        "properties": {
            "source_system_id": {"type": "string"}
        },
        "required": ["source_system_id"]
    }

    sql = """
    select lockbox_secret_id from public.source_system where source_system_id = '{0}' ;
    """

    def execute(self, cursor):
        logger.info(f"SQL: {cursor.mogrify(self.sql.format(self.data['source_system_id']))}")
        cursor.execute(self.sql.format(self.data['source_system_id']))
        result = cursor.fetchall()
        if result:
            return {'lockbox_secret_id': result[0][0]}
        else:
            return {}


class MarkRecordsUploaded(Command):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "operator_name": {"type": "string"},
                "operator_id": {"type": "string"},
                "client_name": {"type": "string"},
                "client_id": {"type": "string"},
                "date": {"type": "string"},
                "direction_outgoing": {"type": "string"},
                "language": {"type": "string"},
                "file_url": {"type": "string"},
                "source_system_id": {"type": "string"},
                "additional_metadata": {"type": ["string", "null"]},
                "speechsense_talk_id": {"type": "string"},
                "metadata_file_path": {"type": "string"}

            },
            "required": ["id", "operator_name", "operator_id", "client_name", "client_id", "date",
                         "direction_outgoing", "language", "file_url", "source_system_id",
                         "additional_metadata",
                         "speechsense_talk_id", "metadata_file_path"]
        }
    }

    sql = """
    insert into public.talk(id, operator_name, operator_id, client_name, client_id, date, direction_outgoing, 
    language, file_url, source_system_id, additional_metadata, speechsense_talk_id, request_id, processed_dttm, metadata_file_path)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    def execute(self, cursor):
        values = list(map(lambda rec:
                          (rec['id'], rec['operator_name'], rec['operator_id'], rec['client_name'],
                           rec['client_id'], rec['date'], rec['direction_outgoing'], rec['language'],
                           rec['file_url'], rec['source_system_id'], rec['additional_metadata'],
                           rec['speechsense_talk_id'], self.request_id, str(datetime.now()), rec['metadata_file_path'])
                          , self.data))
        logger.info(f"SQL: {self.sql}")
        cursor.executemany(self.sql, values)


class CheckRecordsUploaded(Command):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "source_system_id": {"type": "string"}
            },
            "required": ["id", "source_system_id"]
        }
    }

    sql = """
    select t.id, s.source_system_id
    from public.talk t
    inner join public.source_system s 
    on t.source_system_id = s.source_system_id
    where 1=1 
    and (t.id, s.source_system_id) in %s ;
    """

    def execute(self, cursor):
        ids_source_systems = list(map(lambda x: (x['id'], x['source_system_id']), self.data))
        logger.info(f"SQL: {cursor.mogrify(self.sql, (tuple(ids_source_systems),))}")
        cursor.execute(self.sql, (tuple(ids_source_systems),))
        result = cursor.fetchall()
        return {"uploaded": list(map(lambda x: {"id": x[0], "source_system_id": x[1]}, result))} if result else {
            "uploaded": []}
