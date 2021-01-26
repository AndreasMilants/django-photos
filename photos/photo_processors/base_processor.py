import os
from django.conf import settings
from ..photo_processors.utils import handle_zip
from ..models import PHOTO_MODEL, UploadedPhotoModel


class PhotoProcessingError(Exception):
    """An exception that can be raised when you want to output an error to the user"""
    def __init__(self, message):
        self.message = message


class BasePhotoProcessor:
    def handle_zip(self, file, upload_id):
        handle_zip(file, upload_id)

    def handle_photo(self, file, upload_id):
        photo = PHOTO_MODEL(image=file)
        photo.save()
        UploadedPhotoModel.objects.create(photo=photo, upload_id=upload_id)

    def handle_file(self, file, upload_id):
        name, extension = os.path.splitext(file.name)
        if extension == '.zip':
            self.handle_zip(file, upload_id)
        else:
            self.handle_photo(file, upload_id)

    def delete_photo(self, photo):
        photo.delete()  # Calls photo.delete_all_files

    def delete_photos(self, photos):
        for photo in photos:
            photo.delete_all_files()
        photos.delete()  # Bulk delete queryset

    def link_photos_to_gallery(self, upload_id, gallery):
        u_m = UploadedPhotoModel.objects.filter(upload_id=upload_id).select_related('photo').only('id', 'photo_id')
        if gallery is not None:
            gallery.photos.add(*[uploaded_model.photo for uploaded_model in u_m])
        u_m.delete()


_PHOTO_PROCESSOR = getattr(settings, 'PHOTO_PROCESSOR', BasePhotoProcessor())


def get_photo_processor() -> BasePhotoProcessor:
    return _PHOTO_PROCESSOR
