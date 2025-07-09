from django.db import models
from accounts.models import User
from category.models import Product
from django.utils import timezone
import re

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    DELIVERY_CHOICES = [
        ('pickup', 'Retrait en boutique'),
        ('delivery', 'Livraison à domicile'),
    ]
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup')
    delivery_address = models.CharField(max_length=255)    
    delivery_city = models.CharField(max_length=100, blank=True, null=True)
    delivery_postal_code = models.CharField(max_length=20, blank=True, null=True)
    delivery_country = models.CharField(max_length=100, blank=True, null=True)
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande #{self.id} - {self.customer.email}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"CM-{today}"

        last_order = (
            Order.objects
            .filter(order_number__startswith=prefix)
            .order_by('-created_at')
            .first()
        )

        if last_order:
            # Extraire le suffixe de type XX (CM-20250702-03)
            match = re.search(rf"{prefix}-(\d+)", last_order.order_number)
            if match:
                last_seq = int(match.group(1))
            else:
                last_seq = 0
        else:
            last_seq = 0

        new_seq = last_seq + 1
        return f"{prefix}-{new_seq:02d}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande #{self.order.id} : {self.previous_status} → {self.new_status} ({self.changed_at})"
