======
Photos
======

Photos is a Django app, made for creating galleries.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "photos" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'polls',
    ]

2. Run ``python manage.py makemigrations photos`` and ``python manage.py migrate`` to create the models.

3. Include the photos URLconf in your project urls.py like this::

    path('photos/', include('photos.urls')),

4. Start the development server and visit
    http://127.0.0.1:8000/photos/ or http://127.0.0.1:8000/admin/
