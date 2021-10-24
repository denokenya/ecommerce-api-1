from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from api_auth.models import User
from common.views import BulkAPIView
from customers.models import Card
from .filters import filter_store_items
from .models import *
from .serializers import *


class UserView(APIView):
	http_method_names = ['get']

	def get(self, request, *args, **kwargs):
		serializer = ExtendedUserSerializer(instance=request.user)
		return Response(serializer.data)


class StoreItemBulkView(BulkAPIView):
	app_label = 'store'
	model_name = 'StoreItem'

	queryset = StoreItem.objects.all()
	serializer_class = StoreItemSerializer
	http_method_names = ['get', 'post', 'delete']

	def get_queryset(self):
		qs = super().get_queryset()
		return filter_store_items(qs, self.request.GET)
		

class InventoryRecordBulkView(BulkAPIView):
	app_label = 'store'
	model_name = 'InventoryRecord'

	queryset = InventoryRecord.objects.all()
	serializer_class = InventoryRecordSerializer
	http_method_names = ['post']


class OrderView(APIView):
	def get(self, request, *args, **kwargs):
		date = request.GET.get('date')
		user = request.user
		many, qs = True, {}

		qs = Order.objects.filter(user=user)
		if date == 'past':
			qs = Order.objects.past(user=user)

		elif date == 'cancelled':
			qs = Order.objects.cancelled(user=user)

		result = OrderSerializer(qs, many=many).data
		return Response(result)


class CartView(APIView):
	def get_object(self):
		pk = int(self.kwargs.get('pk'))
		obj = get_object_or_404(StoreItem, pk=pk)
		return obj

	def post(self, request, *args, **kwargs):
		store_item = self.get_object()
		order = Order.objects.get_or_create_active(user=request.user)[0]
		order_item = OrderItem.objects.get_or_create(order=order, store_item=store_item)[0]

		serializer = CartSerializer(instance=order_item, data=request.data)
		serializer.is_valid(raise_exception=True)			
		order_item = serializer.update()
		result = OrderItemSerializer(order_item).data

		return Response(result)


class CheckoutView(APIView):
	def get(self, request, *args, **kwargs):
		order = Order.objects.get_or_create_active(user=request.user)[0]
		result = OrderSerializer(instance=order).data
		return Response(result)

	def post(self, request, *args, **kwargs):
		serializer = CheckoutSerializer(context={'request': request}, data=request.data)
		serializer.is_valid(raise_exception=True)
		result = OrderSerializer(instance=serializer.save()).data
		return Response(result)