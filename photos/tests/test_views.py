from django.test import TestCase
from django.urls import reverse_lazy
from ..models import PHOTO_MODEL, UploadedPhotoModel, IMAGE_SIZES
from .model_factories import get_image_file, get_zip_file
import time
from uuid import uuid4


class UploadPhotoApiViewTest(TestCase):
    def check_photo_ok_and_delete(self, photo):
        self.assertTrue(photo.image.storage.exists(photo.image.name))
        for size in IMAGE_SIZES.values():
            self.assertTrue(photo.image.storage.exists(photo.get_filepath_for_size(size)))

        photo.delete()

    def test_upload_photo(self):
        self.client.post(reverse_lazy('image_upload'), {'file': get_image_file(), 'upload_id': str(uuid4())})

        time.sleep(1)  # Different process implementations might need a little bit longer

        self.assertEqual(1, PHOTO_MODEL.objects.count())
        self.assertEqual(1, UploadedPhotoModel.objects.count())
        self.assertEqual(PHOTO_MODEL.objects.first(), UploadedPhotoModel.objects.first().photo)

        photo = PHOTO_MODEL.objects.first()
        self.check_photo_ok_and_delete(photo)

        UploadedPhotoModel.objects.all().delete()

    def test_upload_zip(self):
        zip_file = get_zip_file(images=[get_image_file(name='img1.png'), get_image_file(name='img2.png')])
        self.client.post(reverse_lazy('image_upload'), {'file': zip_file, 'upload_id': str(uuid4())})

        time.sleep(1)  # Different process implementations might need a little bit longer

        self.assertEqual(2, PHOTO_MODEL.objects.count())
        self.assertEqual(2, UploadedPhotoModel.objects.count())

        for photo in PHOTO_MODEL.objects.all():
            self.check_photo_ok_and_delete(photo)

        UploadedPhotoModel.objects.all().delete()
