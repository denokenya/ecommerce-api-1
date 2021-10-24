from collections import OrderedDict
from django.contrib import admin
from .models import *


# Inlines

class CustomerInline(admin.StackedInline):
	model = Customer
	extra = 0

	fields = ('price_level', 'stripe_customer_id', 'purchase_attempt_time', 'payment_methods',)
	readonly_fields = ('stripe_customer_id', 'purchase_attempt_time',)

	classes = ['collapse']

class CardInline(admin.StackedInline):
	model = Card
	extra = 0

	readonly_fields = ('src_id',)
	classes = ['collapse']


class ShippingAddressInline(admin.StackedInline):
	model = ShippingAddress
	extra = 0

	classes = ['collapse'] 