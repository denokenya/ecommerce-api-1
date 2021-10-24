from django.apps import apps
from django.contrib import admin

from catalog.models import *
from common.mixins import RefreshSaveChange

if apps.is_installed('store'):
	from store.admin import PriceInline, StoreItemInline


class ItemTypeAdmin(admin.ModelAdmin):
	fields = ('name', 'is_active',)

	def get_model_perms(self, request):
		return {}


class ItemCategoryAdmin(admin.ModelAdmin):
	fields = ('name', 'is_active',)

	def get_model_perms(self, request):
		return {}


class ImageInline(admin.TabularInline):
	model = Image
	fields = ('name', 'image', 'number',)
	readonly_fields = ('number',)
	extra = 0

	classes = ['collapse']


class ItemAdmin(RefreshSaveChange, admin.ModelAdmin):
	fields = ('item_type', 'item_category', 'name', 'description', 'parcel', 'number', 'is_active',)
	readonly_fields = ('number',)
	list_display = ('name', 'item_type', 'item_category', 'is_active')
	list_filter = ('item_type', 'item_category',)

	inlines = [ImageInline,]
	if apps.is_installed('customers'):
		inlines.append(StoreItemInline)
		inlines.append(PriceInline)


class ParcelAdmin(admin.ModelAdmin):
	def get_model_perms(self, request):
		return {}	


admin.site.register(ItemType, ItemTypeAdmin)
admin.site.register(ItemCategory, ItemCategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Parcel, ParcelAdmin)