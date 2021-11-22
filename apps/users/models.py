from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from common.fields import LowercaseEmailField


# Managers
class UserManager(BaseUserManager):
	use_in_migrations = True

	def _create_user(self, email, password, **extra_fields):
		if not email:
			raise ValueError('The given email must be set')
		
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email=None, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', False)
		extra_fields.setdefault('is_superuser', False)
		return self._create_user(email, password, **extra_fields)

	def create_superuser(self, email=None, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('Superuser must have is_staff=True.')
		if extra_fields.get('is_superuser') is not True:
			raise ValueError('Superuser must have is_superuser=True.')

		return self._create_user(email, password, **extra_fields)


# Models
class User(AbstractUser):
	first_name = models.CharField(max_length=30)
	last_name = models.CharField(max_length=30)
	email = LowercaseEmailField('email address', unique=True)
	last_login_attempt = models.DateTimeField(blank=True, null=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	objects = UserManager()

	def __str__(self):
		return f"{self.first_name} {self.last_name}"


class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	dob = models.DateField()
	image = models.ImageField(upload_to='users/profile/image', blank=True, null=True)

	def can_drink(self):
		age = (timezone.now()-self.dob).days / 365
		return age >= 21


# Signals
@receiver(post_save, sender='users.User', dispatch_uid="user_created")
def user_created(sender, instance, created, *args, **kwargs):
	if created and instance.is_superuser:
		Profile.objects.get_or_create(user=instance, dob=timezone.now())