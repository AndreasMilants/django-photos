from ..photo_processors.base_processor import BasePhotoProcessor
from ..models import PHOTO_MODEL, UploadedPhotoModel, TempZipFile, UploadIdsToGallery
from ..photo_processors.celery_tasks import parse_zip, delete_photo, delete_photo_files


class CeleryProcessor(BasePhotoProcessor):
    def handle_zip(self, file, upload_id):
        temp = TempZipFile.objects.create(file=file)
        parse_zip.delay(temp.id, upload_id)

    def handle_photo(self, file, upload_id):
        photo = PHOTO_MODEL(image=file)
        photo.save(process=False)
        UploadedPhotoModel.objects.create(photo=photo, upload_id=upload_id)

    def delete_photo(self, photo):
        delete_photo.delay(photo)

    def delete_photos(self, photos):
        for photo in photos:
            delete_photo_files.delay(photo.image.name)
        photos.delete()

    def link_photos_to_gallery(self, upload_id, gallery):
        super().link_photos_to_gallery(upload_id, gallery)
        # Celery might still be processing at this moment, that's why we make this model to check later
        UploadIdsToGallery.objects.create(upload_id=upload_id, gallery=gallery)
