from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from common.fields import LowercaseEmailField


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

	def set_username(self):
		username = self.email.split('@')[0]
		number = User.objects.filter(username__iexact=username).count()
		self.username = f"{username}{number}"

	def save(self, *args, **kwargs):
		if not self.pk:
			self.set_username()
		super().save(*args, **kwargs)


class Phone(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)

	phonenumber = PhoneNumberField("Phone Number", null=True, blank=True, unique=True)
	service_sid = models.CharField("Twilio Service SID", max_length=50, null=True, blank=True)
	verified = models.BooleanField(default=False)