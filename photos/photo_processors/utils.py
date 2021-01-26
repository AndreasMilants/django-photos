import os
import zipfile
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile

from ..models import PHOTO_MODEL, UploadedPhotoModel


def handle_zip(file, upload_id):
    photos = []

    with zipfile.ZipFile(file) as zip_file:
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
                photo.save()
                photos.append(photo)
            except Exception:
                pass

    UploadedPhotoModel.objects.bulk_create([UploadedPhotoModel(upload_id=upload_id, photo=photo) for photo in photos])
