from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

from common.mixins import NoChangeDeleteMixin
from .models import Phone, User


# Inlines
class PhoneInline(NoChangeDeleteMixin, admin.TabularInline):
	model = Phone
	extra = 0


# Admins
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	inlines = [PhoneInline]
	if apps.is_installed('customers'):
		from customers.admin import CustomerInline, CardInline
		inlines += [CustomerInline, CardInline]

	fieldsets = (
		(_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'is_active', 'is_staff')}),
		(_('Login dates'), {'fields': ('last_login_attempt', 'last_login', 'date_joined'), 'classes': ('collapse',)}),
	)

	list_display = ('email', 'first_name', 'last_name', 'is_active',)
	list_filter = ('is_staff',)
	search_fields = ('email', 'first_name', 'last_name')
	ordering = ('email',)

	def get_inlines(self, request, obj=None):
		inlines = list(set(self.inlines))
		if apps.is_installed('events'):
			from events.admin import HostInline, AttendeeInline
			from events.models import Host

			inlines.insert(0, AttendeeInline)

			if Host.objects.filter(user=obj):
				inlines.insert(0, HostInline)

		return inlines


admin.site.unregister(Group)