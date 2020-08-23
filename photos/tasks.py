from celery import shared_task
from .models import PHOTO_MODEL, TempZipFile
from .utils import handle_zip


@shared_task(name='photos.tasks.create_sizes', max_retries=5)
def update_sizes(photo_id):
    photo = PHOTO_MODEL.objects.get(id=photo_id)
    photo.update_sizes(running_in_task=True)


@shared_task(name='photos.tasks.delete_files', max_retries=5)
def delete_files(filepath):
    PHOTO_MODEL.delete_files(filepath)


@shared_task(name='photos.tasks.parse_zip', max_retries=5)
def parse_zip(zip_file_id, upload_id):
    file = TempZipFile.objects.get(id=zip_file_id).file
    handle_zip(file, upload_id, running_in_task=True)
