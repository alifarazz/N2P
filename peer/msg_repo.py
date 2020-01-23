from typing import Set

class MsgRepo:
    broadcast_uuids: Set = set()

    @classmethod
    def is_broadcast_uuid_dup(cls, uuid):
        return uuid in cls.broadcast_uuids

    @classmethod
    def mark_uuid_as_seen(cls, uuid):
        cls.broadcast_uuids.add(uuid)
