# Some code in this file is based on the code in the package django-photologue:
# Copyright (c) 2007-2019, Justin C. Driscoll and all the people named in
# https://github.com/richardbarran/django-photologue/blob/master/CONTRIBUTORS.txt.

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.files.storage import default_storage
from PIL import Image
from django.utils.encoding import force_str
import os
from io import BytesIO
from django.core.files.base import ContentFile
from uuid import uuid4
import random
from functools import partial
import logging

logger = logging.getLogger('photos.models')

IMAGE_STORAGE = getattr(settings, 'PHOTOS_IMAGE_STORAGE', default_storage)
TEMP_FILE_STORAGE = getattr(settings, 'PHOTOS_TEMP_FILE_STORAGE', default_storage)
IMAGE_SIZES = {'admin_thumbnail': (100, 100)}
_IMAGE_SIZES = getattr(settings, 'PHOTOS_IMAGE_SIZES', {'display': (500, 500),
                                                        'hd': (1920, 1080)})  # (Width, Height)
IMAGE_SIZES.update(_IMAGE_SIZES)
_SIZE_METHOD_MAP = {}
USE_ASYNC = getattr(settings, 'PHOTOS_USE_ASYNC', False)
UPLOAD_TO = getattr(settings, 'PHOTOS_UPLOAD_TO', 'photos')


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)

    class Meta:
        abstract = True


class UpdateTimesModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ImageModel(models.Model):
    image = models.ImageField(verbose_name=_('image'), storage=IMAGE_STORAGE, upload_to=UPLOAD_TO, null=False)

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_image = self.image

    def image_filename(self):
        return os.path.basename(force_str(self.image.name))

    def _old_image_filename(self):
        return None if self._old_image is None else os.path.basename(force_str(self._old_image.name))

    @staticmethod
    def _get_filepath_for_size(filename, size):
        base, ext = os.path.splitext(filename)
        return '{}/{}_{}x{}{}'.format(UPLOAD_TO, base, size[0], size[1], ext)

    def get_filepath_for_size(self, size):
        return self._get_filepath_for_size(self.image_filename(), size)

    def _get_url_for_size(self, size):
        base, ext = os.path.splitext(self.image.url)
        return '{}_{}x{}{}'.format(base, size[0], size[1], ext)

    def _get_SIZE_url(self, size_name):  # Call this with get_admin_thumbnail_url()
        size = IMAGE_SIZES[size_name]
        return self._get_url_for_size(size)

    def admin_thumbnail_tag(self):
        return mark_safe('''<a href="{}">
                                <div style="background: url(\'{}\') no-repeat center center; background-size: cover; 
                                            width: 50px; height: 50px">
                                </div>
                            </a>'''.format(self.image.url, self.get_admin_thumbnail_url()))

    admin_thumbnail_tag.short_description = _('Thumbnail')

    def _create_size(self, size):
        try:
            with Image.open(self.image) as image:
                image.thumbnail(size, Image.ANTIALIAS)
                filename = self.get_filepath_for_size(size)
                buffer = BytesIO()
                image.save(buffer, image.format, optimize=True)
                buffer_contents = ContentFile(buffer.getvalue())
                self.image.storage.save(filename, buffer_contents)
        except OSError as e:
            logger.error('Error creating size: {}'.format(e))
            raise e

    def _create_sizes(self):
        for size in IMAGE_SIZES.values():
            self._create_size(size)

    @staticmethod
    def _delete_size(filename, size):
        try:
            IMAGE_STORAGE.delete(ImageModel._get_filepath_for_size(filename, size))
        except OSError as e:
            logger.warning("Couldn't delete photo: {}".format(e))
            raise e

    @staticmethod
    def _delete_sizes(filename):
        for size in IMAGE_SIZES.values():
            ImageModel._delete_size(filename, size)

    @staticmethod
    def delete_files(filepath):
        IMAGE_STORAGE.delete(filepath)
        ImageModel._delete_sizes(os.path.basename(force_str(filepath)))

    def delete_all_files(self):
        self.image.close()
        self.delete_files(self.image.name)

    def _update_sizes(self, old_image_filename):
        if old_image_filename is not None:
            self._delete_sizes(old_image_filename)
        self._create_sizes()

    def update_sizes(self):
        self._update_sizes(self._old_image_filename())

    def save(self, *args, process=True, **kwargs):
        should_update = (self._old_image != self.image or self._state.adding) and process
        super().save(*args, **kwargs)  # Have to save first because filename might change upon save
        if should_update:
            self.update_sizes()

    def delete(self, *args, **kwargs):
        self.delete_all_files()
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.image_filename()

    def __getattr__(self, name):
        if not _SIZE_METHOD_MAP:
            init_size_method_map()
        di = _SIZE_METHOD_MAP.get(name, None)
        if di is not None:
            result = partial(getattr(self, di['base_name']), di['size'])
            setattr(self, name, result)
            return result
        else:
            raise AttributeError


