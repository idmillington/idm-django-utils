"""
A more restricted slug field.
"""
import django.db.models as models
import django.forms as forms
import django.core.validators as validators
from django.utils.translation import ugettext as _

default_error = _(
    u"Slugs must consist of lower case letters, numbers and hyphens, starting "
    u"with a letter, and ending with a letter or a number."
    )

# This can be used in place of django.core.validators.slug_re
restricted_slug_re = re.compile(r'^[-\w]+$')

# This can be used in place of django.core.validators.validate_slug
validate_resstricted_slug = RegexValidator(
    restricted_slug_re,
    default_error,
    'invalid')

# The slug form field that is used, by default, by the new slug field.
class RestrictedSlugFormField(forms.SlugField):
    default_error_messages = {'invalid': default_error}
    default_validators = [validate_restricted_slug]

# A drop-in replacement for the normal django slug field.
class RestrictedSlugField(models.SlugField):
    def formfield(self, **kws):
        defaults = dict(form_class=RestrictedSlugFormField)
        defaults.update(kws)
        return super(RestrictedSlugField, self).formfield(**defaults)

