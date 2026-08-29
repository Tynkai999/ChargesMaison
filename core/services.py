"""Logique de calcul de la répartition des charges de la maison.

Règles :
- Le LOYER total est divisé par le nombre TOTAL de résidents actifs
  (présents ou absents) : tout le monde paie sa part de loyer.
- Les AUTRES charges (électricité, eau, etc.) sont divisées uniquement
  entre les résidents PRÉSENTS sur la période.
- Le WIFI : on part du montant total de l'abonnement, on soustrait la somme
  des contributions des externes, et le reste est ajouté au pot des
  "autres charges" (donc réparti lui aussi entre les présents uniquement).
"""
from decimal import Decimal, ROUND_HALF_UP

TWOPLACES = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def compute_period_summary(period):
    """Retourne un dict complet avec le détail du calcul pour une période."""
    from .models import Payment, Resident

    charges = list(period.charges.select_related("charge_type"))
    rent_total = sum((c.montant for c in charges if c.charge_type.est_loyer), Decimal("0"))
    wifi_total = sum((c.montant for c in charges if c.charge_type.est_wifi), Decimal("0"))
    other_total = sum(
        (c.montant for c in charges if not c.charge_type.est_loyer and not c.charge_type.est_wifi),
        Decimal("0"),
    )

    residents = list(Resident.objects.filter(actif=True).select_related("user"))
    total_residents = len(residents)

    presence_map = {p.resident_id: p.present for p in period.presences.select_related("resident")}
    # Par défaut, un résident sans enregistrement de présence est considéré présent.
    present_residents = [r for r in residents if presence_map.get(r.id, True)]
    present_count = len(present_residents)

    external_contrib_total = sum(
        (w.montant for w in period.wifi_contributions.select_related("contributor")), Decimal("0")
    )
    wifi_remainder = wifi_total - external_contrib_total
    if wifi_remainder < 0:
        wifi_remainder = Decimal("0")

    other_pool = other_total + wifi_remainder

    rent_share = _q(rent_total / total_residents) if total_residents else Decimal("0")
    other_share = _q(other_pool / present_count) if present_count else Decimal("0")

    # Détail des "autres charges" ligne par ligne (électricité, eau, ménage, etc.)
    # + le solde wifi restant après déduction des contributions externes,
    # afin que chaque résident sache exactement ce qu'il paie.
    charge_breakdown = []
    for c in charges:
        if c.charge_type.est_loyer or c.charge_type.est_wifi:
            continue
        part = _q(c.montant / present_count) if present_count else Decimal("0")
        charge_breakdown.append({
            "label": c.charge_type.nom,
            "montant_total": c.montant,
            "part_par_present": part,
            "note": c.note,
        })
    if wifi_total > 0:
        charge_breakdown.append({
            "label": "Internet / Wifi (solde après contributions externes)",
            "montant_total": wifi_remainder,
            "part_par_present": _q(wifi_remainder / present_count) if present_count else Decimal("0"),
            "note": (
                f"Abonnement {_q(wifi_total)} FCFA − contributions externes {_q(external_contrib_total)} FCFA"
            ),
        })

    payment_map = {p.resident_id: p for p in period.payments.select_related("resident")}

    lines = []
    for r in residents:
        present = presence_map.get(r.id, True)
        r_other_share = other_share if present else Decimal("0")
        total = rent_share + r_other_share

        payment = payment_map.get(r.id)
        montant_paye = payment.montant_paye if payment else Decimal("0")
        paye = payment.paye if payment else False
        if paye or montant_paye >= total and total > 0:
            statut_paiement = "paye"
        elif montant_paye > 0:
            statut_paiement = "partiel"
        else:
            statut_paiement = "impaye"

        lines.append({
            "resident": r,
            "present": present,
            "rent_share": rent_share,
            "other_share": r_other_share,
            "total": total,
            "payment": payment,
            "montant_paye": montant_paye,
            "paye": paye,
            "statut_paiement": statut_paiement,
            "reste_a_payer": max(total - montant_paye, Decimal("0")),
        })

    grand_total = sum((l["total"] for l in lines), Decimal("0"))

    return {
        "period": period,
        "charges": charges,
        "rent_total": rent_total,
        "wifi_total": wifi_total,
        "other_total": other_total,
        "external_contrib_total": external_contrib_total,
        "wifi_remainder": wifi_remainder,
        "other_pool": other_pool,
        "total_residents": total_residents,
        "present_count": present_count,
        "absent_count": total_residents - present_count,
        "rent_share": rent_share,
        "other_share": other_share,
        "charge_breakdown": charge_breakdown,
        "lines": lines,
        "grand_total": grand_total,
    }
