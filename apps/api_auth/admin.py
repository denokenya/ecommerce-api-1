from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import User
if apps.is_installed('customers'):
	from customers.admin import CustomerInline, CardInline, ShippingAddressInline

	if apps.is_installed('store'):
		from store.admin import CustomPriceInline


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	if apps.is_installed('customers'):
		inlines = [CustomerInline, CardInline, ShippingAddressInline,]

		if apps.is_installed('store'):
			inlines.append(CustomPriceInline)

	fieldsets = (
		(_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'is_active', 'is_staff')}),
		(_('Important dates'), {'fields': ('last_login_attempt', 'last_login', 'date_joined'), 'classes': ('collapse',)}),
	)

	list_display = ('email', 'first_name', 'last_name', 'is_active',)
	list_filter = ('is_staff',)
	search_fields = ('email', 'first_name', 'last_name')
	ordering = ('email',)


admin.site.unregister(Group)