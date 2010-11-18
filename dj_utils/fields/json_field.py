import json
import zlib
import base64

from django.db import models
from django.conf import settings
from datetime import datetime

from django.db import models
from django.utils.encoding import force_unicode

def dbsafe_encode(value):
    return base64.b64encode(zlib.compress(json.dumps(value)))

def dbsafe_decode(value, compress_object=False):
    return json.loads(zlib.decompress(base64.b64decode(value)))

class JSONObject(str):
    pass

class JSONField(models.Field):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('null', True)
        kwargs.setdefault('editable', False)
        super(JSONField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        """
        Add the ability to get the raw JSON strings.
        """
        self.class_name = cls
        super(JSONField, self).contribute_to_class(cls, name)

        def get_raw(model_instance):
            return dbsafe_encode(getattr(model_instance, self.attname, None))
        setattr(cls, 'get_%s_raw' % self.name, get_raw)

    def get_default(self):
        """
        Returns the default value for this field without forcing
        unicode (the default implementation).
        """
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        # If the field doesn't have a default, then we punt to models.Field.
        return super(JSONField, self).get_default()

    def to_python(self, value):
        """
        Return the object, if it is defined.
        """
        if value is not None:
            try:
                value = dbsafe_decode(value)
            except:
                if isinstance(value, JSONObject):
                    raise
        return value

    def get_db_prep_value(self, value):
        """
        JSON and b64encode the object.
        """
        if value is not None and not isinstance(value, JSONObject):
            value = force_unicode(dbsafe_encode(value))
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type not in ['exact', 'in', 'isnull']:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
        # The Field model already calls get_db_prep_value before doing the
        # actual lookup, so all we need to do is limit the lookup types.
        return super(JSONField, self).get_db_prep_lookup(lookup_type, value)
