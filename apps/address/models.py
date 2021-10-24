from django.db import models
from django_countries.fields import CountryField


class Address(models.Model):
	line1 = models.CharField(max_length=30)
	line2 = models.CharField(max_length=30, blank=True, null=True)
	city = models.CharField(max_length=30)
	state = models.CharField(max_length=30)
	zipcode = models.CharField(max_length=20)
	country = CountryField(multiple=False)

	class Meta:
		abstract = True

	def __str__(self):
		val = ""
		if self.line2:
			val = f"{self.line2},"

		address = f"{self.line1},{val} {self.city}, {self.state}, {self.zipcode}, {self.country}"
		return address