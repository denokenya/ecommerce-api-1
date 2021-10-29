from django.db import models
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify


class ItemType(models.Model):
	name = models.CharField(max_length=30, unique=True)
	slug = models.SlugField(unique=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		verbose_name = 'Item Type'

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		self.slug = slugify(self.name)	
		super().save(*args, **kwargs)


class ItemCategory(models.Model):
	name = models.CharField(max_length=30, unique=True)
	slug = models.SlugField(unique=True)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		self.slug = slugify(self.name)	
		super().save(*args, **kwargs)


class Parcel(models.Model):
	length = models.FloatField()
	width = models.FloatField()
	height = models.FloatField()
	weight = models.FloatField()

	def __str__(self):
		return f"{self.length}x{self.width}x{self.height}: {self.weight}"


class Item(models.Model):
	item_type = models.ForeignKey(ItemType, on_delete=models.CASCADE)
	item_category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE)
	parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)

	name = models.CharField(max_length=60)
	slug = models.SlugField()
	description = models.TextField(blank=True, null=True)
	number = models.CharField(max_length=30)

	is_active = models.BooleanField(default=True)

	class Meta:
		unique_together = ('item_type', 'item_category', 'name')

	def clean(self, *args, **kwargs):
		qs = Item.objects.filter(
			item_type=self.item_type, item_category=self.item_category, name__iexact=self.name
		)
		if qs.exists():
			if qs[0].pk != self.pk:
				raise ValidationError('Item with this Item type, Item category and Name already exists.')
		super().clean(*args, **kwargs)

	def __str__(self):
		return self.name

	def set_number(self):
		last_number = 0
		qs = Item.objects.all()
		if qs.count() > 0:
			last_number = list(qs.order_by('-number').values('number'))[0]['number']
		
		self.number = int(last_number) + 1

	def save(self, *args, **kwargs):
		if self.pk is None:
			self.set_number()

		self.slug = slugify(self.name)
		super().save(*args, **kwargs)


class Image(models.Model):
	item = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)

	name = models.CharField(max_length=50, blank=True, null=True)
	image = models.ImageField(blank=True, null=True, upload_to='catalog/image')
	number = models.PositiveIntegerField(default=0)

	def __str__(self):
		return f"Image: {self.item.name}"

	def set_number(self):
		last_number = 0
		qs = Image.objects.filter(item=self.item)
		if qs.count() > 0:
			last_number = list(qs.order_by('-number').values('number'))[0]['number']
		
		self.number = int(last_number) + 1

	def save(self, *args, **kwargs):
		if self.pk is None:
			self.set_number()

		super().save(*args, **kwargs)