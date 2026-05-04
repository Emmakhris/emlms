from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm

User = get_user_model()


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, label='Last Name', widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    field_order = ['first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar', 'bio', 'phone_number', 'country', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'size'):
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError('Avatar must be 2 MB or smaller.')
            valid_types = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
            content_type = getattr(avatar, 'content_type', '')
            if content_type and content_type not in valid_types:
                raise forms.ValidationError('Only JPEG, PNG, WebP, or GIF images are allowed.')
        return avatar
