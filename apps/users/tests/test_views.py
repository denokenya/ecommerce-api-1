from django.test import TestCase
from rest_framework import status

from users.models import User
from .utils import getValidUserData


class UserViewSetTests(TestCase):
	def test_create_user(self):
		data = getValidUserData()
		data.update( {'validate':False} )
		response = self.client.post(
			'/auth/users/',
			data=data,
			content_type='application/json'
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(User.objects.all().count(), 1)

	def test_validate_user_data(self):
		response = self.client.post(
			'/auth/users/',
			data=getValidUserData(),
			content_type='application/json'
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data, {})