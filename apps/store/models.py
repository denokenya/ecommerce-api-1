from django.db import models, transaction
from django.db.models import Manager, Sum
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from address.models import AbstractAddress
from catalog.models import Item, ItemType
from customers.models import Customer


# Constants
ADD = 'Add'
REMOVE = 'Remove'
DEFAULT_TAX = 0.07


# Models
class PaymentMethod(models.Model):
	CREDIT_CARD = 'Credit Card'
	IN_PERSON = 'In Person'

	CHOICES = [
		[CREDIT_CARD, CREDIT_CARD],
		[IN_PERSON, IN_PERSON],
	]

	name = models.CharField(max_length=20, choices=CHOICES, unique=True)

	def __str__(self):
		return self.name


class PostOffice(AbstractAddress):
	name = models.CharField(max_length=100, unique=True)

	def __str__(self):
		return self.name


class Location(AbstractAddress):
	post_office = models.ForeignKey(PostOffice, on_delete=models.CASCADE, blank=True, null=True)

	name = models.CharField(max_length=100, unique=True)
	is_active = models.BooleanField(default=True)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.initial_is_active = self.is_active
		if self.pk is None:
			self.initial_is_active = False

	def __str__(self):
		return self.name


class StoreItem(models.Model):
	item = models.ForeignKey('catalog.Item', on_delete=models.CASCADE)
	location = models.ForeignKey(Location, on_delete=models.CASCADE)

	quantity = models.PositiveIntegerField(default=0)

	class Meta:
		unique_together = ('item', 'location')

		verbose_name_plural = 'Inventory w/Location'
		verbose_name_plural = 'Inventory w/Location'

	def __str__(self):
		return f"{self.item} - {self.location} ({self.quantity})"

	def clean_fields(self, exclude=None):
		if self.pk is None:
			if StoreItem.objects.filter(item=self.item, location=self.location).exists():
				raise ValidationError("StoreItem with location already exists for this item.")

		return super().clean_fields(exclude=None)

	def quantity_in_carts(self):
		cart_quantity = 0

		total = OrderItem.objects.filter(
			store_item=self, order__date_ordered__isnull=True, order__date_cancelled__isnull=True
		).aggregate(Sum('quantity'))['quantity__sum']

		if total:
			cart_quantity = total

		return self.quantity - cart_quantity

	def quantity_dropdown(self):
		quantity = self.quantity_in_carts()
		if quantity > 10:
			quantity = 10

		return range(1, quantity+1)

	def in_stock(self):
		return self.quantity > 0


class InventoryRecord(models.Model):
	CHOICES = [
		[ADD, ADD],
		[REMOVE, REMOVE]
	]

	store_item = models.ForeignKey(StoreItem, verbose_name="Item w/ Location", on_delete=models.CASCADE)
	order_item = models.ForeignKey('store.OrderItem', on_delete=models.CASCADE, blank=True, null=True)

	date = models.DateTimeField(default=timezone.now)
	option = models.CharField(max_length=10, choices=CHOICES)
	info = models.TextField(blank=True, null=True)
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])

	class Meta:
		verbose_name = 'Inventory Records'
		verbose_name_plural = 'Inventory Records'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.init_quantity = self.quantity
		if self.pk is None:
			self.init_quantity = 0

	def __str__(self):
		return f"{self.option} {self.quantity}: {self.store_item}"

	def clean_fields(self, exclude=None):
		quantity_dif = self.quantity - self.init_quantity
		quantity_in_stock = self.store_item.quantity

		if self.option == REMOVE and quantity_dif > quantity_in_stock:
			raise ValidationError("Unable to remove the entered amount. Not enough of the item in stock.")

		return super().clean_fields(exclude=None)

	def quantity_change(self):
		return self.quantity - self.init_quantity


class PriceLevel(models.Model):
	name = models.CharField(max_length=10)
	default = models.BooleanField(default=False)

	class Meta:
		verbose_name = 'Price'
		verbose_name_plural = 'Price'

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)

		qs = PriceLevel.objects.filter(default=True)
		if qs.count() != 1:
			qs.update(default=False)

			price_level = PriceLevel.objects.all()[0] 
			price_level.default = True
			price_level.save()


class PriceType(models.Model):
	item_type = models.ForeignKey('catalog.ItemType', on_delete=models.CASCADE)
	price_level = models.ForeignKey(PriceLevel, on_delete=models.CASCADE)

	def __str__(self):
		return self.item_type.name

	def price_type_link(self):
		if self.pk:
			html_content = ''
			url = reverse('admin:store_pricetype_change', args=(self.pk,))
			html_content = '<a href="{}">{}</a><br>'.format(url, self.item_type.name)
			return format_html(html_content)

		return ''
	price_type_link.short_description = 'View'

	def price_level_link(self):
		if self.pk:
			html_content = ''
			url = reverse('admin:store_pricelevel_change', args=(self.price_level.pk,))
			html_content = '<a href="{}">{}</a><br>'.format(url, self.price_level.name)
			return format_html(html_content)

		return ''
	price_level_link.short_description = 'Back to'


