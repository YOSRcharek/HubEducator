from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from core.models import Subscription

User = get_user_model()

class AddUserForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            ('student', 'Student'),
            ('teacher', 'Teacher'),
        ],
        required=True
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'profile_picture', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email already exists.")
        return email

    def clean_password2(self):
        """
        Keep the default password check (matching + validators),
        but ignore the UserAttributeSimilarityValidator.
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")

        # Appelle les validateurs par défaut sauf UserAttributeSimilarityValidator
        from django.contrib.auth.password_validation import validate_password
        from django.contrib.auth.password_validation import UserAttributeSimilarityValidator

        # Vérifie avec tous les validateurs
        try:
            validate_password(password2, self.instance)
        except ValidationError as e:
            # Supprime uniquement les erreurs liées à UserAttributeSimilarityValidator
            filtered_errors = [
                msg for msg in e.messages
                if "too similar" not in msg.lower()
            ]
            if filtered_errors:
                raise ValidationError(filtered_errors)

        return password2


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'profile_picture']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # empêcher doublons sauf pour le même utilisateur
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email already exists.")
        return email


# --------------------------
# Form to add/edit a subscription
# --------------------------
class SubscriptionForm(forms.ModelForm):
    duration = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., 30 days, 3 months, 1 year',
            'class': 'form-control'
        }),
        help_text="Enter the subscription duration (e.g., 30 days, 3 months, 1 year)"
    )
    
    features = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Enter each feature on a new line\nExample:\nAccess to all courses\nPriority support\nCertificates'
        }),
        help_text="Enter each feature on a new line"
    )
    
    user_type = forms.ChoiceField(
        choices=Subscription.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the type of user this subscription is for"
    )
    
    class Meta:
        model = Subscription
        fields = ['name', 'description', 'price', 'duration', 'features', 'user_type', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price