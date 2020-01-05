from lists import views
from lists import urls

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(r'', views.home_page, name='home'),
    path(r'lists/', include(urls)),
    path('admin/', admin.site.urls),
]
