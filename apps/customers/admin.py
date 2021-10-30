from django.contrib import admin

from .models import *
from common.mixins import NoAddDeleteMixin


# Inlines
class CustomerInline(NoAddDeleteMixin, admin.StackedInline):
	model = Customer

	fields = ['stripe_customer_id', 'purchase_attempt_time']
	if apps.is_installed('store'):
		fields.insert(3, 'price_level')
		fields.insert(4, 'payment_methods')

	readonly_fields = ('stripe_customer_id', 'purchase_attempt_time',)


class CardInline(admin.StackedInline):
	model = Card

	readonly_fields = ('src_id',)
	classes = ['collapse']
	extra = 0


class ShippingAddressInline(admin.StackedInline):
	model = ShippingAddress
	classes = ['collapse']
	extra = 0