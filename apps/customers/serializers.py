import stripe

from rest_framework import serializers

from users.models import User
from .models import Customer, Card, ShippingAddress
from .utils import stripe_check_card, stripe_get_customer


class CardSerializer(serializers.ModelSerializer):
	stripe_src = serializers.CharField(write_only=True)

	class Meta:
		model = Card
		exclude = ('user',)
		extra_kwargs = { 'src_id': {'read_only': True} }

	def update_data(self, data):
		self.src_id = self.instance.src_id
		for k in self.instance.__dict__:
			if data.get(k) is None:
				data[k] = getattr(self.instance, k)
		return data

	def validate(self, validated_data):
		self.user = self.context['request'].user
		data = validated_data		

		try:
			stripe_get_customer(self.user)

			if self.instance is None:
				if stripe_check_card(self.user, data['stripe_src']):
					raise serializers.ValidationError("A card with this number and date already exists on your account.")

				self.src_id = stripe.Customer.create_source(
					self.user.customer.stripe_customer_id,
					source=data['stripe_src']
				).id
			else:
				data = self.update_data(data)
				
			stripe.Customer.modify_source(
				self.user.customer.stripe_customer_id,
				self.src_id,
				owner={
					'name': f"{data['first_name']}, {data['last_name']}",
					'email': data['email'],
					'address': {
						'line1': data['line1'],
						'line2': data['line2'],
						'city': data['city'],
						'state': data['state'],
						'postal_code': data['zipcode'],
						'country': data['country'],
					}
				}
			)
		except stripe.error.StripeError as e:
			raise serializers.ValidationError(e)

		return validated_data

	def save(self, **kwargs):
		if self.instance is None:
			self.validated_data.pop('stripe_src')
			self.validated_data['src_id'] = self.src_id
			self.validated_data['user'] = self.user

		return super().save(**kwargs)


class ShippingAddressSerializer(serializers.ModelSerializer):
	class Meta:
		model = ShippingAddress
		exclude = ('user',)

	def save(self, **kwargs):
		self.validated_data['user'] = self.context['request'].user
		return super().save(**kwargs)