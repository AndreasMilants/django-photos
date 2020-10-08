from django.urls import path
from .views import UploadPhotosView, UploadPhotoApiView, GalleryPhotosView, GalleryListView

urlpatterns = [
    path('create/', UploadPhotosView.as_view(), name='gallery_create'),
    path('upload/', UploadPhotoApiView.as_view(), name='image_upload'),
    path('', GalleryListView.as_view(), name='gallery-list'),
    path('<slug:slug>/', GalleryPhotosView.as_view(), name='gallery-detail'),
]
