from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from happygreen_backend import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),  # <-- questa riga importa le rotte del router da core/urls.py
    path('', include('core.urls'))
]
# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)