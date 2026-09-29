from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("product/<slug:product_slug>/write/", views.review_create_view, name="review_create"),
    path("<int:pk>/edit/", views.review_update_view, name="review_update"),
    path("<int:pk>/delete/", views.review_delete_view, name="review_delete"),
    path("<int:pk>/vote/", views.review_vote_view, name="review_vote"),

    path("moderation/", views.review_moderation_queue_view, name="moderation_queue"),
    path("moderation/<int:pk>/decide/", views.review_moderate_view, name="review_moderate"),
    path("moderation/<int:pk>/reply/", views.review_reply_view, name="review_reply"),
]
