from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),

    path('catalog/', include('catalog.urls')),
    path('customers/', include('customers.urls')),
    path('store/', include('store.urls')),
]