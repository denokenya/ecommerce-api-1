# LAV

from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import Profile, User
from common.mixins import NoAddChangeDeleteMixin


# Inlines
class ProfileInline(NoAddChangeDeleteMixin, admin.StackedInline):
	model = Profile
	verbose_name = 'Profile'
	classes = ('no-upper',)
	extra = 0

	class Media:
		css = { 'all': ('common/css/admin.css',) }


# Admins
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	fieldsets = (
		(_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'username', 'is_active', 'is_staff')}),
		(_('Login dates'), {'fields': ('last_login_attempt', 'last_login', 'date_joined'), 'classes': ('collapse',)}),
	)

	list_display = ('email', 'username', 'first_name', 'last_name', 'is_active',)
	list_filter = ('is_staff',)
	search_fields = ('email', 'username', 'first_name', 'last_name')
	ordering = ('email',)

	def get_inlines(self, request, obj):
		inlines = list(set(self.inlines))
		if Profile.objects.filter(user=obj):
			inlines.append(ProfileInline)
		return inlines


admin.site.unregister(Group)