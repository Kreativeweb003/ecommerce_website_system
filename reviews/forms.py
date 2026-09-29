from django import forms
from .models import Review, ReviewReply


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, i) for i in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }


class ReviewVoteForm(forms.Form):
    vote = forms.ChoiceField(choices=[("helpful", "Helpful"), ("not_helpful", "Not Helpful")])


class ReviewModerationForm(forms.Form):
    status = forms.ChoiceField(choices=[("approved", "Approve"), ("rejected", "Reject")])
    moderation_note = forms.CharField(max_length=255, required=False)


class ReviewReplyForm(forms.ModelForm):
    class Meta:
        model = ReviewReply
        fields = ["message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}



