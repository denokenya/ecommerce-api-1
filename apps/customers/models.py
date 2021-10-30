from django.apps import apps
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from address.models import AbstractAddress


# Models
class Customer(models.Model):
	PURCHASE_WAIT_TIME = 5

	user = models.OneToOneField('users.User', related_name='customer', on_delete=models.CASCADE)
	if apps.is_installed('store'):
		price_level = models.ForeignKey('store.PriceLevel', on_delete=models.SET_NULL, blank=True, null=True)
		payment_methods = models.ManyToManyField('store.PaymentMethod', blank=True)

	stripe_customer_id = models.CharField("Customer Stripe ID", max_length=100, blank=True, null=True)
	purchase_attempt_time = models.DateTimeField(default=timezone.now)
	admin_made = models.BooleanField(default=False)

	class Meta:
		verbose_name = 'Customer Info'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if apps.is_installed('store'):
			self.old_price_level = self.price_level

	def __str__(self):
		return str(self.user)
		

class CustomerAddress(AbstractAddress):
	first_name = models.CharField("First Name", max_length=30)
	last_name = models.CharField("Last Name", max_length=30)
	email = models.EmailField("Email Address", max_length=30)


class Card(CustomerAddress):
	user = models.ForeignKey('users.User', related_name='card', on_delete=models.CASCADE)
	src_id = models.CharField("Credit Card Stripe ID", max_length=30)

	class Meta(CustomerAddress.Meta):
		verbose_name = "Credit Card"


class ShippingAddress(CustomerAddress):
	user = models.ForeignKey('users.User', related_name='shipping_address', on_delete=models.CASCADE)

	class Meta(CustomerAddress.Meta):
		verbose_name = "Shipping Address"


# Signals
@receiver(post_save, sender='users.User', dispatch_uid="user_created")
def user_created(sender, instance, created, *args, **kwargs):
	customer = Customer.objects.get_or_create(user=instance)[0]


@receiver(post_delete, sender=Customer, dispatch_uid="delete_customer")
def delete_customer(sender, instance, *args, **kwargs):
	if instance.user:
		instance.user.delete()