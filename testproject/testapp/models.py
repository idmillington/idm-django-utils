from django.db import models

import dj_utils.fields as dj_fields

class TestModel(models.Model):
    json_data = dj_fields.json.JSONField()
    pickle_data = dj_fields.pickle.PickledObjectField()
    uuid = dj_fields.uuid.UUIDField()
    restricted_slug = dj_fields.slug.RestrictedSlugField()
    ido = dj_fields.ido.ObfuscatedIdField(
        bits = 30,
        seed = "f2edbc65-8064-40b8-a0b3-d6579246b37d"
        )
