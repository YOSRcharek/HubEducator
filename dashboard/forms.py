from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.forms import modelformset_factory
from core.models import Speciality, Certificate, CertificatExercise


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

class SpecialityForm(forms.ModelForm):
    class Meta:
        model = Speciality
        fields = ['name', 'description']
class CertificateForm(forms.ModelForm):
    # cover_image is provided by uploadcare as a URL; make it optional on the form
    cover_image = forms.URLField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Certificate
        fields = ['title', 'description', 'speciality', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter certificate title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe the certificate...'
            }),
            'speciality': forms.Select(attrs={'class': 'form-select'}),
            'cover_image': forms.HiddenInput(),
        }

class CertificatExerciseForm(forms.ModelForm):
    option3 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 3'})
    )
    option4 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 4'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make correct_answer optional because template handles it via JS select/input
        self.fields['correct_answer'].required = False

        # Force correct_answer field to use hidden input; template will show select/input
        self.fields['correct_answer'].widget = forms.HiddenInput()

    class Meta:
        model = CertificatExercise
        fields = ['exercise_type', 'option1', 'option2', 'option3', 'option4', 'question', 'correct_answer']
        widgets = {
            'exercise_type': forms.Select(attrs={'class': 'form-select exercise-type-select'}),
            'option1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 1'}),
            'option2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 2'}),
            'question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your question'}),
        }

    def get_options(self):
        options = []
        for i in range(1, 5):
            val = self.initial.get(f'option{i}', '') or getattr(self.instance, f'option{i}', '') if self.instance else ''
            if val:
                options.append(val)
        return options

    def clean(self):
        cleaned_data = super().clean()
        exercise_type = cleaned_data.get('exercise_type')
        correct_answer = cleaned_data.get('correct_answer')

        if exercise_type == 'qcu':
            options = [opt for opt in [
                cleaned_data.get('option1'),
                cleaned_data.get('option2'),
                cleaned_data.get('option3'),
                cleaned_data.get('option4')
            ] if opt]  # ignore les options vides

            if not correct_answer:
                raise forms.ValidationError("Correct answer is required for QCU exercises.")

            if correct_answer not in options:
                raise forms.ValidationError("The correct answer must be one of the provided options.")

        elif exercise_type == 'truefalse':
            if not correct_answer:
                raise forms.ValidationError("Correct answer is required for True/False exercises.")
            if correct_answer not in ['True', 'False']:
                raise forms.ValidationError("For True/False exercises, the correct answer must be 'True' or 'False'.")

        elif exercise_type == 'text':
            if not correct_answer:
                raise forms.ValidationError("Correct answer is required for Text exercises.")

        return cleaned_data
