from .helpers import PhotologueBaseTest
from .model_factories import GalleryFactory, PhotoFactory
from ..models import PHOTO_MODEL, IMAGE_SIZES, UPLOAD_TO
import os


class GalleryTest(PhotologueBaseTest):

    def setUp(self):
        # Create a gallery with 2 photos
        super().setUp()
        self.test_gallery = GalleryFactory()
        self.p2 = PhotoFactory()
        self.test_gallery.photos.add(self.p1, self.p2)

    def tearDown(self):
        super(GalleryTest, self).tearDown()
        self.p2.delete()

    def test_random_photo(self):
        """Method 'sample' should return a random queryset of photos from the
        gallery."""
        photo = self.test_gallery.get_random_photo()

        self.assertIn(photo, [self.p1, self.p2])


class PhotoTest(PhotologueBaseTest):
    def test_new_photo(self):
        self.assertEqual(PHOTO_MODEL.objects.count(), 1)
        self.assertTrue(self.p1.image.storage.exists(self.p1.image.name))

    def test_sizes_created_and_get_filepath_for_size(self):
        for size in IMAGE_SIZES.values():
            self.assertTrue(self.p1.image.storage.exists(self.p1.get_filepath_for_size(size)))

    def test_photo_deleted(self):
        self.assertEqual(PHOTO_MODEL.objects.count(), 1)
        photo = PhotoFactory()
        self.assertEqual(PHOTO_MODEL.objects.count(), 2)
        photo.delete()
        self.assertEqual(PHOTO_MODEL.objects.count(), 1)

    def test_files_deleted(self):
        photo = PhotoFactory()
        for size in IMAGE_SIZES.values():
            self.assertTrue(photo.image.storage.exists(photo.get_filepath_for_size(size)))
        photo.delete()
        for size in IMAGE_SIZES.values():
            self.assertFalse(photo.image.storage.exists(photo.get_filepath_for_size(size)))

    def test_url_sizes(self):
        size = IMAGE_SIZES['admin_thumbnail']
        url = self.p1._get_url_for_size(size)

        base, ext = os.path.splitext(self.p1.image.name)

        self.assertIn(base, url)
        self.assertIn(ext, url)
        self.assertIn('{}x{}'.format(size[0], size[1]), url)
        self.assertIn(UPLOAD_TO, url)

    def test_accessor_methods(self):
        self.assertEqual(self.p1.get_admin_thumbnail_url(), self.p1._get_url_for_size(IMAGE_SIZES['admin_thumbnail']))

    def test_admin_thumbnail_tag(self):
        self.assertIn(self.p1.get_admin_thumbnail_url(), self.p1.admin_thumbnail_tag())
