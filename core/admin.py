from django.contrib import admin

from .models import Charge, ChargeType, ExternalContributor, Payment, Period, Presence, Resident, WifiContribution


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = ("user", "telephone", "actif", "date_ajout")
    list_filter = ("actif",)
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(ExternalContributor)
class ExternalContributorAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone")
    search_fields = ("nom",)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("__str__", "annee", "mois", "cloturee")
    list_filter = ("annee", "cloturee")


@admin.register(ChargeType)
class ChargeTypeAdmin(admin.ModelAdmin):
    list_display = ("nom", "est_loyer", "est_wifi")


@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = ("period", "charge_type", "montant", "note")
    list_filter = ("period", "charge_type")


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ("resident", "period", "present")
    list_filter = ("period", "present")


@admin.register(WifiContribution)
class WifiContributionAdmin(admin.ModelAdmin):
    list_display = ("period", "contributor", "montant")
    list_filter = ("period",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("period", "resident", "paye", "montant_paye", "date_paiement")
    list_filter = ("period", "paye")
    search_fields = ("resident__user__username", "resident__user__first_name", "resident__user__last_name")
