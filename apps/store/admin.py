from django.contrib import admin, messages
from django import forms

from collections import OrderedDict
from rangefilter.filter import DateRangeFilter

from common.mixins import NoAddDeleteMixin, NoChangeDeleteMixin
from store.models import *


# Actions

def make_active(modeladmin, request, queryset):
	queryset.update(is_active=True)
make_active.short_description = "Mark selected items as active"


def make_inactive(modeladmin, request, queryset):
	queryset.update(is_active=False)
make_inactive.short_description = "Mark selected items as inactive"


def cancel(modeladmin, request, queryset):
	queryset.update(cancelled=True)
cancel.short_description = "Mark selected orders as cancelled"


def uncancel(modeladmin, request, queryset):
	queryset.update(cancelled=False)
uncancel.short_description = "Mark selected orders as not cancelled"



# Admin
class StoreItemInline(NoChangeDeleteMixin, admin.TabularInline):
	model = StoreItem
	extra = 0

	fields = ('location', 'quantity',)
	readonly_fields = ('quantity',)
	classes = ['collapse']


class InventoryRecordAdmin(admin.ModelAdmin):
	fields = ('option', 'store_item', 'date', 'quantity', 'info',)
	list_display = ('store_item', 'option', 'quantity', 'date',)
	list_filter = ('option',)


class PriceInline(NoAddDeleteMixin, admin.TabularInline):
	model = Price
	extra = 0
	per_page = 300

	fields = ('level', 'item', 'price',)
	readonly_fields = ('level', 'item',)



class PriceTypeAdmin(NoAddDeleteMixin, admin.ModelAdmin):
	inlines = [PriceInline,]
	fields = ('price_level_link',)
	readonly_fields = ('price_level_link',)

	def get_model_perms(self, request):
		return {}

class PriceTypeInline(NoAddDeleteMixin, admin.TabularInline):
	model = PriceType
	fields = ['price_type_link',]
	readonly_fields = ['price_type_link',]
	extra = 0


class PriceLevelAdmin(NoAddDeleteMixin, admin.ModelAdmin):
	inlines = [PriceTypeInline,]
	list_display = ['name', 'default']


class CustomPriceInline(admin.TabularInline):
	model = CustomPrice
	extra = 0

	fields = ('item', 'price',)


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0

	verbose_name = 'Order Item'
	fields = ['store_item', 'price', 'quantity', 'total', 'shipping_address']
	readonly_fields = ['price', 'total', 'shipping_address']


class OrderAdmin(admin.ModelAdmin):
	inlines = (OrderItemInline,)
	fieldsets = [
		( ('Info'), {'fields': ('user', 'number',),} ),
		( ('Payments'), {'fields': ('subtotal', 'tax', 'shipping_total', 'grand_total', 'amt_refunded', 'amt_charged',), 'classes': ('',),} ),
		( ('Dates'), {'fields': ('date_ordered', 'date_paid', 'date_recieved', 'date_cancelled',), 'classes': ('collapse',),} ),
		( ('Extra'), {'fields': ('notes',), 'classes': ('collapse',),} ),
	]

	readonly_fields = [
		'number',
		'card',
		'payment_intent_id',
		'subtotal',
		'tax',
		'payment_method',
		'shipping_total',
		'grand_total',
		'date_ordered',
		'date_paid',
		'date_recieved',
		'date_cancelled',
		'amt_refunded',
		'amt_charged',
	]
	list_display = [
		'user',
		'number', 
		'grand_total',
		'date_ordered',
	]
	list_filter = [
		['date_ordered', DateRangeFilter],
		'payment_method'
	]
	search_fields = ['payment_intent_id', 'number', 'orderitem__item__name']
	actions = [cancel, uncancel]


admin.site.register(Location)
admin.site.register(PostOffice)

admin.site.register(InventoryRecord, InventoryRecordAdmin)
admin.site.register(PriceLevel, PriceLevelAdmin)
admin.site.register(PriceType, PriceTypeAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(PaymentMethod)