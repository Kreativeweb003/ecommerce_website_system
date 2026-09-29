from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from cart.services import merge_guest_cart_into_user_cart
from . import services
from .forms import (
    RegisterForm, LoginForm, ProfileUpdateForm,
    PasswordChangeCustomForm, AddressForm,
)
from .models import Address
from django_ratelimit.decorators import ratelimit
from core.ratelimit import real_ip_key




@ratelimit(key=real_ip_key, rate="5/m", method="POST", block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("products:home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            pre_login_session_key = request.session.session_key
            user = services.authenticate_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                merge_guest_cart_into_user_cart(session_key=pre_login_session_key, user=user)
                auth_login(request, user)
                next_url = request.GET.get("next", "products:home")
                return redirect(next_url)
            form.add_error(None, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


@ratelimit(key=real_ip_key, rate="3/m", method="POST", block=True)
def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("dashboard:home")
        return redirect("products:home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            pre_login_session_key = request.session.session_key
            user = services.register_user(
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                phone_number=form.cleaned_data.get("phone_number", ""),
            )
            merge_guest_cart_into_user_cart(session_key=pre_login_session_key, user=user)
            auth_login(request, user)
            messages.success(request, "Account created successfully. Welcome!")
            return redirect("products:home")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


  
@login_required
@ratelimit(key=real_ip_key, rate="5/m", method="POST", block=True)
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeCustomForm(request.POST)
        if form.is_valid():
            try:
                services.change_password(
                    user=request.user,
                    old_password=form.cleaned_data["old_password"],
                    new_password=form.cleaned_data["new_password"],
                )
                messages.success(request, "Password changed successfully. Please log in again.")
                auth_logout(request)
                return redirect("accounts:login")
            except ValueError as e:
                form.add_error("old_password", str(e))
    else:
        form = PasswordChangeCustomForm()

    return render(request, "accounts/change_password.html", {"form": form})
  


@login_required
def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")




@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            services.update_profile(user=request.user, data=form.cleaned_data)
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})





@login_required
def address_list_view(request):
    addresses = services.get_user_addresses(user=request.user)
    return render(request, "accounts/address_list.html", {"addresses": addresses})




@login_required
def address_create_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            services.add_address(user=request.user, data=form.cleaned_data)
            messages.success(request, "Address added successfully.")
            return redirect("accounts:address_list")
    else:
        form = AddressForm()

    return render(request, "accounts/address_form.html", {"form": form, "action": "Add"})




@login_required
def address_update_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            services.update_address(address=address, data=form.cleaned_data)
            messages.success(request, "Address updated successfully.")
            return redirect("accounts:address_list")
    else:
        form = AddressForm(instance=address)

    return render(request, "accounts/address_form.html", {"form": form, "action": "Edit"})




@login_required
def address_delete_view(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    if request.method == "POST":
        services.delete_address(address=address)
        messages.success(request, "Address deleted.")
        return redirect("accounts:address_list")

    return render(request, "accounts/address_confirm_delete.html", {"address": address})





