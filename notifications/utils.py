from .models import Notification

def notify_user(user, title, message, type="INFO"):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        type=type
    )
