from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('django-admin/', admin.site.urls),   # renamed to avoid conflict with api/portal/
    path('api/', include('api.urls')),
]