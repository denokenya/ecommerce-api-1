from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from djoser.compat import get_user_email
from djoser.conf import settings
from djoser.views import UserViewSet as DJoserUserViewSet


class UserViewSet(DJoserUserViewSet):
	def create(self, request, *args, **kwargs):
		if not self.request.data.get('validate'):
			return super().create(request, *args, **kwargs)

		serializer = self.get_serializer(data=self.request.data)
		serializer.is_valid(raise_exception=True)
		return Response({}, status=status.HTTP_200_OK)

	@action(["post"], detail=False)
	def set_password(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		if not self.request.data.get('validate'):
			self.request.user.set_password(serializer.data["new_password"])
			self.request.user.save()

			if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
				context = {"user": self.request.user}
				to = [get_user_email(self.request.user)]
				settings.EMAIL.password_changed_confirmation(self.request, context).send(to)

			if settings.LOGOUT_ON_PASSWORD_CHANGE:
				utils.logout_user(self.request)
			elif settings.CREATE_SESSION_ON_LOGIN:
				update_session_auth_hash(self.request, self.request.user)
		return Response(status=status.HTTP_204_NO_CONTENT)

	@action(["post"], detail=False)
	def reset_password_confirm(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		if not self.request.data.get('validate'):
			serializer.user.set_password(serializer.data["new_password"])
			if hasattr(serializer.user, "last_login"):
				serializer.user.last_login = timezone.now()
			serializer.user.save()

			if settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION:
				context = {"user": serializer.user}
				to = [get_user_email(serializer.user)]
				settings.EMAIL.password_changed_confirmation(self.request, context).send(to)
		return Response(status=status.HTTP_204_NO_CONTENT)

	@action(["get", "patch"], detail=False)
	def me(self, request, *args, **kwargs):
		return super().me(request, *args, **kwargs)