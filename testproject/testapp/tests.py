from django.test import TestCase

import models

class TestPickleField(TestCase):
    def test_default(self):
        m = models.TestModel()
        self.assertEqual(m.pickle_data, None)

    def test_set(self):
        m = models.TestModel()
        data = dict(foo=1, bar=2)
        m.pickle_data = data
        m.save()
        m = models.TestModel.objects.get(pk=m.id)
        self.assertEqual(m.pickle_data, data)

class TestJSONField(TestCase):
    def test_default(self):
        m = models.TestModel()
        self.assertEqual(m.json_data, None)

    def test_set(self):
        m = models.TestModel()
        data = dict(foo=1, bar=2)
        m.json_data = data
        m.save()
        m = models.TestModel.objects.get(pk=m.id)
        self.assertEqual(m.json_data, data)

    def test_get_json(self):
        m = models.TestModel()
        data = dict(foo=1)
        m.json_data = data
        m.save()
        m = models.TestModel.objects.get(pk=m.id)
        self.assertEqual(m.get_json_data_json(), '{"foo": 1}')
