from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    ChargeForm,
    ChargeTypeForm,
    ExternalContributorForm,
    PeriodForm,
    ResidentCreationForm,
    ResidentEditForm,
    WifiContributionForm,
)
from .models import Charge, ChargeType, ExternalContributor, Payment, Period, Presence, Resident, WifiContribution
from .pdf import build_period_pdf, build_resident_pdf
from .services import compute_period_summary

is_staff = user_passes_test(lambda u: u.is_staff)


def _line_for_resident(summary, resident_id):
    for line in summary["lines"]:
        if line["resident"].id == resident_id:
            return line
    return None


def _resident_pdf_response(period, line, summary, inline=True):
    buffer = build_resident_pdf(period, line, summary)
    filename = f"contribution_{line['resident'].user.username}_{period.annee}_{period.mois:02d}.pdf"
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    disposition = "inline" if inline else "attachment"
    response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    return response


@login_required
def dashboard(request):
    periods = Period.objects.all()[:6]
    summaries = [compute_period_summary(p) for p in periods]
    return render(request, "core/dashboard.html", {"summaries": summaries})


@login_required
def period_list(request):
    periods = Period.objects.all()
    return render(request, "core/period_list.html", {"periods": periods})


@staff_member_required
def period_add(request):
    if request.method == "POST":
        form = PeriodForm(request.POST)
        if form.is_valid():
            period = form.save()
            messages.success(request, f"Période « {period} » créée.")
            return redirect("period_detail", pk=period.pk)
    else:
        form = PeriodForm()
    return render(request, "core/period_form.html", {"form": form})


