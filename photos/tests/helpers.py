from django.test import TestCase
from .model_factories import PhotoFactory


class PhotologueBaseTest(TestCase):
    def setUp(self):
        self.p1 = PhotoFactory()

    def tearDown(self):
        pass
        self.p1.delete()
