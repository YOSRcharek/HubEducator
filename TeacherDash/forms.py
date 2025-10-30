from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from etude.models import GroupeEtude, Meeting
from core.models import Speciality, Certificate, CertificatExercise

User = get_user_model()


# --------------------------
# Form to add a student
# --------------------------
class AddUserForm(UserCreationForm):
    # role is automatically set to 'student' and hidden
    role = forms.CharField(widget=forms.HiddenInput(), initial='student')
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


# --------------------------
# Form to edit a student
# --------------------------
class EditUserForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'profile_picture']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # empêcher doublons sauf pour le même utilisateur
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email already exists.")
        return email


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'start', 'end']
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows':3}),
        }

class SpecialityForm(forms.ModelForm):
    class Meta:
        model = Speciality
        fields = ['name', 'description']

class CertificateForm(forms.ModelForm):
    # cover_image is provided by uploadcare as a URL; make it optional on the form
    cover_image = forms.URLField(required=False, widget=forms.HiddenInput())
    speciality = forms.ModelChoiceField(
        queryset=Speciality.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

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
            'cover_image': forms.HiddenInput(),
        }
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 3:
            raise forms.ValidationError("The title must be at least 3 characters long.")
        return title

    def clean_description(self):
        desc = self.cleaned_data.get('description')
        if not desc or len(desc.strip()) < 10:
            raise forms.ValidationError("The description must contain at least 10 characters.")
        return desc

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
        self.fields['correct_answer'].required = False
        self.fields['correct_answer'].widget = forms.HiddenInput()

        # Populate available_options for QCU
        if self.instance and self.instance.pk:
            options = []
            if self.instance.option1:
                options.append(self.instance.option1)
            if self.instance.option2:
                options.append(self.instance.option2)
            if self.instance.option3:
                options.append(self.instance.option3)
            if self.instance.option4:
                options.append(self.instance.option4)
            self.available_options = options
        else:
            self.available_options = []

    class Meta:
        model = CertificatExercise
        fields = ['exercise_type', 'option1', 'option2', 'option3', 'option4', 'question', 'correct_answer']
        widgets = {
            'exercise_type': forms.Select(attrs={'class': 'form-select exercise-type-select'}),
            'option1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 1'}),
            'option2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Option 2'}),
            'question': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your question'}),
        }

    def clean_question(self):
        question = self.cleaned_data.get('question')
        if not question or len(question.strip()) < 5:
            raise forms.ValidationError("The question must contain at least 5 characters.")
        return question

    def clean(self):
        cleaned_data = super().clean()
        exercise_type = cleaned_data.get('exercise_type')
        if not exercise_type:
            raise forms.ValidationError("Exercise type is required.")
        correct_answer = cleaned_data.get('correct_answer')

        if exercise_type == 'qcu':
            options = [
                cleaned_data.get('option1'),
                cleaned_data.get('option2'),
                cleaned_data.get('option3'),
                cleaned_data.get('option4')
            ]
            options = [opt for opt in options if opt]

            if not options:
                raise forms.ValidationError("You must provide at least 2 options for a QCU exercise.")

            if not correct_answer:
                raise forms.ValidationError("Correct answer is required for QCU exercises.")
            if correct_answer not in options:
                raise forms.ValidationError("The correct answer must match one of the provided options.")

        elif exercise_type == 'truefalse':
            if not correct_answer:
                raise forms.ValidationError("Please select True or False for the correct answer.")

        elif exercise_type == 'text':
            if not correct_answer:
                raise forms.ValidationError("You must provide the correct answer for text exercises.")

        return cleaned_data
