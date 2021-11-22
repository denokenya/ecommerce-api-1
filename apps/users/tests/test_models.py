from django.test import TestCase
from django.utils import timezone

from model_bakery import baker


class ProfileModelTests(TestCase):
	def setUp(self):
		self.user = baker.make(
			'users.User',
			email='ken@email.com',
			is_superuser=True
		)
		self.profile = self.user.profile

	def test_profile_is_created_when_createsuperuser(self):
		self.assertIsNot(self.profile, None)

	def test_can_drink(self):
		self.profile.dob = timezone.now()-timezone.timedelta(days=21*365)
		self.profile.save()
		self.assertTrue(self.profile.can_drink())

	def test_cannot_drink(self):
		self.profile.dob = timezone.now()-timezone.timedelta(days=19*365)
		self.profile.save()
		self.assertFalse(self.profile.can_drink())