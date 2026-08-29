from django import forms
from django.contrib.auth.models import User

from .models import Charge, ChargeType, ExternalContributor, Period, Resident, WifiContribution


class ResidentCreationForm(forms.Form):
    """Crée un compte (username + mot de passe) pour un résident de la maison."""
    first_name = forms.CharField(label="Prénom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Nom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label="Nom d'utilisateur", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={"class": "form-control"}), help_text="Utilisé pour lui envoyer son reçu PDF par email.")
    telephone = forms.CharField(label="Téléphone", max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data.get("email", ""),
            password=data["password1"],
        )
        resident = Resident.objects.create(user=user, telephone=data.get("telephone", ""))
        return resident


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["annee", "mois"]
        widgets = {
            "annee": forms.NumberInput(attrs={"class": "form-control"}),
            "mois": forms.Select(attrs={"class": "form-select"}),
        }


class ChargeTypeForm(forms.ModelForm):
    class Meta:
        model = ChargeType
        fields = ["nom", "est_loyer", "est_wifi"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "est_loyer": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "est_wifi": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ChargeForm(forms.ModelForm):
    class Meta:
        model = Charge
        fields = ["charge_type", "montant", "note"]
        widgets = {
            "charge_type": forms.Select(attrs={"class": "form-select"}),
            "montant": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }


class ExternalContributorForm(forms.ModelForm):
    class Meta:
        model = ExternalContributor
        fields = ["nom", "telephone"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
        }


class WifiContributionForm(forms.ModelForm):
    class Meta:
        model = WifiContribution
        fields = ["contributor", "montant"]
        widgets = {
            "contributor": forms.Select(attrs={"class": "form-select"}),
            "montant": forms.NumberInput(attrs={"class": "form-control", "step": "1"}),
        }


class ResidentEditForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Nom", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label="Email", required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    telephone = forms.CharField(label="Téléphone", max_length=30, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    actif = forms.BooleanField(label="Résident actif", required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    new_password = forms.CharField(
        label="Nouveau mot de passe (laisser vide pour ne pas le changer)",
        required=False, widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )



