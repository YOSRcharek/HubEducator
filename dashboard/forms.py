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
            'speciality': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cover_image': forms.HiddenInput(),
        }
class CertificatExerciseForm(forms.ModelForm):
    correct_answer_truefalse = forms.ChoiceField(
        choices=[('True', 'True'), ('False', 'False')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    correct_answer_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    correct_answer_qcu = forms.ChoiceField(  # Changed from correct_answer_qcm to correct_answer_qcu
        choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3'), ('4', 'Option 4')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Options conditionnelles
    option3 = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 3'})
    )
    option4 = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 4'})
    )

    class Meta:
        model = CertificatExercise
        fields = ['exercise_type', 'option1', 'option2', 'option3', 'option4', 'question', 'correct_answer']
        widgets = {
            'exercise_type': forms.Select(attrs={'class': 'form-select exercise-type-select'}),
            'option1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 1'}),
            'option2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 2'}),
            'question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your question'}),
            'correct_answer': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir la bonne réponse selon le type (utile pour l'édition)
        instance = kwargs.get('instance') if 'instance' in kwargs else getattr(self, 'instance', None)
        if instance and getattr(instance, 'pk', None):
            exercise_type = getattr(instance, 'exercise_type', None)
            if exercise_type == 'truefalse':
                self.fields['correct_answer_truefalse'].initial = instance.correct_answer
            elif exercise_type == 'text':
                self.fields['correct_answer_text'].initial = instance.correct_answer
            elif exercise_type == 'qcu':
                # si stored as '1','2','3','4' ou la valeur correspondante
                self.fields['correct_answer_qcu'].initial = instance.correct_answer

    def clean(self):
        cleaned_data = super().clean()
        exercise_type = cleaned_data.get('exercise_type')

        if exercise_type == 'truefalse':
            cleaned_data['correct_answer'] = cleaned_data.get('correct_answer_truefalse')
        elif exercise_type == 'text':
            cleaned_data['correct_answer'] = cleaned_data.get('correct_answer_text')
        elif exercise_type == 'qcu':
            # Ensure a QCU correct answer is provided
            qcu = cleaned_data.get('correct_answer_qcu')
            if not qcu:
                raise ValidationError({'correct_answer_qcu': 'This field is required for QCU exercises.'})
            cleaned_data['correct_answer'] = qcu

        return cleaned_data
