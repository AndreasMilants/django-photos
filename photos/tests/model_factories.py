import factory
from ..models import GALLERY_MODEL, PHOTO_MODEL
from django.utils.text import slugify
from io import BytesIO
from PIL import Image
from django.core.files.base import File


def get_image_file(name='test.png', ext='png', size=(2000, 2000)):
    color = (255, 0, 0, 0)
    file_obj = BytesIO()
    image = Image.new("RGB", size=size, color=color)
    image.save(file_obj, ext)
    file_obj.seek(0)
    return File(file_obj, name=name)


class GalleryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GALLERY_MODEL

    title = factory.Sequence(lambda n: 'gallery{0:0>3}'.format(n))
    slug = factory.LazyAttribute(lambda a: slugify(a.title))


class PhotoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PHOTO_MODEL

    image = factory.django.ImageField(from_file=get_image_file())
