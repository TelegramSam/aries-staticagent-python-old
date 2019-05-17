from collections import UserDict
import json

class Message(UserDict):
    @property
    def type(self):
        return self['@type']

    @staticmethod
    def deserialize(serialized: str):
        return Message(json.loads(serialized))

    def serialize(self):
        return json.dumps(self.data)
