from django.apps import apps
from rest_framework import serializers
from .models import *


class ParcelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Parcel
		fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
	item_type = serializers.CharField()
	item_category = serializers.CharField()
	parcel = ParcelSerializer()

	class Meta:
		model = Item
		fields = ['id', 'item_type', 'item_category', 'name', 'slug', 'description', 'number', 'is_active', 'parcel']

		depth = 1
		extra_kwargs = {
			'description': {'required': False},
			'is_active': {'required': False},
			'number': {'read_only': True},
			'slug': {'read_only': True},
		}

	def validate_item_type(self, value):
		return ItemType.objects.get_or_create(name=value)[0]

	def validate_item_category(self, value):
		return ItemCategory.objects.get_or_create(name=value)[0]

	def validate_parcel(self, value):
		value = dict(value)
		parcel = Parcel.objects.get_or_create(
			length=value['length'],
			width=value['width'],
			height=value['height'],
			weight=value['weight']
		)[0]
		return parcel