# LAV

import re
import datetime
import djoser

from django.contrib.auth.models import User
from rest_framework import serializers

from djoser import serializers as djoser_sz

from .models import Profile, User


# Mixins
class ValidatorSerializerMixin(serializers.Serializer):
	def get_password(self, validated_data):
		password = validated_data.get('password')
		new_password = validated_data.get('new_password')
		return password if password else new_password

	def validate(self, validated_data):
		error_list = []

		email = validated_data.get('email') or self.email
		email_name = email.split("@")[0]
		password = self.get_password(validated_data)

		if len(password) < 8:
			error_list.append("Password is not at least 8 characters.")
		if not re.search("[a-zA-Z]", password):
			error_list.append("Password does not contain a letter.")
		if not re.search("[0-9]", password):
			error_list.append("Password does not contain a number.")
		if not re.search(r"[!#$%&'()*+,-./:;<=>?@[\]^_`{|}~]", password):
			error_list.append("Password does not contain a special character.")

		if len(email_name) > 4 and email_name.lower() in password.lower():
			error_list.append("Password contains your email.")

		if len(error_list) > 0:
			raise serializers.ValidationError( {'password': error_list} )

		return super().validate(validated_data)


class PasswordSerializerMixin(ValidatorSerializerMixin, djoser_sz.PasswordSerializer):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.email = self.context['request'].user.email


class PasswordRetypeSerializerMixin(PasswordSerializerMixin, djoser_sz.PasswordRetypeSerializer):
	pass


# Serializers

# Create User w/ Profile
class CurrentProfileSerializer(serializers.ModelSerializer):
	class Meta:
		model = Profile
		fields = ('image', 'dob')

	def validate_dob(self, value):
		years = (datetime.datetime.now().date() - value).days / 365
		if years < 19:
			raise serializers.ValidationError("You must be 19 years or older to use this product.")
		return value

	def save(self, user, **kwargs):
		if self.instance is None:
			self.validated_data['user'] = user
		return super().save(**kwargs)


class UserCreateSerializer(ValidatorSerializerMixin, djoser_sz.UserCreateSerializer):
	profile = CurrentProfileSerializer(read_only=True)

	class Meta(djoser_sz.UserCreateSerializer.Meta):
		fields = ('id', 'first_name', 'last_name', 'email', 'username', 'password', 'profile',)
		extra_kwargs = { 'password': {'write_only': True} }

	def validate_email(self, value):
		if User.objects.filter(email__iexact=value.lower()).exists():
			raise serializers.ValidationError("A user with this email already exists.")
		return value

	def to_representation(self, instance):
		return super().to_representation(instance) if not self.context['request'].data.get('validate') else {}


class UserCreatePasswordRetypeSerializer(UserCreateSerializer, djoser_sz.UserCreatePasswordRetypeSerializer):
	pass


# Get/Patch Current User
class CurrentUserSerializer(djoser_sz.UserSerializer):
	profile = CurrentProfileSerializer(read_only=True)
	image = serializers.ImageField(required=False, write_only=True)

	class Meta(djoser_sz.UserSerializer.Meta):
		model = User
		fields = ('id', 'first_name', 'last_name', 'email', 'username', 'profile', 'image')

	def update(self, instance, validated_data):
		image = validated_data.pop('image', None)
		if image:
			instance.profile.image = image
			instance.profile.save()
		return super().update(instance, validated_data)


# Change Password
class SetPasswordSerializer(PasswordSerializerMixin, djoser_sz.CurrentPasswordSerializer):
	pass


class SetPasswordRetypeSerializer(PasswordRetypeSerializerMixin, djoser_sz.CurrentPasswordSerializer):
	pass


# Reset Password
class PasswordResetConfirmSerializer(djoser_sz.UidAndTokenSerializer, PasswordSerializerMixin):
	pass


class PasswordResetConfirmRetypeSerializer(djoser_sz.UidAndTokenSerializer, PasswordRetypeSerializerMixin):
	pass


# Get all Users (limited data)
class PublicProfileSerializer(serializers.ModelSerializer):
	class Meta:
		model = Profile
		fields = ('image',)


class PublicUserSerializer(serializers.ModelSerializer):
	profile = PublicProfileSerializer(read_only=True)

	class Meta:
		model = User
		fields = ('id', 'username', 'profile')