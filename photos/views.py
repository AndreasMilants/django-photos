from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import generic, View
from .forms import UploadPhotosToNewGalleryForm
from .models import PHOTO_MODEL, GALLERY_MODEL
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.utils.translation import ugettext_lazy as _
from .mixins import StaffRequiredMixin
from photos.photo_processors.base_processor import get_photo_processor, PhotoProcessingError

PHOTO_APP_LABEL = PHOTO_MODEL._meta.app_label
GALLERY_APP_LABEL = GALLERY_MODEL._meta.app_label

PHOTO_MODEL_NAME = PHOTO_MODEL._meta.model_name
GALLERY_MODEL_NAME = GALLERY_MODEL._meta.model_name

CREATE_PHOTO_PERMISSION_NAME = '{}.add_{}'.format(PHOTO_APP_LABEL, PHOTO_MODEL_NAME)
CREATE_GALLERY_PERMISSION_NAME = '{}.add_{}'.format(GALLERY_APP_LABEL, GALLERY_MODEL_NAME)


class UploadPhotosView(generic.CreateView):
    form_class = UploadPhotosToNewGalleryForm
    template_name = 'photos/gallerymodel_create.html'
    success_url = reverse_lazy('gallery_create')
    success_object_url = None

    def get_succes_object_url(self):
        return self.success_object_url.format(**self.object.__dict__)

    def get_success_url(self):
        if self.object is not None:
            if self.success_object_url is not None:
                return self.get_succes_object_url()
            elif self.success_url is not None:
                return self.success_url.format(**self.object.__dict__)
            else:
                try:
                    return self.object.get_absolute_url()
                except AttributeError:
                    pass
        elif self.success_url is not None:
            return self.success_url

        raise ImproperlyConfigured(
            "No URL to redirect to.  Either provide a url or define"
            " a get_absolute_url method on the GalleryModel.")


class UploadPhotosWithPermissionView(LoginRequiredMixin, PermissionRequiredMixin, UploadPhotosView):
    permission_required = (CREATE_PHOTO_PERMISSION_NAME, CREATE_GALLERY_PERMISSION_NAME)


class UploadPhotoApiView(View):
    def post(self, request, *args, **kwargs):
        try:
            file = request.FILES.get('file')
            upload_id = request.POST.get('upload_id')
            get_photo_processor().handle_file(file, upload_id)
            return HttpResponse(status=201)
        except PhotoProcessingError as e:
            return HttpResponse(_(e.message), status=500)
        except Exception as e:
            return HttpResponse(_('Something unexpected happened while processing the file'), status=500)


class UploadPhotoWithPermissionApiView(LoginRequiredMixin, PermissionRequiredMixin, UploadPhotoApiView):
    permission_required = (CREATE_PHOTO_PERMISSION_NAME,)


class UploadPhotoAdminApiView(UploadPhotoWithPermissionApiView, StaffRequiredMixin):
    pass


class GalleryListView(generic.ListView):
    model = GALLERY_MODEL
    context_object_name = 'gallery_list'


class GalleryPhotosView(generic.ListView):
    model = PHOTO_MODEL
    context_object_name = 'photo_list'

    def get_queryset(self):
        return PHOTO_MODEL.objects.filter(galleries__slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['gallery'] = GALLERY_MODEL.objects.get(slug=self.kwargs['slug'])
        return context
