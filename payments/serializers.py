from rest_framework import serializers
from payments.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "order_number", "amount", "status", "method", "paid_at", "created_at"
        ]
