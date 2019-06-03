from collections import UserDict
import json
import re

class InvalidMessageType(Exception): pass
class InvalidMessageTypeVersion(Exception): pass

class Semver:
    __slots__ = 'major', 'minor', 'patch', 'pre', 'build'
    def __init__(self, major, minor, patch, pre, build):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre = pre
        self.build = build


class Message(UserDict):
    MTURI_RE = re.compile(r'(.*?)([a-z0-9._-]+)/(\d[^/]*)/([a-z0-9._-]+)$')
    SEMVER_RE = re.compile(
        r'^(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?'
        r'(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_uri, self.protocol, self.version, self.short_type = \
                Message.parse_type_info(self.type)
        self.version_info = Semver(*Message.parse_version_info(self.version))

    @property
    def type(self):
        return self['@type']

    @staticmethod
    def parse_type_info(message_type_uri):
        matches = Message.MTURI_RE.match(message_type_uri)
        if not matches:
            raise InvalidMessageType()

        return matches.groups()

    @staticmethod
    def parse_version_info(version_str):
        matches = Message.SEMVER_RE.match(version_str)
        if not matches:
            raise InvalidMessageTypeVersion

        return matches.groups()

    @staticmethod
    def deserialize(serialized: str):
        return Message(json.loads(serialized))

    def serialize(self):
        return json.dumps(self.data)
