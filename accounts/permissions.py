from rest_framework.permissions import BasePermission

class IsVendor(BasePermission):
    """
    Autorise uniquement les vendeurs (user.role == 1)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 1

class IsCustomer(BasePermission):
    """
    Autorise uniquement les clients (user.role == 2)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 2
