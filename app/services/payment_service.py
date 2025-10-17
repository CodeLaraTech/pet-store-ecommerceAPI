from typing import Optional

class PaymentService:
    """Simple stub for payments. Integrate Stripe/Razorpay here."""

    def create_checkout(self, order_id: int, amount: float) -> str:
        return f"https://pay.example.com/checkout?order_id={order_id}&amount={amount}"

    def verify_webhook(self, payload: dict, signature: Optional[str]) -> bool:
        # TODO: implement signature verification
        return True

    def payment_status(self, order_id: int) -> str:
        # TODO: query PSP
        return "paid"