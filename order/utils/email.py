from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_order_confirmation_email(order):
    subject = f"Confirmation de votre commande #{order.order_number}"
    message = render_to_string("emails/order_confirmation.html", {
        "order": order,
        "user": order.customer,
    })
    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [order.customer.email],
        html_message=message,
    )
