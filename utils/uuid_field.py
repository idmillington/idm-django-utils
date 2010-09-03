import uuid
from django.db import models

class UUIDField(models.CharField):
    """
    A field that holds the ISO-standard format of a random 128-bit UUID.
    """
    @staticmethod
    def rnd_uuid():
        return str(uuid.uuid4())

    def __init__(self, *args, **kws):
        kws.setdefault('default', UUIDField.rnd_uuid)
        kws.setdefault('max_length', 36)
        super(UUIDField, self).__init__(*args, **kws)
