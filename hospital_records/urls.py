from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('hospital_records.apps.accounts.urls')),
    path('', include('hospital_records.apps.patients.urls')),
    path('records/', include('hospital_records.apps.records.urls')),
    path('reports/', include('hospital_records.apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)