from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/change-password/", views.change_password_view, name="change_password"),

    path("addresses/", views.address_list_view, name="address_list"),
    path("addresses/add/", views.address_create_view, name="address_create"),
    path("addresses/<int:pk>/edit/", views.address_update_view, name="address_update"),
    path("addresses/<int:pk>/delete/", views.address_delete_view, name="address_delete"),
]