class Price(models.Model):
	price_type = models.ForeignKey(PriceType, on_delete=models.CASCADE)
	item = models.ForeignKey(Item, on_delete=models.CASCADE)

	price = models.FloatField(default=0, validators=[MinValueValidator(0)])

	def __str__(self):
		return f"${self.price} - {self.item}"

	def level(self):
		return self.price_type.price_level.name


class CustomPrice(models.Model):
	user = models.ForeignKey('api_auth.User', on_delete=models.CASCADE)
	item = models.ForeignKey(Item, on_delete=models.CASCADE)

	price = models.FloatField(default=0)

	def __str__(self):
		return f"${self.price} - {self.item}"


def get_user_price(user, item):
	qs = CustomPrice.objects.filter(user=user, item=item)
	if qs.exists():
		return qs[0].price

	qs = Price.objects.filter(price_type__price_level=user.customer.price_level, item=item)
	if qs.exists():
		return qs[0].price

	return 0


class OrderManager(Manager):
	def get_or_create_active(self, user):
		obj, created = Order.objects.get_or_create(
			user=user,
			date_ordered__isnull=True,
			date_paid__isnull=True,
			date_cancelled__isnull=True,
			date_recieved__isnull=True
		)
		return [obj, created]

	def past(self, user):
		qs = self.get_queryset()
		qs = qs.filter(
			user=user,
			date_ordered__isnull=False,
			date_paid__isnull=False,
			date_cancelled__isnull=True
		)
		return qs

	def cancelled(self, user):
		qs = self.get_queryset()
		qs = qs.filter(user=user, date_cancelled__isnull=False)
		return qs


class Order(models.Model):
	user = models.ForeignKey('api_auth.User', related_name='orders', on_delete=models.CASCADE)
	payment_method = models.ForeignKey(PaymentMethod, verbose_name='Payment Method', on_delete=models.SET_NULL, blank=True, null=True)
	card = models.ForeignKey('customers.Card', on_delete=models.CASCADE, blank=True, null=True)

	payment_intent_id = models.CharField('Payment Intent Stripe ID', max_length=30, blank=True, null=True)
	number = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])

	date_ordered = models.DateTimeField('Placed', blank=True, null=True)
	date_paid = models.DateTimeField('Paid', blank=True, null=True)
	date_recieved = models.DateTimeField('Recieved', blank=True, null=True)
	date_cancelled = models.DateTimeField('Cancelled', blank=True, null=True)

	subtotal = models.FloatField(default=0)
	shipping_total = models.FloatField('Shipping Total', default=0)
	tax = models.FloatField('Tax', default=0)
	grand_total = models.FloatField('Grand Total', default=0)

	amt_charged = models.FloatField('Amount Charged', default=0)
	amt_refunded = models.FloatField('Amount Refunded', default=0)

	notes = models.TextField(blank=True, null=True)

	objects = OrderManager()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		if self.pk is None:
			self.set_number()

	def __str__(self):
		return f"{self.user} | {self.number}"

	def set_number(self):
		number = 0
		qs = Order.objects.filter(number__isnull=False).order_by('-number')

		if qs.exists():
			number = qs[0].number + 1		
		self.number = number

	def is_active(self):
		return self.date_ordered is None and self.date_cancelled is None

	def has_items_in_cart(self):
		return self.orderitem_set.filter(quantity__gt=0).exists()

	def get_order_info(self):
		info_list = []
		for order_item in self.orderitem_set.all():
			item = order_item.store_item.item
			info_list.append(
				f"{order_item.quantity} order(s) of {item.name}"
			)

		info = ', '.join(info_list)
		return info

	def update_subtotal(self):
		subtotal = 0
		for order_item in self.orderitem_set.all():
			subtotal += order_item.total

		self.subtotal = subtotal
		return self.subtotal

	def update_shipping_total(self):
		return self.shipping_total

	def update_tax(self):
		self.tax = (self.subtotal + self.shipping_total) * DEFAULT_TAX
		return self.tax

	def update_grand_total(self):
		self.grand_total = self.update_subtotal() + self.update_shipping_total() + self.update_tax()
		self.save()

	def pre_payment(self, card):
		self.orderitem_set.filter(quantity__lt=1).delete()

		credit_card = PaymentMethod.CHOICES[1][0]
		self.payment_method = PaymentMethod.objects.get_or_create(name=credit_card)[0]
		self.card = card
		self.save()

	def make_payment(self, payment_intent_id):
		self.payment_intent_id = payment_intent_id
		self.date_ordered = timezone.now()
		self.date_paid = timezone.now()
		self.save()

		for order_item in self.orderitem_set.filter(quantity__gt=0):
			InventoryRecord.objects.create(
				order_item=order_item,
				store_item=order_item.store_item,
				option=REMOVE,
				quantity=order_item.quantity
			)


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE)
	store_item = models.ForeignKey(StoreItem, verbose_name='Item w/Location', on_delete=models.CASCADE)
	shipping_address = models.ForeignKey('customers.ShippingAddress', on_delete=models.CASCADE, blank=True, null=True)

	quantity = models.PositiveIntegerField(default=0)
	price = models.FloatField(default=0)
	total = models.FloatField(default=0)

	class Meta:
		unique_together = ('order', 'store_item',)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.init_quantity = self.quantity

	def __str__(self):
		return f"{self.store_item.item}: {self.quantity}"

	def quantity_dif(self):
		return self.quantity-self.init_quantity

	def clean_fields(self, exclude=None):
		if self.quantity_dif() > self.store_item.quantity_in_carts():
			raise ValidationError("Not enough to add.")

		return super().clean_fields(exclude=None)

	def set_total(self):
		self.total = self.quantity * self.price

	def save(self, *args, **kwargs):
		if self.order.is_active():
			self.price = get_user_price(self.order.user, self.store_item.item)
			self.set_total()

		super().save(*args, **kwargs)


