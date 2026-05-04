from django import forms
from .models import Course, CourseReview


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'subtitle', 'description', 'category', 'tags',
            'thumbnail', 'preview_video_url', 'level', 'language',
            'pricing_type', 'price', 'discounted_price', 'currency',
            'certificate_enabled', 'discussion_enabled',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned = super().clean()
        pricing = cleaned.get('pricing_type')
        price = cleaned.get('price')
        if pricing == 'paid' and (not price or price <= 0):
            raise forms.ValidationError('Paid courses must have a price greater than 0.')
        return cleaned


class CourseReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)],
        widget=forms.RadioSelect
    )

    class Meta:
        model = CourseReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }
