import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from order.models import Order
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from payments.serializers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateStripeCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        try:
            order = Order.objects.get(id=order_id, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Commande introuvable."}, status=404)

        if order.status != "pending":
            return Response({"error": "Commande déjà traitée."}, status=400)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {"name": f"Commande #{order.order_number}"},
                    "unit_amount": int(order.total_price * 100),
                },
                "quantity": 1,
            }],
            metadata={"order_id": str(order.id)},
            mode="payment",
            success_url="myapp://checkout-success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="myapp://checkout-cancel",
        )
        return Response({"checkout_url": session.url})

@csrf_exempt
def stripe_webhook(request):
    print("📩 Webhook Stripe reçu")

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        print("✅ Signature Stripe valide")
    except ValueError as e:
        print(f"❌ Erreur payload : {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Signature invalide : {e}")
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("💳 Paiement terminé : checkout.session.completed")

        order_id = session.get("metadata", {}).get("order_id")
        stripe_session_id = session.get("id")
        amount_total = int(session.get("amount_total", 0)) / 100
        customer_email = session.get("customer_details", {}).get("email")

        print(f"🧾 order_id reçu : {order_id}")
        print(f"💰 Montant total : {amount_total} €")
        print(f"📧 Email client : {customer_email}")

        try:
            order = Order.objects.get(id=order_id)
            print(f"🔍 Commande trouvée : {order}")
            order.status = "confirmed"
            order.save()
            print("✅ Statut changé à 'confirmed'")

            Payment.objects.update_or_create(
                order=order,
                defaults={
                    "user": order.customer,
                    "amount": amount_total,
                    "status": "succeeded",
                    "method": "card",
                    "stripe_session_id": stripe_session_id,
                    "paid_at": now(),
                }
            )
            print("💾 Paiement enregistré avec succès")
        except Order.DoesNotExist:
            print(f"❌ Commande avec ID {order_id} introuvable")

    else:
        print(f"ℹ️ Événement non pris en charge : {event['type']}")

    return HttpResponse(status=200)

class PaymentListAPIView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")