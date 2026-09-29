from django.contrib import admin
from .models import Review, ReviewVote, ReviewReply


class ReviewReplyInline(admin.StackedInline):
    model = ReviewReply
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "status", "is_verified_purchase", "created_at"]
    list_filter = ["status", "rating", "is_verified_purchase"]
    search_fields = ["product__name", "user__email", "comment"]
    inlines = [ReviewReplyInline]


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ["review", "user", "vote", "created_at"]