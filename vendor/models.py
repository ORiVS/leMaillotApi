from django.db import models
from django.utils.text import slugify

from accounts.models import User, UserProfile
from accounts.utils import send_notification

class Vendor (models.Model):
    user = models.OneToOneField(User, related_name='vendor', on_delete=models.CASCADE, null=True, blank=True)
    user_profile = models.OneToOneField(UserProfile, related_name='userprofile', on_delete=models.CASCADE, null=True, blank=True)
    vendor_name = models.CharField(max_length=50)
    vendor_license =models.ImageField(upload_to='vendor/license', null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='vendor/logos/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    slug = models.SlugField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
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