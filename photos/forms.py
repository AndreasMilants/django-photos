from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import GALLERY_MODEL, PHOTO_MODEL, UploadedPhotoModel, USE_CELERY
from uuid import uuid4
from django.urls import reverse_lazy
import os
from .utils import handle_zip
from .widgets import DropzoneWidget
from django.contrib.admin.widgets import FilteredSelectMultiple

if USE_CELERY:
    from .models import UploadIdsToGallery, TempZipFile
    from .tasks import parse_zip


class BaseUploadPhotosToGalleryForm(forms.Form):
    upload_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid4)
    new_photos = forms.FileField(widget=DropzoneWidget(options={'url': reverse_lazy('image_upload')}),
                                 required=False, label='')

    def __init__(self, files=None, instance=None, *args, **kwargs):
        super().__init__(files=files, *args, **kwargs)

    def _save_m2m(self):
        gallery = self.instance
        upload_id = self.cleaned_data['upload_id']

        if self.files:  # Javascript is disabled in the browser
            photos = []
            for file in self.files.getlist('new_photos'):
                name, extension = os.path.splitext(file.name)
                if extension == '.zip':
                    if USE_CELERY:
                        temp = TempZipFile.objects.create(file=file)
                        parse_zip.delay(temp.id, upload_id)
                    else:
                        handle_zip(file, upload_id)
                else:
                    photo = PHOTO_MODEL(image=file)
                    photo.save()
                    photos.append(photo)
            if gallery is not None:
                gallery.photos.add(*photos)
        else:  # Normal save (when user has js enabled)
            # Should make sure we delete the same uploaded_models as photos we added to the gallery, because of celery
            u_m = UploadedPhotoModel.objects.filter(upload_id=upload_id).select_related('photo').only('id', 'photo_id')
            if gallery is not None:
                gallery.photos.add(*[uploaded_model.photo for uploaded_model in u_m])
            u_m.delete()

        if USE_CELERY and gallery is not None:
            # This model is used because photos from zip_files might not be created yet upon completion of this function
            UploadIdsToGallery.objects.create(upload_id=upload_id, gallery=gallery)

    def save(self, commit=True):
        if isinstance(self, forms.ModelForm):
            return super().save(commit=commit)
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        if commit:
            self._save_m2m()
        else:
            self.save_m2m = self._save_m2m
        return self.instance


class UploadPhotosToExistingGalleryForm(BaseUploadPhotosToGalleryForm):
    gallery = forms.ModelChoiceField(queryset=GALLERY_MODEL.objects.all(), required=False, help_text=_(
        'Add these photos to an existing gallery or leave this empty.'))

    def clean(self):
        cleaned_data = super().clean()
        self.instance = cleaned_data['gallery']
        return cleaned_data


class UploadPhotosToNewGalleryForm(BaseUploadPhotosToGalleryForm, forms.ModelForm):
    class Meta:
        model = GALLERY_MODEL
        exclude = ('id', 'photos', 'slug')


class BaseAdminUploadPhotosFormAdminUrl(BaseUploadPhotosToGalleryForm):
    new_photos = forms.FileField(widget=DropzoneWidget(options={'url': reverse_lazy('admin:image_upload')}),
                                 required=False, label='')


class UploadPhotosToNewGalleryAdminForm(BaseAdminUploadPhotosFormAdminUrl, UploadPhotosToNewGalleryForm):
    pass


class UploadPhotosToExistingGalleryAdminForm(BaseAdminUploadPhotosFormAdminUrl, UploadPhotosToExistingGalleryForm):
    pass


class SinglePhotoForm(forms.ModelForm):
    galleries = forms.ModelMultipleChoiceField(GALLERY_MODEL.objects.all(),
                                               widget=FilteredSelectMultiple(_('Galleries'), False),
                                               required=False, label=_('Galleries'))

    class Meta:
        model = PHOTO_MODEL
        exclude = ('id',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial:
            self.fields['galleries'].initial = self.instance.galleries.all().values_list('id', flat=True)

    def save(self, commit=True):
        photo = super().save(commit=commit)
        photo.galleries.set(self.cleaned_data['galleries'])
        return photo


class GalleryForm(forms.ModelForm):
    photos = forms.ModelMultipleChoiceField(PHOTO_MODEL.objects.filter(uploaded_photo__isnull=True),
                                            widget=FilteredSelectMultiple(_('Photos'), False), required=False,
                                            label=_('Photos'),
                                            help_text=_('Add already uploaded photos to this gallery'))
    class Meta:
        model = GALLERY_MODEL
        exclude = ('id', 'slug')
        fields = ('title', 'photos', 'description')
