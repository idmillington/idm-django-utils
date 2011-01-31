import random
import hashlib

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
            salt = auth_models.get_hexdigest(
                algorithm, str(random.random()), str(random.random())
                )[:5]
            hsh = auth_models.get_hexdigest(algorithm, salt, raw_password)
            setattr(
                model_instance, self.attname,
                "%s$%s$%s" % (algorithm, salt, hsh)
                )

        def check_password(model_instance, raw_password):
            """
            Checks the password against the given content.
            """
            return auth_models.check_password(
                raw_password,
                getattr(model_instance, self.attname, None)
                )

        setattr(cls, 'set_%s' % self.name, set_password)
        setattr(cls, 'check_%s' % self.name, check_password)
