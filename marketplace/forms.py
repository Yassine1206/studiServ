from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Compte, EtatCompte, Prestataire, RoleUser, Utilisateur

User = get_user_model()


class EmailAuthForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={
            "autofocus": True,
            "class": "form-control",
            "placeholder": "votre@email.com",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Mot de passe",
        })


class InscriptionCompteForm(forms.Form):
    prenom = forms.CharField(max_length=100, label="Prénom",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Prénom"}))
    nom = forms.CharField(max_length=100, label="Nom",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}))
    email = forms.EmailField(label="Adresse e-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "votre@email.com"}))
    mot_de_passe = forms.CharField(label="Mot de passe", min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "8 caractères minimum"}))
    confirmation = forms.CharField(label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Répétez le mot de passe"}))
    role = forms.ChoiceField(label="Je suis",
        choices=[
            (RoleUser.PRESTATAIRE, "Prestataire — je propose des services"),
            (RoleUser.CONSOMMATEUR, "Consommateur — je cherche des services"),
        ],
        widget=forms.RadioSelect(attrs={"class": "role-radio"}))
    carte_etudiant = forms.CharField(label="Numéro de carte étudiante", max_length=100, required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex : 20241234"}))

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse e-mail est déjà utilisée.")
        return email

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("mot_de_passe")
        confirm = cleaned.get("confirmation")
        if pwd and confirm and pwd != confirm:
            self.add_error("confirmation", "Les mots de passe ne correspondent pas.")
        role = cleaned.get("role")
        carte = cleaned.get("carte_etudiant", "").strip()
        if role == RoleUser.PRESTATAIRE and not carte:
            self.add_error("carte_etudiant", "Le numéro de carte étudiante est requis pour les prestataires.")
        return cleaned