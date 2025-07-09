from django.db import models
from accounts.models import User
from category.models import Product

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Panier de {self.user.email}"

class CartItem(models.Model):
    SIZE_CHOICES = [
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'),
    ]

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default='M')
    def __str__(self):
        return f"{self.quantity} × {self.product.product_name} (Taille: {self.size})"
