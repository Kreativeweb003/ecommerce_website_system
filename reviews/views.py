from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from core.permissions import superuser_required

from products.models import Product
from . import services
from .forms import ReviewForm, ReviewVoteForm, ReviewModerationForm, ReviewReplyForm
from .models import Review
from django_ratelimit.decorators import ratelimit
from core.ratelimit import real_ip_key



@login_required
@ratelimit(key=real_ip_key, rate="5/h", method="POST", block=True)
def review_create_view(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, status="published")

    existing_review = services.get_existing_review(product=product, user=request.user)
    if existing_review:
        messages.info(request, "You have already reviewed this product. You can edit your existing review.")
        return redirect("reviews:review_update", pk=existing_review.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                services.create_review(product=product, user=request.user, data=form.cleaned_data)
                messages.success(request, "Review submitted — it will appear once approved.")
                return redirect("products:product_detail", slug=product.slug)
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, "message") else e))
    else:
        form = ReviewForm()

    return render(request, "reviews/review_form.html", {"form": form, "product": product, "action": "Write"})


@login_required
def review_update_view(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            services.update_review(review=review, data=form.cleaned_data)
            messages.success(request, "Review updated — it will be re-reviewed before appearing again.")
            return redirect("products:product_detail", slug=review.product.slug)
    else:
        form = ReviewForm(instance=review)

    return render(request, "reviews/review_form.html", {"form": form, "product": review.product, "action": "Edit"})


@login_required
def review_delete_view(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        product_slug = review.product.slug
        services.delete_review(review=review)
        messages.info(request, "Review deleted.")
        return redirect("products:product_detail", slug=product_slug)

    return render(request, "reviews/review_confirm_delete.html", {"review": review})


@login_required
@ratelimit(key=real_ip_key, rate="30/m", method="POST", block=True)
def review_vote_view(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if request.method == "POST":
        form = ReviewVoteForm(request.POST)
        if form.is_valid():
            try:
                services.vote_on_review(review=review, user=request.user, vote=form.cleaned_data["vote"])
                return JsonResponse({
                    "success": True,
                    "helpful_count": review.helpful_count,
                    "not_helpful_count": review.not_helpful_count,
                })
            except ValidationError as e:
                return JsonResponse({"success": False, "error": str(e.message if hasattr(e, "message") else e)}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)


# --- Admin/moderation views ---

@login_required
@superuser_required
def review_moderation_queue_view(request):
    pending_reviews = services.get_pending_reviews()
    return render(request, "reviews/moderation_queue.html", {"reviews": pending_reviews})


@login_required
@superuser_required
def review_moderate_view(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if request.method == "POST":
        form = ReviewModerationForm(request.POST)
        if form.is_valid():
            services.moderate_review(
                review=review,
                status=form.cleaned_data["status"],
                note=form.cleaned_data.get("moderation_note", ""),
                moderator=request.user,
            )
            messages.success(request, f"Review {form.cleaned_data['status']}.")
            return redirect("reviews:moderation_queue")
    else:
        form = ReviewModerationForm()

    return render(request, "reviews/review_moderate.html", {"form": form, "review": review})


@login_required
@superuser_required
def review_reply_view(request, pk):
    review = get_object_or_404(Review, pk=pk)

    if request.method == "POST":
        form = ReviewReplyForm(request.POST)
        if form.is_valid():
            services.add_reply(review=review, responder=request.user, message=form.cleaned_data["message"])
            messages.success(request, "Reply posted.")
            return redirect("reviews:moderation_queue")
    else:
        form = ReviewReplyForm(instance=getattr(review, "reply", None))

    return render(request, "reviews/review_reply_form.html", {"form": form, "review": review})


