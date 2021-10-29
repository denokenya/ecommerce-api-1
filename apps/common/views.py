from django.apps import apps

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.settings import api_settings

from .serializers import BulkSerializer


class GenericAPISerializerView(GenericAPIView):
	def handle_response(self, request, many=False):
		serializer = self.get_serializer(data=request.data, many=many)
		serializer.is_valid(raise_exception=True)
		result = serializer.save()
		return Response(result)

	def post(self, request, format=None):
		return self.handle_response(request)

	def put(self, request, format=None):
		return self.handle_response(request)

	def patch(self, request, format=None):
		return self.handle_response(request)


class BulkAPIView(ListCreateAPIView):
	app_label = None
	model_name = None
	queryset = None
	serializer_class = None

	def setup(self, request, *args, **kwargs):
		super().setup(request, *args, **kwargs)
		self.model = apps.get_model(app_label=self.app_label, model_name=self.model_name)

	def get_delete_ids(self):
		serializer = BulkSerializer(data={'data': self.request.data})
		serializer.is_valid(raise_exception=True)
		return serializer.get_delete_ids()

	def get_update_ids(self):
		serializer = BulkSerializer(data={'data': self.request.data})
		serializer.is_valid(raise_exception=True)
		return serializer.get_update_ids()

	def handle_update(self, request, *args, **kwargs):
		id_list = self.get_update_ids()
		qs = self.model.objects.filter(pk__in=id_list)
		for obj in qs:
			serializer = self.get_serializer(instance=obj, data=id_list[obj.id])
			serializer.is_valid(raise_exception=True)
			serializer.save()

		return Response(self.get_serializer(qs, many=True).data)

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data, many=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

	def patch(self, request, *args, **kwargs):
		return self.handle_update(request, *args, **kwargs)

	def put(self, request, *args, **kwargs):
		return self.handle_update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
		id_list = self.get_delete_ids()
		qs = self.model.objects.filter(id__in=id_list)
		count = qs.count()
		qs.delete()
		result = {'count': f'{count} {self.model_name} instance(s) have been deleted.'}
		return Response(result)