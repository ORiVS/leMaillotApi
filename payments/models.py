from django.db import models
from django.utils import timezone
from order.models import Order
from accounts.models import User

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("card", "Carte bancaire"),
        ("mobile", "Paiement mobile"),
        ("cash", "Espèces"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("succeeded", "Réussi"),
        ("failed", "Échoué"),
        ("cancelled", "Annulé"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment", null=False, blank=False,)
    payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=200, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="card")
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_paid(self, intent_id=None):
        self.status = "succeeded"
        self.paid_at = timezone.now()
        if intent_id:
            self.payment_intent_id = intent_id
        self.save()

    def __str__(self):
        return f"Paiement de {self.amount}€ pour commande #{self.order.id} – {self.status}"