def init_size_method_map():
    for name in IMAGE_SIZES.keys():
        _SIZE_METHOD_MAP['get_%s_url' % name] = {'base_name': '_get_SIZE_url', 'size': name}


class Photo(UUIDModel, UpdateTimesModel, ImageModel):
    class Meta:
        abstract = True


_PHOTO_MODEL = getattr(settings, 'PHOTOS_PHOTO_MODEL', Photo)
PHOTO_MODEL = _PHOTO_MODEL

if _PHOTO_MODEL._meta.abstract:
    class PhotoModel(_PHOTO_MODEL):
        class Meta:
            verbose_name = _('Photo')
            verbose_name_plural = _('Photos')


    PHOTO_MODEL = PhotoModel


class BaseGallery(models.Model):
    photos = models.ManyToManyField(PHOTO_MODEL, verbose_name=_('Photos'), blank=True, related_name='galleries')

    class Meta:
        abstract = True

    def get_random_photo(self):
        size = PHOTO_MODEL.objects.filter(galleries=self).count()
        if size > 0:
            r = random.randrange(0, size)
            return PHOTO_MODEL.objects.filter(galleries=self)[r]
        return None

    def random_photo_tag(self):
        photo = self.get_random_photo()
        if photo is None:
            return mark_safe('<a href="{}"><div style="width: 50px; height: 50px"></div></a>')
        return photo.admin_thumbnail_tag()

    random_photo_tag.short_description = _('sample')


class Gallery(UUIDModel, UpdateTimesModel, BaseGallery):
    title = models.CharField(max_length=255, unique=True, verbose_name=_('title'))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_('slug'))
    description = models.TextField(verbose_name=_('description'))

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)  # We want to update the slug if title changed
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


_GALLERY_MODEL = getattr(settings, 'PHOTOS_GALLERY_MODEL', Gallery)
GALLERY_MODEL = _GALLERY_MODEL

if _GALLERY_MODEL._meta.abstract:
    class GalleryModel(_GALLERY_MODEL):
        class Meta:
            verbose_name = _('Gallery')
            verbose_name_plural = _('Galleries')
            ordering = ('-created_at', '-updated_at', 'title')


    GALLERY_MODEL = GalleryModel


class UploadedPhotoModel(UpdateTimesModel):
    """These model-instances and their attached photos should be deleted once every few ~days"""
    photo = models.ForeignKey(PHOTO_MODEL, verbose_name=_('photo'), null=False, on_delete=models.CASCADE,
                              related_name='uploaded_photo')
    upload_id = models.UUIDField(db_index=True, verbose_name=_('upload id'), null=False)


if USE_ASYNC:
    class UploadIdsToGallery(UpdateTimesModel):
        """
        This table temporarily saves all the links of upload_ids to galleries.
        This is only used when using async, because the uploaded_photo_model might already be checked before all
        rows were created.
        After using this to link photos to a gallery, you should also set confirmed to True
        """
        upload_id = models.UUIDField(primary_key=True)
        gallery = models.ForeignKey(GALLERY_MODEL, on_delete=models.CASCADE, null=True)


    class TempZipFile(models.Model):
        file = models.FileField(storage=TEMP_FILE_STORAGE)
