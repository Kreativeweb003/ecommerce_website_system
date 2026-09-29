from django.core.exceptions import PermissionDenied
from functools import wraps


def staff_required(view_func):
    """Lighter alternative to @permission_required when you just need 'any staff member'."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied("Staff access required.")
        return view_func(request, *args, **kwargs)
    return wrapper


def owns_object(*, user, obj, owner_field="user"):
    """Generic ownership check — e.g. does this user own this order/review/address."""
    return getattr(obj, f"{owner_field}_id", None) == user.id


class IsOwnerOrStaffMixin:
    """
    Class-based view mixin: restricts access to the object's owner or staff.
    Expects self.get_object() and an owner_field attribute (defaults to 'user').
    """
    owner_field = "user"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not (owns_object(user=request.user, obj=obj, owner_field=self.owner_field) or request.user.is_staff):
            raise PermissionDenied("You do not have permission to access this object.")
        return super().dispatch(request, *args, **kwargs)


def superuser_required(view_func):
    """
    Restricts a view to superusers only. Used on every custom admin-panel view
    across dashboard, products, inventory, orders, payments, coupons, shipping,
    and reviews — this IS the access control for the whole admin panel.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied("Admin panel access is restricted to superusers.")
        return view_func(request, *args, **kwargs)
    return wrapper