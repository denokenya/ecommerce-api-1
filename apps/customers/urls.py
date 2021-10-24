from django.urls import include, path
from rest_framework import routers

from . import views


app_name = 'customers'

router = routers.DefaultRouter()
router.register('address', views.ShippingAddressView)
router.register('cards', views.CardView, basename='cards')

urlpatterns = [
	path('', include(router.urls)),
	path('stripe/', views.StripeView.as_view())
] 