# Signals
@receiver(post_save, sender=InventoryRecord, dispatch_uid="inv_record_updated")
def inv_record_updated(sender, instance, created, **kwargs):
	store_item = instance.store_item

	if instance.option == ADD:
		store_item.quantity += instance.quantity_change()
	else:
		quantity_change = instance.quantity_change()
		store_item.quantity -= quantity_change

		if quantity_change > 0:
			# Didn't use update to activate signal on save
			qs = OrderItem.objects.filter(store_item=instance.store_item, order__date_ordered__isnull=True, order__date_cancelled__isnull=True)
			for order_item in qs:
				order_item.quantity = 0
				order_item.save()

	store_item.save()


@receiver(pre_delete, sender=InventoryRecord, dispatch_uid="inv_record_deleted")
def inv_record_deleted(sender, instance, **kwargs):
	store_item = instance.store_item

	if instance.option == ADD:
		store_item.quantity -= instance.quantity
	else:
		store_item.quantity += instance.quantity
	
	store_item.save()


@receiver(post_save, sender=PriceLevel, dispatch_uid="price_level_created")
def price_level_created(sender, instance, created, **kwargs):
	if created:
		for item_type in ItemType.objects.all():
			price_type = PriceType.objects.create(item_type=item_type, price_level=instance)

			for item in Item.objects.all():
				Price.objects.create(price_type=price_type, item=item)


@receiver(post_save, sender=Customer, dispatch_uid="price_level_changed")
def price_level_changed(sender, instance, **kwargs):
	if instance.old_price_level != instance.price_level:
		qs = OrderItem.objects.filter(
			order__user__customer=instance,
			order__date_ordered__isnull=True,
			order__date_paid__isnull=True,
		)

		for order_item in qs:
			new_price = Price.objects.get(
				item=order_item.store_item.item,
				price_type__price_level=instance.price_level
			).price
			order_item.price = new_price
			order_item.save()


@receiver(post_save, sender='catalog.Item', dispatch_uid="item_created_create_price")
def item_created_create_price(sender, instance, created, **kwargs):
	if created:
		for level in PriceLevel.objects.all():
			price_type = PriceType.objects.get_or_create(item_type=instance.item_type, price_level=level)[0]
			Price.objects.create(price_type=price_type, item=instance)


@receiver(post_save, sender=OrderItem, dispatch_uid="update_total")
def update_total(sender, instance, created, **kwargs):
	if instance.order.is_active():
		instance.order.update_grand_total()



def update_prices(item, price):
	qs = OrderItem.objects.filter(
		order__date_ordered__isnull=True,
		order__date_paid__isnull=True,
		store_item__item=item
	)

	with transaction.atomic():
		for order_item in qs:
			order_item.price = price
			order_item.save()


@receiver(post_save, sender=CustomPrice, dispatch_uid="save_update_custom_prices")
def save_update_custom_prices(sender, instance, created, **kwargs):
	update_prices(instance.item, instance.price)


@receiver(post_save, sender=Price, dispatch_uid="save_update_prices")
def save_update_prices(sender, instance, created, **kwargs):
	update_prices(instance.item, instance.price)


@receiver(post_delete, sender=CustomPrice, dispatch_uid="delete_update_prices")
def delete_update_prices(sender, instance, **kwargs):
	price = Price.objects.get(
		item=instance.item,
		price_type__price_level=instance.user.customer.price_level
	).price

	update_prices(instance.item, price)

