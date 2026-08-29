from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


MOIS_CHOICES = [
    (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
    (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
    (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre"),
]


class Resident(models.Model):
    """Une personne de la maison (résident officiel).

    Un résident paie toujours sa part du loyer (le total du loyer est
    divisé par le nombre total de résidents), et paie en plus sa part des
    autres charges uniquement s'il est présent sur la période.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="resident")
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    actif = models.BooleanField("Actif", default=True, help_text="Décochez pour retirer un résident sans supprimer son historique.")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Résident"
        verbose_name_plural = "Résidents"
        ordering = ["user__first_name", "user__last_name"]

    def __str__(self):
        full = self.user.get_full_name()
        return full if full else self.user.username


class ExternalContributor(models.Model):
    """Une personne qui ne vit PAS dans la maison mais qui contribue
    uniquement à l'abonnement internet (wifi)."""
    nom = models.CharField("Nom", max_length=150)
    telephone = models.CharField("Téléphone", max_length=10, blank=True)

    class Meta:
        verbose_name = "Contributeur externe (wifi)"
        verbose_name_plural = "Contributeurs externes (wifi)"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Period(models.Model):
    """Une période (mois/année) sur laquelle on calcule les charges."""
    annee = models.PositiveIntegerField("Année")
    mois = models.PositiveSmallIntegerField("Mois", choices=MOIS_CHOICES)
    cloturee = models.BooleanField("Clôturée", default=False, help_text="Une période clôturée n'est plus modifiable dans l'interface.")

    class Meta:
        verbose_name = "Période"
        verbose_name_plural = "Périodes"
        unique_together = ("annee", "mois")
        ordering = ["-annee", "-mois"]

    def __str__(self):
        return f"{self.get_mois_display()} {self.annee}"


class ChargeType(models.Model):
    """Type de charge : Loyer, Électricité, Eau, Wifi, Ménage, etc."""
    nom = models.CharField("Nom", max_length=100, unique=True)
    est_loyer = models.BooleanField(
        "C'est le loyer",
        default=False,
        help_text="Coché uniquement pour le type 'Loyer' : réparti entre TOUS les résidents (présents ou non).",
    )
    est_wifi = models.BooleanField(
        "C'est l'abonnement wifi",
        default=False,
        help_text="Coché uniquement pour le type 'Internet/Wifi' : les contributions externes en sont déduites avant répartition.",
    )

    class Meta:
        verbose_name = "Type de charge"
        verbose_name_plural = "Types de charge"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Charge(models.Model):
    """Une dépense pour une période donnée (montant du loyer du mois,
    facture d'électricité du mois, abonnement wifi du mois, etc.)."""
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="charges")
    charge_type = models.ForeignKey(ChargeType, on_delete=models.PROTECT, related_name="charges")
    montant = models.DecimalField("Montant (FCFA)", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    note = models.CharField("Note", max_length=255, blank=True)

    class Meta:
        verbose_name = "Charge"
        verbose_name_plural = "Charges"
        ordering = ["charge_type__nom"]

    def __str__(self):
        return f"{self.charge_type} - {self.montant} FCFA ({self.period})"


class Presence(models.Model):
    """Statut de présence d'un résident sur une période donnée.
    Par défaut (aucun enregistrement), le résident est considéré présent."""
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="presences")
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="presences")
    present = models.BooleanField("Présent dans la maison", default=True)

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        unique_together = ("resident", "period")

    def __str__(self):
        etat = "présent" if self.present else "absent"
        return f"{self.resident} - {self.period} ({etat})"


class WifiContribution(models.Model):
    """Contribution d'une personne externe à l'abonnement wifi, pour une période."""
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="wifi_contributions")
    contributor = models.ForeignKey(ExternalContributor, on_delete=models.CASCADE, related_name="contributions")
    montant = models.DecimalField("Montant (FCFA)", max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "Contribution wifi (externe)"
        verbose_name_plural = "Contributions wifi (externes)"
        unique_together = ("period", "contributor")

    def __str__(self):
        return f"{self.contributor} - {self.montant} FCFA ({self.period})"


class Payment(models.Model):
    """Suivi du paiement d'un résident pour une période donnée.
    Rempli par l'administration (case à cocher + montant réellement versé)."""
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name="payments")
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="payments")
    paye = models.BooleanField("Payé", default=False)
    montant_paye = models.DecimalField(
        "Montant payé (FCFA)", max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    date_paiement = models.DateField("Date du paiement", null=True, blank=True)
    note = models.CharField("Note", max_length=255, blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        unique_together = ("period", "resident")

    def __str__(self):
        return f"{self.resident} - {self.period} : {self.montant_paye} FCFA"
