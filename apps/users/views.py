from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from djoser.views import UserViewSet as DJoserUserViewSet

from common.views import GenericAPISerializerView
from users.models import User
from .serializers import AddPhonenumberSerializer, TokenSerializer, VerifyPhonenumberSerializer


class UserViewSet(DJoserUserViewSet):
	@action(["post"], detail=False)
	def reset_password_confirm(self, request, *args, **kwargs):
		serializer = TokenSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		token = request.data['token']
		
		obj = PasswordResetTokenGenerator()
		for user in User.objects.all():
			user_found = obj.check_token(user, token)
			if user_found:
				break
			user = None

		if user:
			return super().reset_password_confirm(request, *args, **kwargs)

		return Response(
			{"token": ["Invalid token for given user."]},
			status=status.HTTP_400_BAD_REQUEST
		)


class AddPhonenumberView(GenericAPISerializerView):
	serializer_class = AddPhonenumberSerializer
	http_method_names = ['post']


class VerifyPhonenumberView(GenericAPISerializerView):
	serializer_class = VerifyPhonenumberSerializer
	http_method_names = ['post']