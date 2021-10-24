from rest_framework.permissions import BasePermission


class AlwaysDeny(BasePermission):
	def has_permission(self, request, view):
		return False