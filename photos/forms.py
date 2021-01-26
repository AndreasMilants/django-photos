from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import GALLERY_MODEL, PHOTO_MODEL
from uuid import uuid4
from django.urls import reverse_lazy
from .widgets import DropzoneWidget
from django.contrib.admin.widgets import FilteredSelectMultiple
from photos.photo_processors.base_processor import get_photo_processor


class BaseUploadPhotosToGalleryForm(forms.Form):
    upload_id = forms.UUIDField(widget=forms.HiddenInput, initial=uuid4)
    new_photos = forms.FileField(widget=DropzoneWidget(options={'url': reverse_lazy('image_upload')}),
                                 required=False, label=_('Add Photos'))

    def __init__(self, *args, **kwargs):
        if not isinstance(self, forms.ModelForm):
            kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def _save_m2m(self):
        if isinstance(self, forms.ModelForm):
            super()._save_m2m()
        gallery = self.instance
        upload_id = self.cleaned_data['upload_id']

        if self.files:  # Javascript is disabled in the browser
            for file in self.files.getlist('new_photos'):
                get_photo_processor().handle_file(file, upload_id)

        if gallery is not None:
            get_photo_processor().link_photos_to_gallery(upload_id, gallery)

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
        self.instance = cleaned_data.get('gallery', None)
        return cleaned_data


class UploadPhotosToNewGalleryForm(BaseUploadPhotosToGalleryForm, forms.ModelForm):
    class Meta:
        model = GALLERY_MODEL
        exclude = ('id', 'photos', 'slug')


class BaseAdminUploadPhotosFormAdminUrl(BaseUploadPhotosToGalleryForm):
    new_photos = forms.FileField(widget=DropzoneWidget(options={'url': reverse_lazy('admin:image_upload')}),
                                 required=False, label=_('Add Photos'), help_text=_('Add new photos to this gallery'))


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


class GalleryForm(BaseAdminUploadPhotosFormAdminUrl, forms.ModelForm):
    photos = forms.ModelMultipleChoiceField(PHOTO_MODEL.objects.filter(uploaded_photo__isnull=True),
                                            widget=FilteredSelectMultiple(_('Photos'), False), required=False,
                                            label=_('Uploaded Photos'),
                                            help_text=_('Add already uploaded photos to this gallery'))

    class Meta:
        model = GALLERY_MODEL
        fields = ('title', 'description', 'photos', 'new_photos')
