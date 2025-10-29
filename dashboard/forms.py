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
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Basic Plan',
                'minlength': '3',
                'maxlength': '100'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Describe the subscription plan',
                'minlength': '10',
                'maxlength': '500'
            }),
            'price': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'max': '10000',
                'class': 'form-control',
                'placeholder': '0.00'
            }),
        }
    
    def clean_name(self):
        """Validate subscription name."""
        name = self.cleaned_data.get('name')
        if name:
            # Vérifier la longueur minimale
            if len(name.strip()) < 3:
                raise forms.ValidationError("Name must be at least 3 characters long.")
            
            # Vérifier si le nom existe déjà (sauf pour l'édition)
            existing = Subscription.objects.filter(name__iexact=name.strip())
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError("A subscription with this name already exists.")
        
        return name.strip()
    
    def clean_description(self):
        """Validate description."""
        description = self.cleaned_data.get('description')
        if description:
            if len(description.strip()) < 10:
                raise forms.ValidationError("Description must be at least 10 characters long.")
            if len(description.strip()) > 500:
                raise forms.ValidationError("Description cannot exceed 500 characters.")
        return description.strip()
    
    def clean_price(self):
        """Validate price."""
        price = self.cleaned_data.get('price')
        if price is not None:
            if price < 0:
                raise forms.ValidationError("Price cannot be negative.")
            if price > 10000:
                raise forms.ValidationError("Price cannot exceed $10,000.")
            if price == 0:
                raise forms.ValidationError("Price must be greater than zero.")
        return price
    
    def clean_duration(self):
        """Validate duration format."""
        duration = self.cleaned_data.get('duration')
        if duration:
            duration = duration.strip().lower()
            # Vérifier le format basique (nombre + unité)
            import re
            pattern = r'^\d+\s*(day|days|week|weeks|month|months|year|years)$'
            if not re.match(pattern, duration):
                raise forms.ValidationError(
                    "Invalid duration format. Use format like: '30 days', '3 months', '1 year'"
                )
        return duration
    
    def clean_features(self):
        """Validate features."""
        features = self.cleaned_data.get('features')
        if features:
            features = features.strip()
            # Vérifier qu'il y a au moins une feature
            feature_lines = [line.strip() for line in features.split('\n') if line.strip()]
            if len(feature_lines) < 1:
                raise forms.ValidationError("Please add at least one feature.")
            if len(feature_lines) > 20:
                raise forms.ValidationError("Cannot exceed 20 features.")
        return features