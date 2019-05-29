from collections import UserDict
import json
import re

class Message(UserDict):
    PROTOCOL_RE = re.compile(r'(?:.*/)?(.+)/(\d\.\d)/(.+)$')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        type_info = Message.parse_type_info(self.type)
        if type_info:
            self.protocol, self.version, self.short_type = type_info

    @property
    def type(self):
        return self['@type']

    @staticmethod
    def parse_type_info(type_info_str):
        matches = Message.PROTOCOL_RE.match(type_info_str)
        if not matches:
            return None

        return matches.group(1), matches.group(2), matches.group(3)

    @staticmethod
    def deserialize(serialized: str):
        return Message(json.loads(serialized))

    def serialize(self):
        return json.dumps(self.data)
