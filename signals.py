
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomerOrder, User

from .emails import send_order_confirmation_email, send_welcome_email

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def send_welcome_email_on_signup(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        send_welcome_email(instance)
    except Exception:
      
        logger.exception("Failed to send welcome email for user_id=%s", instance.pk)


@receiver(post_save, sender=CustomerOrder)
def send_confirmation_email_on_order(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        send_order_confirmation_email(instance)
    except Exception:
        
        logger.exception("Failed to send order confirmation for order_id=%s", instance.pk)
