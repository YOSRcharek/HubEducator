from django import forms
from .models import User  # ou ton modèle custom
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
import re

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'phone', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-lg form-control-solid mb-3 mb-lg-0',
                'placeholder': 'Username'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg form-control-solid',
                'placeholder': 'Phone number'
            }),
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.png, .jpg, .jpeg'
            }),
        }


class EmailForm(forms.Form):
    email = forms.EmailField(label="New Email")
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("current_password")

        # Vérifier si l'email est différent de l'actuel
        if email and self.user and email == self.user.email:
            raise forms.ValidationError("Veuillez entrer une adresse différente de l'actuelle.")

        # Vérifier le mot de passe
        if password and not self.user.check_password(password):
            raise forms.ValidationError("Mot de passe actuel incorrect.")

        return cleaned_data


class PasswordForm(forms.Form):
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg form-control-solid'}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg form-control-solid'}),
        label="New Password"
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg form-control-solid'}),
        label="Confirm New Password"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        password = self.cleaned_data.get("current_password")
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Current password is incorrect.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_new_password")

        if new_password != confirm_password:
            raise forms.ValidationError("New password and confirmation do not match.")

        # Validate length and letters + numbers
        if new_password:
            if len(new_password) < 8:
                raise forms.ValidationError("New password must be at least 8 characters long.")
            if not re.search(r'[A-Za-z]', new_password) or not re.search(r'\d', new_password):
                raise forms.ValidationError("Password must contain at least one letter and one number.")

        return cleaned_data

    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg form-control-solid'}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg form-control-solid'}),
        label="New Password"
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg form-control-solid'}),
        label="Confirm New Password"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        password = self.cleaned_data.get("current_password")
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Current password is incorrect.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_new_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New password and confirmation do not match.")

        if new_password and len(new_password) < 8:
            raise forms.ValidationError("New password must be at least 8 characters long.")

        return cleaned_data
    
 