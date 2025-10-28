from django import forms
from .models import GroupeEtude

class GroupeEtudeForm(forms.ModelForm):
    class Meta:
        model = GroupeEtude
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du groupe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optionnelle)'}),
        }