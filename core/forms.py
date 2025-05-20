from django import forms
from .models import *

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['titre', 'description', 'importance', 'est_public']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-md'}),
            'importance': forms.Select(attrs={'class': 'w-full p-2 border rounded-md'}),
            'est_public': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300'}),
        }
        
        
class PieceForm(forms.ModelForm):
    class Meta:
        model = Piece
        fields = ['titre', 'description', 'numero', 'type', 'duree_vie', 'piece_date', 'fichier', 'est_public']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-md'}),
            'numero': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'type': forms.Select(attrs={'class': 'w-full p-2 border rounded-md'}),
            'duree_vie': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'piece_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded-md'}),
            'fichier': forms.ClearableFileInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'est_public': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300'}),
        }

class LoginForm(forms.Form):
    identifier = forms.CharField(label='Matricule ou Email')
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    
    
class UserRegistrationForm(forms.ModelForm):

    direction = forms.ModelChoiceField(
        queryset=Direction.objects.all(),
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md'}),
        required=True
    )
    service = forms.ModelChoiceField(
        queryset=Service.objects.none(),
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded-md'}),
        required=True
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded-md'})
    )
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded-md'})
    )

    class Meta:
        model = User
        fields = ['email', 'matricule', 'nom', 'prenom', 'direction', 'service', 'poste']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'matricule': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'nom': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'prenom': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-md'}),
            'poste': forms.Select(attrs={'class': 'w-full p-2 border rounded-md'}),
        }
        

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@gouv.bj'):
            raise forms.ValidationError("L'adresse email doit se terminer par @gouv.bj")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.none()
        self.fields['poste'].queryset = Poste.objects.none()

        if 'direction' in self.data:
            try:
                direction_id = self.data.get('direction')
                self.fields['service'].queryset = Service.objects.filter(direction_id=direction_id)
            except (ValueError, TypeError):
                pass
        
        if 'service' in self.data:
            try:
                service_id = self.data.get('service')
                self.fields['poste'].queryset = Poste.objects.filter(
                    service_id=service_id,
                    est_occupe=False
                )
            except (ValueError, TypeError):
                pass

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.statut = 'attente'
        if commit:
            user.save()
        return user