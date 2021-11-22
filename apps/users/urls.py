from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views

from . import views


router = DefaultRouter()
router.register('', views.UserViewSet)

urlpatterns = [
    path('', include('djoser.urls.jwt')),
    path('users/', include(router.urls)),

	path('jwt/create/', jwt_views.TokenObtainPairView.as_view()),
	path('jwt/refresh/', jwt_views.TokenRefreshView.as_view()),
	path('jwt/verify/', jwt_views.TokenVerifyView.as_view()),
]