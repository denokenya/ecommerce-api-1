from django.urls import path, re_path
from . import views


urlpatterns = [
	re_path(r'^$', views.StoreItemBulkView.as_view()),
	path('inventory/', views.InventoryRecordBulkView.as_view()),

	path('user/', views.UserView.as_view()),
	re_path(r'^orders/$', views.OrderView.as_view()),
	path('cart/<int:pk>/', views.CartView.as_view()),
	path('checkout/', views.CheckoutView.as_view()),
]