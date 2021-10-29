from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

	path('phone/add/', views.AddPhonenumberView.as_view()),
	path('phone/verify/', views.VerifyPhonenumberView.as_view()),
]