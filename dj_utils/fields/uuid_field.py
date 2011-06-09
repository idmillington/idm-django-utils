import uuid
from django.db import models

class UUIDField(models.CharField):
    """
    A field that holds the ISO-standard format of a random 128-bit UUID.
    """
    @staticmethod
    def rnd_uuid1():
        """Generate a random UUID1"""
        return str(uuid.uuid1())

    @staticmethod
    def rnd_uuid4():
        """Generate a random UUID4 (the default for the field)."""
        return str(uuid.uuid4())

    def __init__(self, *args, **kws):
        kws.setdefault('default', UUIDField.rnd_uuid4)
        kws.setdefault('max_length', 36)
        super(UUIDField, self).__init__(*args, **kws)
