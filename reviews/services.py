from django.db import transaction, IntegrityError
from django.db.models import Avg, Count
from django.core.exceptions import ValidationError

from orders.models import OrderItem
from .models import Review, ReviewVote, ReviewReply





def has_purchased_product(*, user, product):
    return OrderItem.objects.filter(
        order__user=user, product=product, order__status__in=["paid", "processing", "shipped", "delivered"]
    ).exists()


def get_existing_review(*, product, user):
    return Review.objects.filter(product=product, user=user).first()





@transaction.atomic
def create_review(*, product, user, data):
    if get_existing_review(product=product, user=user):
        raise ValidationError("You have already reviewed this product.")

    is_verified = has_purchased_product(user=user, product=product)

    try:
        review = Review.objects.create(
            product=product,
            user=user,
            rating=data["rating"],
            title=data.get("title", ""),
            comment=data["comment"],
            is_verified_purchase=is_verified,
            status="pending",
        )
    except IntegrityError:
        # Handles the race where two submissions both passed the existence check above
        # before either committed — the unique constraint is the real source of truth.
        raise ValidationError("You have already reviewed this product.")

    return review


@transaction.atomic
def update_review(*, review, data):
    review.rating = data["rating"]
    review.title = data.get("title", "")
    review.comment = data["comment"]
    review.status = "pending"  # edited reviews go back through moderation
    review.save(update_fields=["rating", "title", "comment", "status", "updated_at"])
    return review


def delete_review(*, review):
    review.delete()


def get_approved_reviews_for_product(*, product):
    return Review.objects.filter(product=product, status="approved").select_related("user").prefetch_related("reply")


def get_product_rating_summary(*, product):
    approved_reviews = get_approved_reviews_for_product(product=product)
    summary = approved_reviews.aggregate(average_rating=Avg("rating"), total_reviews=Count("id"))

    rating_breakdown = {
        star: approved_reviews.filter(rating=star).count() for star in range(5, 0, -1)
    }

    return {
        "average_rating": round(summary["average_rating"], 1) if summary["average_rating"] else 0,
        "total_reviews": summary["total_reviews"],
        "rating_breakdown": rating_breakdown,
    }


@transaction.atomic
def vote_on_review(*, review, user, vote):
    if review.user_id == user.id:
        raise ValidationError("You cannot vote on your own review.")

    existing_vote = ReviewVote.objects.filter(review=review, user=user).first()

    if existing_vote:
        if existing_vote.vote == vote:
            raise ValidationError("You have already cast this vote.")
        # switch vote: decrement old count, increment new
        _adjust_vote_count(review=review, vote_type=existing_vote.vote, delta=-1)
        existing_vote.vote = vote
        existing_vote.save(update_fields=["vote"])
    else:
        ReviewVote.objects.create(review=review, user=user, vote=vote)

    _adjust_vote_count(review=review, vote_type=vote, delta=1)
    return review


def _adjust_vote_count(*, review, vote_type, delta):
    field = "helpful_count" if vote_type == "helpful" else "not_helpful_count"
    setattr(review, field, max(getattr(review, field) + delta, 0))
    review.save(update_fields=[field])


@transaction.atomic
def moderate_review(*, review, status, note="", moderator=None):
    review.status = status
    review.moderation_note = note
    review.save(update_fields=["status", "moderation_note", "updated_at"])
    return review


def add_reply(*, review, responder, message):
    reply, created = ReviewReply.objects.update_or_create(
        review=review, defaults={"responder": responder, "message": message}
    )
    return reply


def get_pending_reviews():
    return Review.objects.filter(status="pending").select_related("product", "user")



def revoke_verified_purchase_if_unqualified(*, user, product):
    """
    Called when an order is cancelled/refunded. Re-checks whether the user still has
    ANY qualifying purchase of this product, and strips the verified badge if not.
    Does nothing if no review exists — reviews aren't created by this flow.
    """
    review = get_existing_review(product=product, user=user)
    if not review or not review.is_verified_purchase:
        return

    if not has_purchased_product(user=user, product=product):
        review.is_verified_purchase = False
        review.save(update_fields=["is_verified_purchase", "updated_at"])



