from collections import UserDict
import json
import re

from module import Semver

class InvalidMessageType(Exception): pass

class Message(UserDict):
    MTURI_RE = re.compile(r'(.*?)([a-z0-9._-]+)/(\d[^/]*)/([a-z0-9._-]+)$')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_uri, self.protocol, self.version, self.short_type = \
                Message.parse_type_info(self.type)
        try:
            self.version_info = Semver.from_str(self.version)
        except ValueError as err:
            raise InvalidMessageType('Invalid message type version') from err

    @property
    def type(self):
        return self['@type']

    @property
    def qualified_protocol(self):
        return self.doc_uri + self.protocol

    @staticmethod
    def parse_type_info(message_type_uri):
        matches = Message.MTURI_RE.match(message_type_uri)
        if not matches:
            raise InvalidMessageType()

        return matches.groups()

    @staticmethod
    def deserialize(serialized: str):
        return Message(json.loads(serialized))

    def serialize(self):
        return json.dumps(self.data)
