from django.contrib.auth import authenticate
from django.db import transaction
from .models import User, Address
from notifications.services import notify_welcome, notify_password_changed


def register_user(*, first_name, last_name, email, password, phone_number=""):
    with transaction.atomic():
        user = User.objects.create_user(
            email=email, password=password, first_name=first_name,
            last_name=last_name, phone_number=phone_number,
        )
    notify_welcome(user=user)
    return user


def change_password(*, user, old_password, new_password):
    if not user.check_password(old_password):
        raise ValueError("Old password is incorrect.")
    user.set_password(new_password)
    user.save(update_fields=["password"])
    notify_password_changed(user=user)
    return user


def authenticate_user(*, email, password):
    """Returns a user instance if credentials are valid, else None."""
    return authenticate(username=email, password=password)


def update_profile(*, user, data):
    for field, value in data.items():
        setattr(user, field, value)
    user.save(update_fields=list(data.keys()))
    return user




def get_user_addresses(*, user):
    return Address.objects.filter(user=user)


@transaction.atomic
def add_address(*, user, data):
    if data.get("is_default"):
        Address.objects.filter(user=user, address_type=data.get("address_type", "shipping")).update(is_default=False)
    address = Address.objects.create(user=user, **data)
    return address


@transaction.atomic
def update_address(*, address, data):
    if data.get("is_default"):
        Address.objects.filter(
            user=address.user, address_type=data.get("address_type", address.address_type)
        ).exclude(pk=address.pk).update(is_default=False)
    for field, value in data.items():
        setattr(address, field, value)
    address.save()
    return address


def delete_address(*, address):
    address.delete()


def get_default_address(*, user, address_type="shipping"):
    return Address.objects.filter(user=user, address_type=address_type, is_default=True).first()


