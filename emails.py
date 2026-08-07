
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send_templated_email(subject, template_name, context, to_email):
    try:
        html_body = render_to_string(template_name, context)
    except TemplateDoesNotExist:
        logger.info(
            "Skipping email '%s' to %s — template %s not created yet.",
            subject, to_email, template_name,
        )
        return False

    text_body = strip_tags(html_body)
    send_mail(
        subject=subject,
        message=text_body,
        html_message=html_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=True, 
    )
    return True


def send_welcome_email(user):
    """Sent once, right after a new account is created."""
    _send_templated_email(
        subject="Welcome to Perfume Platform!",
        template_name="emails/welcome.html",
        context={"first_name": user.first_name},
        to_email=user.email,
    )


def send_order_confirmation_email(order):
    """Sent once, right after a customer order is created."""
    _send_templated_email(
        subject=f"Order #{order.order_id} confirmed",
        template_name="emails/order_confirmation.html",
        context={
            "first_name": order.user.first_name,
            "order_id": order.order_id,
            "total_amount": order.total_amount,
            "order_date": order.order_date,
        },
        to_email=order.user.email,
    )


def send_shipping_notification_email(order):
    """
    Sent by the admin-triggered shipping endpoint (Fuad's Sprint 6 task,
    "Shipping Email API Endpoint") — exposed here so that view can just
    call this function instead of duplicating email-sending logic.
    """
    _send_templated_email(
        subject=f"Order #{order.order_id} has shipped",
        template_name="emails/shipping_notification.html",
        context={
            "first_name": order.user.first_name,
            "order_id": order.order_id,
        },
        to_email=order.user.email,
    )


def send_password_reset_email(user, reset_token):
    """
    Sent when a password reset is requested. Not wired to a signal (there's
    no PasswordResetToken creation flow yet — see README) — call this
    directly from that view once it exists.
    """
    _send_templated_email(
        subject="Reset your Perfume Platform password",
        template_name="emails/password_reset.html",
        context={
            "first_name": user.first_name,
            "reset_token": reset_token,
        },
        to_email=user.email,
    )
