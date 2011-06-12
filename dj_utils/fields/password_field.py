import uuid
import hashlib

import django.forms as forms
from django.db import models
import django.contrib.auth.models as auth_models

class PasswordField(models.CharField):
    """
    A field for storing passwords, where the passwords are stored
    encrypted with a random salt and adjustable hashing algorithm.
    """
    def __init__(self, *args, **kwargs):
        self.algorithm = kwargs.get('algorithm', 'sha1')
        if 'algorithm' in kwargs: del kwargs['algorithm']
        kwargs.setdefault('max_length', 128)
        super(PasswordField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        """
        Add password setting and checking.
        """
        super(PasswordField, self).contribute_to_class(cls, name)

        def set_password(model_instance, raw_password):
            """
            Encrypts and sets the password.
            """
            algorithm = 'sha1'
            salt = str(uuid.uuid4())
            hsh = auth_models.get_hexdigest(algorithm, salt, raw_password)
            setattr(
                model_instance, self.attname,
                "%s$%s$%s" % (algorithm, salt, hsh)
                )

        def check_password(model_instance, raw_password):
            """
            Checks the password against the given content.
            """
            current = getattr(model_instance, self.attname, None)
            if not current:
                return not raw_password
            else:
                return auth_models.check_password(raw_password, current)

        setattr(cls, 'set_%s' % self.name, set_password)
        setattr(cls, 'check_%s' % self.name, check_password)

    def formfield(self, **kwargs):
        """
        Returns a CharField with the PasswordInput widget.
        """
        defaults = {'widget': forms.PasswordInput}
        defaults.update(kwargs)
        return super(PasswordField, self).formfield(**defaults)

# If we're using south for schema migration, then register this field.
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(
        [(
                [PasswordField],
                [],
                {
                    "algorithm": ("algorithm", {"default":"sha1"})
                }
        )],
        ["^dj_utils\.fields\.password_field\.PasswordField"]
        )
except ImportError:
    pass
