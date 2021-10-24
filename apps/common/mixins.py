from django.shortcuts import redirect
from .utils import hide_admin_btns

# Admin
class NoAddMixin:
	def has_add_permission(self, request, obj=None):
		return False


class NoDeleteMixin:
	def has_delete_permission(self, request, obj=None):
		return False


class NoChangeDeleteMixin(NoDeleteMixin):
	def has_change_permission(self, request, obj=None):
		return False


class NoAddDeleteMixin(NoDeleteMixin):
	def has_add_permission(self, request, obj=None):
		return False


class NoAddChangeDeleteMixin(NoAddDeleteMixin):
	def has_change_permission(self, request, obj=None):
		return False


class RefreshSaveChange:
	def response_change(self, request, obj):
		return redirect(request.path_info)

	def change_view(self, request, object_id, extra_context={}):
		extra_context = hide_admin_btns(extra_context, show_save=False, show_save_add=True, close=False)
		return super().change_view(request, object_id, extra_context=extra_context)
