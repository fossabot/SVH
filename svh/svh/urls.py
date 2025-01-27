from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from svh.views import index, play_video, page_from, page_by_type

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', index),
    url(r'^videos/(\d+)/$', play_video, name='play_video'),
    url(r'(\d+)/$', page_from, name='page'),
    url(r'^types/([\w\-]+)/$', page_by_type, name='by_type')
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)