from rest_framework import serializers

from api_auth.serializers import PhoneSerializer
from api_auth.models import User
from customers.models import Card, Customer
from customers.serializers import CardSerializer, ShippingAddressSerializer

from .models import *
from .utils import stripe_make_payment


# Catalog
class LocationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Location
		fields = '__all__'
		extra_kwargs = {'name': {'validators': []}}


class StoreItemSerializer(serializers.ModelSerializer):
	location = LocationSerializer()

	class Meta:
		model = StoreItem
		fields = ('id', 'item', 'quantity', 'location')
		depth = 0
		extra_kwargs = {
			'quantity': {'read_only': True}
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.context['request'].method == 'GET':
			self.Meta.depth = 1

	def validate_location(self, value):
		location = Location.objects.update_or_create(
			name=value['name'],
			defaults={
				'line1': value['line1'],
				'line2': value.get('line2'),
				'city': value.get('city'),
				'state': value['state'],
				'zipcode': value['zipcode'],
				'country': value['country']
			}
		)[0]
		return location


class InventoryRecordSerializer(serializers.ModelSerializer):
	class Meta:
		model = InventoryRecord
		exclude = ('order_item',)

	def validate_quantity(self, value):
		if value < 1:
			raise serializers.ValidationError("Invalid quantity")
		return value

	def validate(self, validated_data):
		vd = validated_data
		error = {'quantity': "Unable to remove the entered amount. Not enough of the item in stock."}

		if vd['option'] == REMOVE:
			if self.instance:
				quantity_dif = vd['quantity'] - self.instance.init_quantity
				quantity_in_stock = self.instance.store_item.quantity
				if quantity_dif > quantity_in_stock:
					raise serializers.ValidationError(error)
			
			elif vd['store_item'].quantity-vd['quantity'] < 0:
				raise serializers.ValidationError(error)

		return validated_data


# Customer
class CustomerSerializer(serializers.ModelSerializer):
	class Meta:
		model = Customer
		fields = ('stripe_customer_id', 'purchase_attempt_time', 'price_level', 'payment_methods')
	
	def to_representation(self, instance):
		customer = super().to_representation(instance)
		customer['price_level'] = instance.price_level.name
		customer['payment_methods'] = list(instance.payment_methods.all().values_list('name', flat=True))
		return customer


class ExtendedUserSerializer(serializers.ModelSerializer):
	phone = PhoneSerializer(read_only=True)
	customer = CustomerSerializer(read_only=True)
	card = CardSerializer(read_only=True, many=True)
	shipping_address = ShippingAddressSerializer(read_only=True, many=True)

	class Meta:
		model = User
		fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'customer', 'card', 'shipping_address')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['orders'] = OrderSerializer(
			instance=Order.objects.get_or_create_active(self.instance)[0], read_only=True, many=True
		)


# Order
class OrderItemSerializer(serializers.ModelSerializer):
	class Meta:
		model = OrderItem
		fields = ('store_item', 'quantity', 'price', 'total', 'shipping_address',)
		depth = 2


class OrderSerializer(serializers.ModelSerializer):
	orderitem_set = OrderItemSerializer(many=True)

	class Meta:
		model = Order
		fields = (
			'number',

			'subtotal',
			'shipping_total',
			'tax',
			'grand_total',
			'amt_charged',
			'amt_refunded',
			
			'payment_method',
			'card',
			'payment_intent_id',

			'date_ordered',
			'date_paid',
			'date_recieved',
			'date_cancelled',

			'notes',
			'orderitem_set'
		)


# Cart
class CartSerializer(serializers.Serializer):
	quantity = serializers.IntegerField()

	def validate_quantity(self, value):
		if value < 0:
			raise serializers.ValidationError("Quantity cannot be negative.")

		if value - self.instance.quantity > self.instance.store_item.quantity_in_carts():
			raise serializers.ValidationError("Not enough to add.")
		return value

	def update(self):
		self.instance.quantity = self.validated_data['quantity']
		self.instance.save()
		return self.instance


class CheckoutSerializer(serializers.Serializer):
	card = serializers.PrimaryKeyRelatedField(queryset=Card.objects.all())

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		request = self.context.get('request')
		if request:
			self.order = Order.objects.get_or_create_active(user=request.user)[0]

	def validate(self, validated_data):
		user_pms = list(
			self.order.user.customer.payment_methods.all().values_list('name', flat=True)
		)
		if PaymentMethod().CREDIT_CARD not in user_pms:
			raise serializers.ValidationError("User is not allowed to make a credit card payment.")

		if not self.order.has_items_in_cart():
			raise serializers.ValidationError("No items in cart.")
		return validated_data

	def save(self):
		self.order.pre_payment(self.validated_data['card'])
		payment_intent_id = stripe_make_payment(self.order)
		self.order.make_payment(payment_intent_id)
		return self.order