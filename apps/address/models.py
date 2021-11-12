from django.db import models
from django_countries.fields import CountryField


class AbstractAddress(models.Model):
	line1 = models.CharField(max_length=30)
	line2 = models.CharField(max_length=30, blank=True, null=True)
	city = models.CharField(max_length=30)
	state = models.CharField(max_length=30)
	zipcode = models.CharField(max_length=20)
	country = CountryField(multiple=False)

	class Meta:
		abstract = True

	def __str__(self):
		line2 = " " + self.line2 if self.line2 else ""
		return f"{self.line1}{line2}, {self.city}, {self.state}, {self.zipcode}, {self.country}"