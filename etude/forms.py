from django import forms
from .models import GroupeEtude, ResourceEtude


class GroupeEtudeForm(forms.ModelForm):
    class Meta:
        model = GroupeEtude
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du groupe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optionnelle)'}),
        }

# teacher add ressource for etude
class ResourceEtudeForm(forms.ModelForm):
    class Meta:
        model = ResourceEtude
        fields = ['title', 'description', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows':3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }