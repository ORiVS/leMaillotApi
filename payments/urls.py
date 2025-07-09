from django.urls import path
from .views import CreateStripeCheckoutSessionView, stripe_webhook, PaymentListAPIView

urlpatterns = [
    path("create-checkout-session/", CreateStripeCheckoutSessionView.as_view(), name="create-checkout-session"),
    path("webhook/", stripe_webhook, name="stripe-webhook"),
    path("", PaymentListAPIView.as_view()),
]
