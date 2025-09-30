
from django.contrib import admin
from django.urls import path ,include
from django.conf.urls.static import static

from HubEducator import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('teacherDash/', include('TeacherDash.urls')),
    path('core/', include('core.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)