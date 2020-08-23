import os
import zipfile
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile

from .models import PHOTO_MODEL, UploadedPhotoModel


def handle_zip(file, upload_id, running_in_task=False):
    zip_file = zipfile.ZipFile(file)
    photos = []
    for filename in sorted(zip_file.namelist()):
        if filename.startswith('__') or filename.startswith('.'):
            continue
        if os.path.dirname(filename):
            continue
        data = zip_file.read(filename)
        if not len(data):
            continue

        try:
            file = BytesIO(data)
            opened = Image.open(file)
            opened.verify()
            photo = PHOTO_MODEL()
            content_file = ContentFile(data)
            photo.image.save(filename, content_file)
            photo.save(running_in_task=running_in_task)
            photos.append(photo)
        except Exception:
            pass
    zip_file.close()

    UploadedPhotoModel.objects.bulk_create([UploadedPhotoModel(upload_id=upload_id, photo=photo) for photo in photos])
