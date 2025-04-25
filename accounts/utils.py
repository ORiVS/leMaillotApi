from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string

"""
def send_verification_email(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    activation_url = f"http://{current_site.domain}{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"

    mail_subject = 'Active ton compte sur LeMaillot'
    message = render_to_string('accounts/emails/activation_email.html', {
        'user': user,
        'activation_url': activation_url,
    })

    to_email = user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html'
    email.send()

"""
def send_verification_code_email(user):
    subject = "Votre code de vérification"
    message = f"Bonjour {user.first_name},\n\nVoici votre code : {user.verification_code}\n\nL'équipe LeMaillot"
    send_mail(subject, message, 'no-reply@lemaillot.com', [user.email])
    print(f"[EMAIL] Code envoyé à {user.email} : {user.verification_code}")

def send_verification_code_sms(user):
    # Simulation, à remplacer par un vrai service (ex : Twilio)
    print(f"SMS to {user.phone_number}: Code = {user.verification_code}")