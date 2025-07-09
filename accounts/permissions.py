from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from accounts.models import User


class IsVendor(BasePermission):
    """
    Autorise uniquement les vendeurs (user.role == 1)
    """

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        if user.role != User.VENDOR:
            raise PermissionDenied("Vous devez être un vendeur pour accéder à cette ressource.")

        try:
            _ = user.vendor  # Vérifie si l'objet Vendor existe
        except:
            raise PermissionDenied("Aucun profil vendeur associé à ce compte.")

        return True

class IsCustomer(BasePermission):
    """
    Autorise uniquement les clients (user.role == 2)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 2
