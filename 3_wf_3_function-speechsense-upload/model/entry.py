"""
SpeechSense metadata entry holder class with json serializers
"""
from datetime import datetime
from jsonschema import validate

class Entry:
    """
    Entry holder class
    """
    REQUIRED_FIELDS = ["id", "operator_name", "operator_id", "client_name", "client_id", "date", "direction_outgoing",
                       "language", "file_url", "lockbox_secret_id"]

    SCHEMA = {
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
            "file_url": {"type": "string"},
            "lockbox_secret_id": {"type": "string"}
        },
        "required": REQUIRED_FIELDS
    }

    def __init__(self, dct: dict):

        # простановка значений для подсказок анализатору
        # возможно, переделать на аннотации
        self.id = None
        self.operator_name = None
        self.operator_id = None
        self.client_name = None
        self.client_id = None
        self.date = None
        self.direction_outgoing = None
        self.language = None
        self.file_url = None
        self.lockbox_secret_id = None
        #self.metadata_file = None
        self.additional_metadata = None

        # валидация словаря и заполнение аттрибутов класса
        validate(dct, self.SCHEMA)
        for key in self.REQUIRED_FIELDS:
            setattr(self, key, dct[key])
        self.additional_metadata = {k: dct[k] for k in set(list(dct.keys())) - set(self.REQUIRED_FIELDS) if dct[k]}

        # ключ записи должен быть задан
        if not self.id:
            raise ValueError("entries id field is empty")

        # приведение поля даты к требуемому формату
        if self.date and self.date.endswith("Z"):
            self.date = self.date[:-1]
        self.date = datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%dT%H:%M:%S.000")

        # поле direction_outgoing
        self.direction_outgoing = str(self.direction_outgoing == "0").lower()

    def to_dict(self):
        return {k: getattr(self, k) for k in self.REQUIRED_FIELDS} | self.additional_metadata

    def required_fields_dict(self):
        return {k: getattr(self, k) for k in self.REQUIRED_FIELDS}

    def __repr__(self):
        return "<{klass} @{id:x} {attrs}>".format(
            klass=self.__class__.__name__,
            id=id(self) & 0xFFFFFF,
            attrs=", ".join("{}={!r}".format(k, v) for k, v in self.__dict__.items()),
        )

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Entry):
            return self.id == other.id
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)
