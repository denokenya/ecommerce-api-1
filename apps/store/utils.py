import stripe

from django.contrib import messages
from customers.models import Card


def stripe_make_payment(order):
	description = order.get_order_info()
	card = order.card

	total = order.grand_total
	if total <= 0.5:
		total = 0.51

	# Initiate payment
	payment_intent_id = stripe.PaymentIntent.create(
		description=description,
		amount=int(total * 100),
		currency='usd',
		customer=order.user.customer.stripe_customer_id,
	)['id']

	# Confirm payment
	payment_intent = stripe.PaymentIntent.confirm(
		payment_intent_id,
		payment_method=card.src_id,
	)

	return payment_intent_id


# def stripe_refund(order):
# 	if order.payment_intent_id:
# 		stripe.Refund.create(
# 			payment_intent=order.payment_intent_id,
# 		)


# def stripe_partial_charge(order, refund_amt):
# 	payment_intent_id = stripe.PaymentIntent.create(
# 		description="Partial Refund",
# 		amount=int(refund_amt * 100),
# 		currency='usd',
# 		customer=order.customer.stripe_customer_id,
# 	)['id']

# 	# Confirm payment
# 	payment_intent = stripe.PaymentIntent.confirm(
# 		payment_intent_id,
# 		payment_method=order.card.src_id,
# 	)


# def stripe_partial_refund(order, refund_amt):
# 	# payment_intent_id = stripe.PaymentIntent.create(
# 	# 	description="Partial Refund",
# 	# 	amount=int(refund_amt * 100),
# 	# 	currency='usd',
# 	# 	customer=order.customer.stripe_customer_id,
# 	# )['id']

# 	# # Confirm payment
# 	# payment_intent = stripe.PaymentIntent.confirm(
# 	# 	payment_intent_id,
# 	# 	payment_method=order.card.src_id,
# 	# )

# 	stripe.Refund.create(
# 		payment_intent=order.payment_intent_id,
# 		amount=int(refund_amt * 100)
# 	)