import logging
from datetime import date

logger = logging.getLogger("email_service")


def send_welcome_email(email: str, name: str):
    logger.info(f"Welcome email sent to {email} ({name})")


def send_order_confirmation(email: str, order_id: int):
    logger.info(f"Order confirmation sent to {email} for order {order_id}")


def send_subscription_reminder(email: str, subscription_id: int, next_date: date):
    logger.info(f"Subscription {subscription_id} reminder to {email} for {next_date}")


def send_low_stock_alert(product_slug: str, remaining: int):
    logger.warning(f"Low stock alert for {product_slug}: {remaining} left")