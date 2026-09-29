from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from products.models import Product


class Review(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending Moderation"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")

    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150, blank=True)
    comment = models.TextField()

    is_verified_purchase = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    moderation_note = models.CharField(max_length=255, blank=True)

    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reviews_review"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["product", "user"], name="unique_review_per_user_per_product"),
        ]
        indexes = [
            models.Index(fields=["product", "status"]),
        ]

    def __str__(self):
        return f"{self.rating}★ - {self.product.name} by {self.user.email}"

    @property
    def helpfulness_score(self):
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return 0
        return round((self.helpful_count / total_votes) * 100)


class ReviewVote(models.Model):
    VOTE_CHOICES = (
        ("helpful", "Helpful"),
        ("not_helpful", "Not Helpful"),
    )

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_votes")
    vote = models.CharField(max_length=15, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews_review_vote"
        constraints = [
            models.UniqueConstraint(fields=["review", "user"], name="unique_vote_per_user_per_review"),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.vote} on review #{self.review_id}"


class ReviewReply(models.Model):
    """Seller/admin response to a review — common in real-world storefronts."""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="reply")
    responder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews_review_reply"

    def __str__(self):
        return f"Reply to review #{self.review_id}"



