import stripe

from django.conf import settings
from .models import Customer


def stripe_get_customer(user):
	customer = user.customer

	if customer.stripe_customer_id is None:
		name = f"{user.first_name} {user.last_name}"
		customer_id = stripe.Customer.create(
			name=user.first_name,
			email=user.email,
		)['id']
		customer.stripe_customer_id = customer_id
		customer.save()

	return customer


def stripe_check_card(user, stripe_src):
	card = stripe.Source.retrieve(stripe_src)
	fingerprint = card.card.fingerprint
	exp_month = card.card.exp_month
	exp_year = card.card.exp_year

	card_list = stripe.Customer.list_sources(user.customer.stripe_customer_id,)['data']

	for card in card_list:
		if (
			card['card']['fingerprint'] == fingerprint and
			card['card']['exp_month'] == exp_month and
			card['card']['exp_year'] == exp_year
		):
			return card['id']

	return


def stripe_get_card(instance):
	card = stripe.Customer.retrieve_source(
		instance.user.customer.stripe_customer_id,
		instance.src_id,
	)
	return card


def stripe_get_card_list(customer):
	card_list = stripe.Customer.list_sources(customer.stripe_customer_id,)['data']
	return card_list


def stripe_delete_card(instance):
	stripe.Customer.delete_source(
		instance.user.customer.stripe_customer_id,
		instance.src_id,
	)