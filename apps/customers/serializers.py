import stripe

from rest_framework import serializers

from api_auth.models import User
from .models import Customer, Card, ShippingAddress
from .utils import stripe_check_card, stripe_get_customer


class CardSerializer(serializers.ModelSerializer):
	user = serializers.HiddenField(default=serializers.CurrentUserDefault())
	stripe_src = serializers.CharField(write_only=True)

	class Meta:
		model = Card
		fields = '__all__'

	def update_data(self, data):
		self.src_id = self.instance.src_id
		for k in self.instance.__dict__:
			if data.get(k) is None:
				data[k] = getattr(self.instance, k)
		return data

	def validate(self, validated_data):
		data = validated_data		

		try:
			stripe_get_customer(data['user'])
			if stripe_check_card(data['user'], value):
				raise serializers.ValidationError("A card with this number and date already exists on your account.")

			if self.instance is None:
				self.src_id = stripe.Customer.create_source(
					data['user'].customer.stripe_customer_id,
					source=data['stripe_src']
				).id
			else:
				data = self.update_data(data)
				
				stripe.Customer.modify_source(
					data['user'].customer.stripe_customer_id,
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
		except Exception as e:
			raise serializers.ValidationError(e)

		return validated_data

	def save(self, *args, **kwargs):
		data = self.validated_data
		card = Card.objects.update_or_create(
			src_id=self.src_id,
			user=data['user'],
			defaults={
				'line1':data['line1'],
				'line2':data['line2'],
				'city':data['city'],
				'state':data['state'],
				'country':data['country'],
				'zipcode':data['zipcode'],
				'first_name':data['first_name'],
				'last_name':data['last_name'],
				'email':data['email'],
			}
		)[0]
		return card


class ShippingAddressSerializer(serializers.ModelSerializer):
	user = serializers.HiddenField(default=serializers.CurrentUserDefault())

	class Meta:
		model = ShippingAddress
		fields = '__all__'