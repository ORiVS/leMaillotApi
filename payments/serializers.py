from rest_framework import serializers
from payments.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.SerializerMethodField()

    def get_order_number(self, obj):
        if obj.order:
            return obj.order.order_number
        return None

    class Meta:
        model = Payment
        fields = [
            "id", "order_number", "amount", "status", "method", "paid_at", "created_at"
        ]
