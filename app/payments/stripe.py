import stripe, os
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_payment_intent(amount):
    return stripe.PaymentIntent.create(
        amount=int(amount * 100),
        currency="usd"
    )
