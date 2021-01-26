from django.contrib import admin
from django.contrib.admin.utils import model_ngettext
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib.admin import helpers
from .models import PHOTO_MODEL, GALLERY_MODEL
from django.urls import path
from .views import UploadPhotoAdminApiView
from .forms import SinglePhotoForm, GalleryForm
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count
from .photo_processors.base_processor import get_photo_processor, PhotoProcessingError
from django.contrib import messages

PHOTO_APP_LABEL = PHOTO_MODEL._meta.app_label
GALLERY_APP_LABEL = GALLERY_MODEL._meta.app_label

GALLERY_MODEL_NAME = GALLERY_MODEL._meta.model_name
PHOTO_MODEL_NAME = PHOTO_MODEL._meta.model_name


class PhotoAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('image_filename', 'admin_thumbnail_tag')
    form = SinglePhotoForm

    def get_queryset(self, request):
        return PHOTO_MODEL.objects.filter(uploaded_photo__isnull=True)

    @staticmethod
    def photo_admin_context(context):
        context['adminform'] = helpers.AdminForm(context['form'], [(None, {'fields': context['form'].base_fields})], {})
        context['title'] = _('Upload photos')
        context['app_label'] = PHOTO_MODEL._meta.app_config.verbose_name
        context['opts'] = PHOTO_MODEL._meta
        context['has_change_permission'] = 'photos.change_{}'.format(PHOTO_MODEL_NAME)
        context['has_permission'] = True
        return context

    def delete_queryset(self, request, queryset):
        for photo in queryset:
            photo.delete_all_files()
        super().delete_queryset(request, queryset)


class GalleryAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = ('__str__', 'random_photo_tag', 'count_photos')
    form = GalleryForm
    actions = ('delete_with_photos',)

    def get_queryset(self, request):
        return GALLERY_MODEL.objects.all().annotate(count_photos=Count('photos'))

    def count_photos(self, obj):
        return obj.count_photos

    count_photos.short_description = _('Photos')

    def get_urls(self):
        custom_urls = [
            path('delete-with-photos/', self._delete_with_photos, name='delete_with_photos'),
            path('upload-photo/', UploadPhotoAdminApiView.as_view(), name='image_upload')
        ]
        return custom_urls + super().get_urls()

    @staticmethod
    def gallery_admin_context(context):
        context['adminform'] = helpers.AdminForm(context['form'], [(None, {'fields': context['form'].base_fields})], {})
        context['title'] = _('Add photos to existing gallery')
        context['app_label'] = GALLERY_MODEL._meta.app_config.verbose_name
        context['opts'] = GALLERY_MODEL._meta
        context['has_change_permission'] = 'photos.change_{}'.format(PHOTO_MODEL_NAME)
        context['has_permission'] = True
        return context

    def _delete_with_photos(self, request):
        ids = [id for id in request.POST.getlist('id[]', [])]
        queryset = GALLERY_MODEL.objects.filter(id__in=ids)

        photos = PHOTO_MODEL.objects.filter(galleries__id__in=ids)
        try:
            get_photo_processor().delete_photos(photos)
        except PhotoProcessingError as e:
            messages.add_message(request, messages.ERROR, _(e.message))

        queryset.delete()

        for gallery in queryset:
            self.log_deletion(request, gallery, str(gallery))

        return HttpResponseRedirect('..')

    def delete_with_photos(self, request, queryset):
        opts = self.model._meta
        deletable_objects, model_count, perms_needed, protected = self.get_deleted_objects(queryset, request)

        objects_name = model_ngettext(queryset)

        title = _("Are you sure?")
        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": objects_name}
        context = {
            **self.admin_site.each_context(request),
            'title': title,
            'objects_name': str(objects_name),
            'deletable_objects': [deletable_objects],
            'model_count': dict(model_count).items(),
            'queryset': queryset,
            'perms_lacking': perms_needed,
            'protected': protected,
            'opts': opts,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            'media': self.media,
        }

        request.current_app = self.admin_site.name

        # Display the confirmation page
        return TemplateResponse(request, 'admin/photos/gallerymodel/delete_with_photos.html', context)

    delete_with_photos.short_description = _('Delete selected galleries and their photos')


admin.site.register(GALLERY_MODEL, GalleryAdmin)
admin.site.register(PHOTO_MODEL, PhotoAdmin)
