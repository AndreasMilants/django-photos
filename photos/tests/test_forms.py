from .helpers import GalleryAndPhotoTest
from ..forms import *
from ..models import UploadedPhotoModel
from uuid import uuid4


class BaseUploadPhotosToGalleryFormTest(GalleryAndPhotoTest):
    def test_save(self):
        self.assertEqual(1, GALLERY_MODEL.objects.count())
        f = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4())})
        f.is_valid()
        f.save()
        self.assertEqual(1, GALLERY_MODEL.objects.count())

        f = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4()), 'gallery': self.g1.pk})
        f.is_valid()
        f.save()
        self.assertEqual(1, GALLERY_MODEL.objects.count())

        f = UploadPhotosToNewGalleryForm(
            data={'upload_id': str(uuid4()), 'title': 'My title', 'description': 'My description'})
        f.is_valid()
        f.save(commit=False)
        self.assertEqual(1, GALLERY_MODEL.objects.count())

        f = UploadPhotosToNewGalleryForm(
            data={'upload_id': str(uuid4()), 'title': 'My title', 'description': 'My description'})
        f.is_valid()
        f.save()
        self.assertEqual(2, GALLERY_MODEL.objects.count())
        f.instance.delete()

    def test_save_m2m(self):
        upload_id = uuid4()
        UploadedPhotoModel.objects.create(photo=self.p1, upload_id=upload_id)

        f = UploadPhotosToExistingGalleryForm(data={'upload_id': str(upload_id), 'gallery': self.g1.pk})
        f.is_valid()
        f.save(commit=False)
        self.assertEqual(1, UploadedPhotoModel.objects.count())
        self.assertEqual(0, self.p1.galleries.count())

        f.save_m2m()
        self.assertEqual(0, UploadedPhotoModel.objects.count())
        self.assertEqual(1, self.p1.galleries.count())
        self.assertEqual(self.g1, self.p1.galleries.first())

        self.p1.galleries.set([])
        UploadedPhotoModel.objects.create(photo=self.p1, upload_id=upload_id)
        self.assertEqual(0, self.p1.galleries.count())
        f.save()
        self.assertEqual(0, UploadedPhotoModel.objects.count())
        self.assertEqual(1, self.p1.galleries.count())
        self.assertEqual(self.g1, self.p1.galleries.first())


class UploadPhotosToExistingGalleryFormTest(GalleryAndPhotoTest):
    def test_init(self):
        UploadPhotosToExistingGalleryForm()
        UploadPhotosToExistingGalleryForm(data={'gallery': 'some fake id'})
        UploadPhotosToExistingGalleryForm(data={'gallery': None})
        UploadPhotosToExistingGalleryForm(data={'gallery': self.g1.pk})

    def test_invalid(self):
        form = UploadPhotosToExistingGalleryForm()
        self.assertFalse(form.is_valid())
        form2 = UploadPhotosToExistingGalleryForm(data={'upload_id': 'fake uuid'})
        self.assertFalse(form2.is_valid())
        form3 = UploadPhotosToExistingGalleryForm(data={'gallery': 'fake uuid'})
        self.assertFalse(form3.is_valid())
        form4 = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4()), 'gallery': 'fake uuid'})
        self.assertFalse(form4.is_valid())
        form5 = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4()), 'gallery': str(uuid4())})
        self.assertFalse(form5.is_valid())
        form6 = UploadPhotosToExistingGalleryForm(data={'upload_id': 'fake uuid', 'gallery': self.g1.pk})
        self.assertFalse(form6.is_valid())

    def test_valid(self):
        form = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4())})
        self.assertTrue(form.is_valid())
        form2 = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4()), 'gallery': self.g1.pk})
        self.assertTrue(form2.is_valid())

    def test_instance(self):
        form = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4())})
        form.is_valid()
        self.assertEqual(form.instance, None)
        form2 = UploadPhotosToExistingGalleryForm(data={'upload_id': str(uuid4()), 'gallery': self.g1.pk})
        form2.is_valid()
        self.assertEqual(form2.instance, self.g1)