@staff_member_required
def period_edit(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if request.method == "POST":
        form = PeriodForm(request.POST, instance=period)
        if form.is_valid():
            period = form.save(commit=False)
            period.cloturee = request.POST.get("cloturee") == "on"
            period.save()
            messages.success(request, "Période modifiée.")
            return redirect("period_detail", pk=period.pk)
    else:
        form = PeriodForm(instance=period)
    return render(request, "core/period_edit.html", {"form": form, "period": period})

@login_required
def period_detail(request, pk):
    period = get_object_or_404(Period, pk=pk)
    summary = compute_period_summary(period)
    charge_form = ChargeForm()
    wifi_form = WifiContributionForm()
    residents = Resident.objects.filter(actif=True).select_related("user")
    presence_map = {p.resident_id: p.present for p in period.presences.all()}
    presence_rows = [
        {"resident": r, "present": presence_map.get(r.id, True)} for r in residents
    ]
    return render(request, "core/period_detail.html", {
        "period": period,
        "summary": summary,
        "charge_form": charge_form,
        "wifi_form": wifi_form,
        "presence_rows": presence_rows,
    })

@staff_member_required
def period_delete(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if request.method == "POST":
        period.delete()
        messages.success(request, "Période supprimée.")
        return redirect("period_list")
    return render(request, "core/period_delete.html", {"period": period})


@login_required
def charge_add(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if request.method == "POST":
        form = ChargeForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.period = period
            charge.save()
            messages.success(request, "Charge ajoutée.")
        else:
            messages.error(request, "Impossible d'ajouter la charge : vérifiez le formulaire.")
    return redirect("period_detail", pk=period.pk)

# modifier les charges existantes       
@login_required
def charge_edit(request, pk, charge_id):
    period = get_object_or_404(Period, pk=pk)
    charge = get_object_or_404(Charge, pk=charge_id, period=period)
    if request.method == "POST":
        form = ChargeForm(request.POST, instance=charge)
        if form.is_valid():
            form.save()
            messages.success(request, "Charge modifiée.")
            return redirect("period_detail", pk=period.pk)
    else:
        form = ChargeForm(instance=charge)
    return render(request, "core/charge_edit.html", {"form": form, "period": period, "charge": charge})

@login_required
def charge_delete(request, pk, charge_id):
    period = get_object_or_404(Period, pk=pk)
    charge = get_object_or_404(Charge, pk=charge_id, period=period)
    if request.method == "POST":
        charge.delete()
        messages.success(request, "Charge supprimée.")
    return redirect("period_detail", pk=period.pk)


@login_required
def presence_update(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if request.method == "POST":
        residents = Resident.objects.filter(actif=True)
        for r in residents:
            present = request.POST.get(f"present_{r.id}") == "on"
            Presence.objects.update_or_create(resident=r, period=period, defaults={"present": present})
        messages.success(request, "Présences mises à jour.")
    return redirect("period_detail", pk=period.pk)


@login_required
def wifi_contribution_add(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if request.method == "POST":
        form = WifiContributionForm(request.POST)
        if form.is_valid():
            wc = form.save(commit=False)
            wc.period = period
            try:
                wc.save()
                messages.success(request, "Contribution wifi ajoutée.")
            except Exception:
                messages.error(request, "Ce contributeur a déjà une contribution sur cette période.")
        else:
            messages.error(request, "Impossible d'ajouter la contribution : vérifiez le formulaire.")
    return redirect("period_detail", pk=period.pk)


@login_required
def wifi_contribution_edit(request, pk, wc_id):
    period = get_object_or_404(Period, pk=pk)
    wc = get_object_or_404(WifiContribution, pk=wc_id, period=period)
    if request.method == "POST":
        form = WifiContributionForm(request.POST, instance=wc)
        if form.is_valid():
            form.save()
            messages.success(request, "Contribution wifi modifiée.")
            return redirect("period_detail", pk=period.pk)
    else:
        form = WifiContributionForm(instance=wc)
    return render(request, "core/wifi_contribution_edit.html", {"form": form, "period": period, "wc": wc})

@login_required
def wifi_contribution_delete(request, pk, wc_id):
    period = get_object_or_404(Period, pk=pk)
    wc = get_object_or_404(WifiContribution, pk=wc_id, period=period)
    if request.method == "POST":
        wc.delete()
        messages.success(request, "Contribution wifi supprimée.")
    return redirect("period_detail", pk=period.pk)


@login_required
def contributor_list(request):
    contributors = ExternalContributor.objects.all()
    if request.method == "POST":
        form = ExternalContributorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contributeur externe ajouté.")
            return redirect("contributor_list")
    else:
        form = ExternalContributorForm()
    return render(request, "core/contributor_list.html", {"contributors": contributors, "form": form})


@login_required
def contributor_edit(request, pk):
    contributor = get_object_or_404(ExternalContributor, pk=pk)
    if request.method == "POST":
        form = ExternalContributorForm(request.POST, instance=contributor)
        if form.is_valid():
            form.save()
            messages.success(request, "Contributeur modifié.")
            return redirect("contributor_list")
    else:
        form = ExternalContributorForm(instance=contributor)
    return render(request, "core/contributor_edit.html", {"form": form, "contributor": contributor})


@login_required
def contributor_delete(request, pk):
    contributor = get_object_or_404(ExternalContributor, pk=pk)
    if request.method == "POST":
        contributor.delete()
        messages.success(request, "Contributeur externe supprimé.")
    return redirect("contributor_list")


@login_required
def charge_type_list(request):
    charge_types = ChargeType.objects.all()
    if request.method == "POST":
        form = ChargeTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Type de charge ajouté.")
            return redirect("charge_type_list")
    else:
        form = ChargeTypeForm()
    return render(request, "core/charge_type_list.html", {"charge_types": charge_types, "form": form})

@login_required
def charge_type_edit(request, pk):
    charge_type = get_object_or_404(ChargeType, pk=pk)
    if request.method == "POST":
        form = ChargeTypeForm(request.POST, instance=charge_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Type de charge modifié.")
            return redirect("charge_type_list")
    else:
        form = ChargeTypeForm(instance=charge_type)
    return render(request, "core/charge_type_edit.html", {"form": form, "charge_type": charge_type})


@login_required
def charge_type_delete(request, pk):
    charge_type = get_object_or_404(ChargeType, pk=pk)
    if request.method == "POST":
        charge_type.delete()
        messages.success(request, "Type de charge supprimé.")
    return redirect("charge_type_list")


@login_required
def resident_list(request):
    residents = Resident.objects.select_related("user").all()
    return render(request, "core/resident_list.html", {"residents": residents})


@is_staff
def resident_add(request):
    if request.method == "POST":
        form = ResidentCreationForm(request.POST)
        if form.is_valid():
            resident = form.save()
            messages.success(request, f"Compte créé pour {resident}.")
            return redirect("resident_list")
    else:
        form = ResidentCreationForm()
    return render(request, "core/resident_form.html", {"form": form})

@is_staff
def resident_edit(request, pk):
    resident = get_object_or_404(Resident, pk=pk)
    if request.method == "POST":
        form = ResidentEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = resident.user
            user.first_name = data["first_name"]
            user.last_name = data["last_name"]
            user.email = data["email"]
            if data["new_password"]:
                user.set_password(data["new_password"])
            user.save()
            resident.telephone = data["telephone"]
            resident.actif = data["actif"]
            resident.save()
            messages.success(request, f"Informations de {resident} mises à jour.")
            return redirect("resident_list")
    else:
        form = ResidentEditForm(initial={
            "first_name": resident.user.first_name,
            "last_name": resident.user.last_name,
            "email": resident.user.email,
            "telephone": resident.telephone,
            "actif": resident.actif,
        })
    return render(request, "core/resident_edit.html", {"form": form, "resident": resident})


@login_required
def contribution_pdf(request, pk, resident_id):
    """Télécharge le reçu PDF d'un résident pour une période.
    Un résident ne peut télécharger que le sien ; l'administration peut tout voir."""
    period = get_object_or_404(Period, pk=pk)
    resident = get_object_or_404(Resident, pk=resident_id)

    own_resident = getattr(request.user, "resident", None)
    if not request.user.is_staff and (own_resident is None or own_resident.id != resident.id):
        raise Http404("Vous ne pouvez pas accéder au reçu d'un autre résident.")

    summary = compute_period_summary(period)
    line = _line_for_resident(summary, resident.id)
    if line is None:
        raise Http404("Résident introuvable pour cette période.")

    return _resident_pdf_response(period, line, summary, inline=False)


@login_required
def period_pdf_all(request, pk):
    """Télécharge le récapitulatif PDF de tous les résidents pour une période."""
    period = get_object_or_404(Period, pk=pk)
    summary = compute_period_summary(period)
    buffer = build_period_pdf(summary)
    filename = f"recapitulatif_{period.annee}_{period.mois:02d}.pdf"
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@is_staff
def contribution_pdf_send(request, pk, resident_id):
    """Envoie le reçu PDF d'un résident par email (bouton 'Envoyer' réservé à l'administration)."""
    period = get_object_or_404(Period, pk=pk)
    resident = get_object_or_404(Resident, pk=resident_id)
    summary = compute_period_summary(period)
    line = _line_for_resident(summary, resident.id)
    if line is None:
        raise Http404("Résident introuvable pour cette période.")

    if not resident.user.email:
        messages.error(request, f"{resident} n'a pas d'adresse email enregistrée. Ajoutez-la via l'admin Django avant d'envoyer.")
        return redirect("period_detail", pk=period.pk)

    buffer = build_resident_pdf(period, line, summary)
    filename = f"contribution_{resident.user.username}_{period.annee}_{period.mois:02d}.pdf"

    email = EmailMessage(
        subject=f"Votre contribution pour {period}",
        body=(
            f"Bonjour {resident},\n\n"
            f"Voici le détail de votre contribution pour {period} : {line['total']:.0f} FCFA "
            f"(loyer : {line['rent_share']:.0f} FCFA, autres charges : {line['other_share']:.0f} FCFA).\n\n"
            "Vous trouverez le reçu détaillé en pièce jointe.\n\n"
            "Merci."
        ),
        to=[resident.user.email],
    )
    email.attach(filename, buffer.read(), "application/pdf")
    try:
        email.send()
        messages.success(request, f"Reçu envoyé par email à {resident} ({resident.user.email}).")
    except Exception as exc:
        messages.error(request, f"Échec de l'envoi de l'email : {exc}")

    return redirect("period_detail", pk=period.pk)


@is_staff
def payment_tracking(request, pk):
    """Page d'administration : cocher qui a payé, combien, et suivre les paiements."""
    period = get_object_or_404(Period, pk=pk)

    if request.method == "POST":
        residents = Resident.objects.filter(actif=True)
        for r in residents:
            paye = request.POST.get(f"paye_{r.id}") == "on"
            montant_raw = request.POST.get(f"montant_{r.id}", "0").strip() or "0"
            date_raw = request.POST.get(f"date_{r.id}", "").strip()
            note = request.POST.get(f"note_{r.id}", "").strip()
            try:
                montant = Decimal(montant_raw)
            except InvalidOperation:
                montant = Decimal("0")
            date_paiement = date_raw or None
            Payment.objects.update_or_create(
                period=period, resident=r,
                defaults={
                    "paye": paye,
                    "montant_paye": montant,
                    "date_paiement": date_paiement,
                    "note": note,
                },
            )
        messages.success(request, "Suivi des paiements mis à jour.")
        return redirect("payment_tracking", pk=period.pk)

    summary = compute_period_summary(period)
    return render(request, "core/payment_tracking.html", {"period": period, "summary": summary})


@login_required
def my_contributions(request):
    resident = getattr(request.user, "resident", None)
    rows = []
    if resident:
        periods = Period.objects.all()
        for period in periods:
            summary = compute_period_summary(period)
            for line in summary["lines"]:
                if line["resident"].id == resident.id:
                    rows.append({"period": period, **line})
    return render(request, "core/my_contributions.html", {"rows": rows, "resident": resident})
