from django.test import TestCase
from .model_factories import PhotoFactory, GalleryFactory


class PhotologueBaseTest(TestCase):
    def setUp(self):
        self.p1 = PhotoFactory()

    def tearDown(self):
        self.p1.delete()


class GalleryAndPhotoTest(PhotologueBaseTest):
    def setUp(self):
        super().setUp()
        self.g1 = GalleryFactory()

    def tearDown(self):
        super().tearDown()
        self.g1.delete()
