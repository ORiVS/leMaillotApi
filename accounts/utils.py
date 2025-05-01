import os
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from twilio.rest import Client
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site

def send_html_email_with_logo(subject, template_path, context, to_email):
    """
    Envoie un e-mail HTML avec logo intégré automatiquement si 'cid:lemaillot_logo' est utilisé dans le template.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    html_content = render_to_string(template_path, context)

    email = EmailMultiAlternatives(subject, '', from_email, [to_email])
    email.attach_alternative(html_content, "text/html")

    if "cid:lemaillot_logo" in html_content:
        logo_path = os.path.join(settings.BASE_DIR, 'static/email_assets/LeMaillot_final.webp')
        with open(logo_path, 'rb') as img:
            logo = MIMEImage(img.read())
            logo.add_header('Content-ID', '<lemaillot_logo>')
            logo.add_header('Content-Disposition', 'inline', filename='logo.webp')
            email.attach(logo)

    email.send()

def send_notification(mail_subject, mail_template, context):
    to_email = context['user'].email
    send_html_email_with_logo(mail_subject, mail_template, context, to_email)

def send_verification_code_email(user):
    context = {'user': user}
    send_html_email_with_logo(
        subject="Votre code de vérification",
        template_path="accounts/emails/verification_code.html",
        context=context,
        to_email=user.email
    )
    print(f"[EMAIL] Code envoyé à {user.email} : {user.verification_code}")

def send_verification_code_sms(user):
    print(f"SMS to {user.phone_number}: Code = {user.verification_code}")

def send_verification_code_sms(user):
    message = (
        f"LeMaillot ⚽\n\n"
        f"Bonjour {user.first_name}, voici votre code de vérification : {user.verification_code}\n\n"
        "Ce code est valide pendant 10 minutes.\n\n"
        "Merci et à bientôt !"
    )

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=user.phone_number
    )
