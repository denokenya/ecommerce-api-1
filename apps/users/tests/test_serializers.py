from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from model_bakery import baker

from users.models import User
from users.serializers import (
	AGE_LIMIT,
	CreateGetProfileSerializer,
	CurrentUserSerializer,
	UserCreateSerializer
)
from .utils import getValidUserData


class UserSerializerTests(TestCase):
	def get_dob(self, age_limit):
		return (timezone.now()-timezone.timedelta(days=age_limit*365)).strftime('%Y-%m-%d')

	def test_create_user(self):
		serializer = UserCreateSerializer(data=getValidUserData())
		self.assertTrue(serializer.is_valid())

		user = serializer.save()
		self.assertEqual(User.objects.all().count(), 1)
		self.assertNotEqual(user.profile, None)

	def test_update_user(self):
		factory = APIRequestFactory()
		old_dob = self.get_dob(AGE_LIMIT)
		new_dob = self.get_dob(AGE_LIMIT+1)

		profile = baker.make('users.Profile', dob=old_dob, user__email='blanka@email.com')
		request = factory.patch('')

		data = {
			'first_name': 'Oro',
			'last_name': 'Sean',
			'username': 'balrog',
			'profile': {
				'dob': new_dob
			}
		}
		serializer = CurrentUserSerializer(
			context={'request': request},
			instance=profile.user,
			data=data,
			partial=True
		)
		serializer.is_valid()
		self.assertTrue(serializer.is_valid())

		updated_user = serializer.save()
		self.assertEqual(updated_user.first_name, data['first_name'])
		self.assertEqual(updated_user.last_name, data['last_name'])
		self.assertEqual(updated_user.username, data['username'])
		self.assertEqual(updated_user.profile.dob, old_dob)  # dob isn't supposed to change

	def test_invalid_password_length_number_symbol_email(self):
		data = getValidUserData()
		data.update({'password': 'blanka'})
		serializer = UserCreateSerializer(data=data)
		self.assertFalse(serializer.is_valid())
		self.assertEqual(len(serializer.errors['password']), 4)

	def test_invalid_password_letter(self):
		data = getValidUserData()
		data.update({'password': '102938!@'})
		serializer = UserCreateSerializer(data=data)
		self.assertFalse(serializer.is_valid())
		self.assertEqual(len(serializer.errors['password']), 1)

	def test_invalid_dob(self):
		data = {'dob': self.get_dob(AGE_LIMIT-1)}
		serializer = CreateGetProfileSerializer(data=data)
		self.assertFalse(serializer.is_valid())
		self.assertEqual(len(serializer.errors['dob']), 1)