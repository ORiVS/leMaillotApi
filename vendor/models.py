from django.db import models
from django.utils.text import slugify

from accounts.models import User, UserProfile
from accounts.utils import send_notification

class Vendor (models.Model):
    user = models.OneToOneField(User, related_name='user', on_delete=models.CASCADE)
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE)
    vendor_name = models.CharField(max_length=50)
    vendor_license =models.ImageField(upload_to='vendor/license', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    slug = models.SlugField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.vendor_name

    def save(self, *args, **kwargs):
        if self.pk:
            orig = Vendor.objects.get(pk=self.pk)
            if orig.is_approved != self.is_approved:
                mail_template = 'accounts/emails/admin_approval.html'
                context = {
                    'user': self.user,
                    'is_approved': self.is_approved,
                }
                subject = (
                    "Félicitations ! Vous avez été approuvé !"
                    if self.is_approved else
                    "Nous sommes désolés ! Vous n'avez pas été approuvé !"
                )
                send_notification(subject, mail_template, context)

        if not self.slug:
            self.slug = slugify(self.vendor_name)

        return super().save(*args, **kwargs)