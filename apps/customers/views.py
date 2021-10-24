from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import TemplateView

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Card, ShippingAddress
from .serializers import CardSerializer, ShippingAddressSerializer
from .utils import stripe_get_card, stripe_delete_card


# Used to send Stripe Token to API
class StripeView(TemplateView):
	template_name = 'customers/stripe.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['pub_key'] = settings.STRIPE_PUBLISHABLE_KEY
		return context

	def post(self, *args, **kwargs):
		return redirect(self.request.path_info)


class CardView(ModelViewSet):
	queryset = Card.objects.all()
	serializer_class = CardSerializer

	def get_queryset(self):
		return self.queryset.filter(user=self.request.user)

	def retrieve(self, request, *args, **kwargs):
		instance = self.get_object()
		card = stripe_get_card(instance)
		return Response(card)

	def perform_destroy(self, instance):
		stripe_delete_card(instance)
		return super().perform_destroy(instance)


class ShippingAddressView(ModelViewSet):
	queryset = ShippingAddress.objects.all()
	serializer_class = ShippingAddressSerializer

	def get_queryset(self):
		return self.queryset.filter(user=self.request.user)