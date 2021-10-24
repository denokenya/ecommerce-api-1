import stripe

from rest_framework import serializers

from api_auth.models import User
from .models import Customer, Card, ShippingAddress
from .utils import stripe_check_card, stripe_get_customer


class CardSerializer(serializers.ModelSerializer):
	stripe_src = serializers.CharField(required=False)

	class Meta:
		model = Card
		exclude = ('user',)
		extra_kwargs = { 'src_id': {'read_only': True} }

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		request = self.context.get('request')
		if request:
			self.user = request.user
			if request.method == "POST":
				self.fields['stripe_src'].required = True

	def validate_stripe_src(self, value):
		try:
			stripe_get_customer(self.user)
			src_id = stripe_check_card(self.user, value)
		except Exception as e:
			raise serializers.ValidationError(e)			

		if src_id:
			raise serializers.ValidationError("A card with this number and date already exists on your account.")

		return value

	def validate(self, validated_data):
		data = validated_data

		try:
			if self.instance is None:
				self.src_id = stripe.Customer.create_source(self.user.customer.stripe_customer_id, source=data['stripe_src']).id
			else:
				self.src_id = self.instance.src_id
				for k in self.instance.__dict__:
					if data.get(k) is None:
						data[k] = getattr(self.instance, k)

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
		except Exception as e:
			raise serializers.ValidationError({'stripe_src': e})

		return validated_data

	def save(self, *args, **kwargs):
		data = self.validated_data
		card = Card.objects.update_or_create(
			src_id=self.src_id,
			user=self.user,
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
	class Meta:
		model = ShippingAddress
		exclude = ('user',)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		request = self.context.get('request')
		if request:
			if request.method == "POST":
				qs = User.objects.filter(pk=request.user.pk)
				self.fields['user'] = serializers.PrimaryKeyRelatedField(
					write_only=True,
					queryset=qs,
					default=qs[0]
				)