import djoser
import re

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from django_countries.serializer_fields import CountryField
from djoser import serializers as djoser_sz
from phonenumber_field.phonenumber import PhoneNumber
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from .models import *


# Utils
class TokenSerializer(serializers.Serializer):
	token = serializers.CharField()


class PasswordValidatorMixin(serializers.Serializer):
	def get_password(self, validated_data):
		password = validated_data.get('password')
		new_password = validated_data.get('new_password')

		if password:
			return password
		return new_password

	def validate(self, validated_data):
		error_list = []

		first_name = validated_data.get('first_name') or self.first_name
		last_name = validated_data.get('last_name') or self.last_name
		email = validated_data.get('email') or self.email

		email_name = email.split("@")[0]
		password = self.get_password(validated_data)

		if len(password) < 8:
			error_list.append("Password is not at least 8 characters")
		if not re.search("[a-zA-Z]", password):
			error_list.append("Password does not contain a letter")
		if not re.search("[0-9]", password):
			error_list.append("Password does not contain a number")
		if not re.search(r"[!#$%&'()*+,-./:;<=>?@[\]^_`{|}~]", password):
			error_list.append("Password does not contain a special character")

		if len(first_name) > 4 and first_name.lower() in password.lower():
			error_list.append("Password contains your first name")
		if len(last_name) > 4 and last_name.lower() in password.lower():
			error_list.append("Password contains your last name")
		if len(email_name) > 4 and email_name.lower() in password.lower():
			error_list.append("Password contains your email")

		if len(error_list) > 0:
			raise serializers.ValidationError(error_list)

		return super().validate(validated_data)


class PasswordSerializer(PasswordValidatorMixin, serializers.Serializer):
	new_password = serializers.CharField(write_only=True, style={"input_type": "password"})

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		request = self.context.get('request')
		if request:
			if request.method == "POST":
				self.first_name = request.user.first_name
				self.last_name = request.user.last_name
				self.email = request.user.email


class PasswordRetypeSerializer(PasswordSerializer, djoser_sz.PasswordRetypeSerializer):
	pass


# Create User
class UserCreateSerializer(PasswordValidatorMixin, djoser_sz.UserCreateSerializer):
	class Meta(djoser_sz.UserCreateSerializer.Meta):
		fields = ('id', 'first_name', 'last_name', 'email', 'username', 'password')
		extra_kwargs = {
			'username': {'read_only': True},
			'password': {'write_only': True},
		}

	def validate_email(self, value):
		if User.objects.filter(email__iexact=value.lower()).exists():
			raise serializers.ValidationError("A user with this email already exists")
		return value


class UserCreatePasswordRetypeSerializer(UserCreateSerializer, djoser_sz.UserCreatePasswordRetypeSerializer):
	pass


# Get User
class UserSerializer(djoser_sz.UserSerializer):
	class Meta(djoser_sz.UserSerializer.Meta):
		model = User
		fields = ('first_name', 'last_name', 'email', 'username')


# Change/Reset Password
class SetPasswordSerializer(PasswordSerializer, djoser_sz.CurrentPasswordSerializer):
	pass


class SetPasswordRetypeSerializer(PasswordRetypeSerializer, djoser_sz.CurrentPasswordSerializer):
	pass


class PasswordResetConfirmSerializer(djoser_sz.UidAndTokenSerializer, PasswordSerializer):
	pass


class PasswordResetConfirmRetypeSerializer(djoser_sz.UidAndTokenSerializer, PasswordRetypeSerializer):
	pass


# Twilio
ACCOUNT_SID = settings.ACCOUNT_SID
AUTH_TOKEN = settings.AUTH_TOKEN
TRIAL_NUMBER = settings.TRIAL_NUMBER


# Used in other apps
class PhoneSerializer(serializers.ModelSerializer):
	class Meta:
		model = Phone
		fields = ('phonenumber', 'service_sid', 'verified')


class AddPhonenumberSerializer(serializers.Serializer):
	NUMBER_ERROR = "Use only numbers. Please try again"

	user = serializers.HiddenField(default=serializers.CurrentUserDefault())
	country_code = CountryField(initial='US')
	area_code = serializers.CharField(max_length=5)
	number = serializers.CharField(max_length=15)

	def validate_area_code(self, value):
		if not re.match(r'^([\s\d]+)$', value):
			raise serializers.ValidationError(self.NUMBER_ERROR)
		return value

	def validate_number(self, value):
		if not re.match(r'^([\s\d]+)$', value):
			raise serializers.ValidationError(self.NUMBER_ERROR)
		return value

	def validate(self, validated_data):
		data = validated_data
		phonenumber = PhoneNumber.from_string(
			phone_number=f"{data['area_code']}{data['number']}", region=data['country_code']
		).as_e164

		try:
			client = Client(ACCOUNT_SID, AUTH_TOKEN)
			service = client.verify.services.create(friendly_name=data['user'].email)

			verification = client.verify \
			.services(service.sid) \
			.verifications \
			.create(to=str(phonenumber), channel='sms')

			self.phonenumber = phonenumber
			self.service_sid = service.sid
		except TwilioRestException as e:
			raise serializers.ValidationError(e)

		return validated_data

	def save(self):
		Phone.objects.update_or_create(
			user=self.validated_data['user'],
			defaults={
				'phonenumber': self.phonenumber,
				'service_sid': self.service_sid,
				'verified': False
			}
		)
		return {'details': f"Phonenumber: '{self.phonenumber}' added to account"}


class VerifyPhonenumberSerializer(serializers.Serializer):
	user = serializers.HiddenField(default=serializers.CurrentUserDefault())
	code = serializers.CharField(max_length=10)

	def validate(self, validated_data):
		data = validated_data
		self.phone = Phone.objects.get(user=data['user'])

		try:
			client = Client(ACCOUNT_SID, AUTH_TOKEN)

			verification_check = client.verify \
			.services(self.phone.service_sid) \
			.verification_checks \
			.create(to=str(self.phone.phonenumber), code=data['code'])
		
			if verification_check.status == 'approved':
				return validated_data
			raise serializers.ValidationError("There was an error. Please try again")

		except TwilioRestException as e:
			raise serializers.ValidationError(e)

	def save(self):
		Phone.objects.filter(user=self.validated_data['user']).update(verified=True)
		return {'details': f"Phonenumber: '{self.phone.phonenumber}' verified"}