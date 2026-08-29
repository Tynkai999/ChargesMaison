"""Génération de PDF pour les contributions de la maison, avec reportlab.

Deux fonctions principales :
- build_resident_pdf(period, line) : reçu individuel d'un résident pour une période.
- build_period_pdf(summary)        : récapitulatif de tous les résidents pour une période.

Les deux renvoient un objet BytesIO prêt à être envoyé en réponse HTTP ou en
pièce jointe d'email.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("TitleFR", parent=STYLES["Title"], fontSize=18, spaceAfter=4)
SUBTITLE_STYLE = ParagraphStyle("SubtitleFR", parent=STYLES["Normal"], fontSize=11, textColor=colors.grey, spaceAfter=16)
SECTION_STYLE = ParagraphStyle("SectionFR", parent=STYLES["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6)
NORMAL_STYLE = STYLES["Normal"]


def _montant(v):
    return f"{v:,.0f} FCFA".replace(",", " ")


def _statut_label(statut):
    return {"paye": "Payé", "partiel": "Partiel", "impaye": "Impayé"}.get(statut, statut)


def build_resident_pdf(period, line, summary=None):
    """Reçu individuel d'un résident pour une période donnée.
    `line` est un des éléments de summary['lines'] (voir services.py).
    `summary` (optionnel) permet d'afficher le détail ligne par ligne des
    « autres charges » (électricité, eau, solde wifi, etc.)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25 * mm, bottomMargin=20 * mm)
    resident = line["resident"]

    elements = [
        Paragraph("Charges Maison", TITLE_STYLE),
        Paragraph(f"Reçu de contribution &mdash; {period}", SUBTITLE_STYLE),
        Paragraph(f"<b>Résident :</b> {resident}", NORMAL_STYLE),
        Paragraph(f"<b>Statut de présence :</b> {'Présent' if line['present'] else 'Absent'}", NORMAL_STYLE),
        Spacer(1, 10 * mm),
        Paragraph("Détail de la contribution", SECTION_STYLE),
    ]

    data = [
        ["Élément", "Montant"],
        ["Part de loyer", _montant(line["rent_share"])],
        ["Part des autres charges (dont solde wifi)", _montant(line["other_share"])],
        ["Total à payer", _montant(line["total"])],
    ]
    table = Table(data, colWidths=[110 * mm, 50 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20335f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f6f8")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    # Détail des "autres charges" type par type, pour que le résident sache
    # précisément ce qu'il paie (électricité, eau, ménage, solde wifi, etc.)
    breakdown = (summary or {}).get("charge_breakdown") or []
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Détail des autres charges", SECTION_STYLE))
    if not line["present"]:
        elements.append(Paragraph(
            "Résident absent ce mois-ci : seule la part de loyer est due, "
            "les autres charges ci-dessous sont réparties uniquement entre les résidents présents.",
            NORMAL_STYLE,
        ))
        detail_rows = [["Type de charge", "Montant total de la maison"]]
        for item in breakdown:
            detail_rows.append([item["label"], _montant(item["montant_total"])])
        detail_table = Table(detail_rows, colWidths=[110 * mm, 50 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(detail_table)
    elif breakdown:
        detail_rows = [["Type de charge", "Montant total", "Nb. présents", "Votre part"]]
        for item in breakdown:
            present_count = (summary or {}).get("present_count") or 1
            detail_rows.append([
                item["label"],
                _montant(item["montant_total"]),
                str(present_count),
                _montant(item["part_par_present"]),
            ])
        detail_rows.append(["Total « autres charges »", "", "", _montant(line["other_share"])])
        detail_table = Table(detail_rows, colWidths=[70 * mm, 35 * mm, 25 * mm, 30 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f6f8")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(detail_table)
        # Notes de bas de tableau (ex : détail du calcul du solde wifi)
        notes = [item["note"] for item in breakdown if item.get("note")]
        if notes:
            elements.append(Spacer(1, 3 * mm))
            for note in notes:
                elements.append(Paragraph(f"<font size=8 color='grey'>{note}</font>", NORMAL_STYLE))
    else:
        elements.append(Paragraph("Aucune autre charge enregistrée pour cette période.", NORMAL_STYLE))

    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Suivi du paiement", SECTION_STYLE))
    pay_data = [
        ["Statut", _statut_label(line["statut_paiement"])],
        ["Montant versé", _montant(line["montant_paye"])],
        ["Reste à payer", _montant(line["reste_a_payer"])],
    ]
    pay_table = Table(pay_data, colWidths=[110 * mm, 50 * mm])
    pay_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(pay_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def build_period_pdf(summary):
    """Récapitulatif de la contribution de tous les résidents pour une période."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25 * mm, bottomMargin=20 * mm)
    period = summary["period"]

    elements = [
        Paragraph("Charges Maison", TITLE_STYLE),
        Paragraph(f"Récapitulatif des contributions &mdash; {period}", SUBTITLE_STYLE),
        Paragraph(
            f"Loyer total : {_montant(summary['rent_total'])} &nbsp;|&nbsp; "
            f"Autres charges : {_montant(summary['other_total'])} &nbsp;|&nbsp; "
            f"Solde wifi réparti : {_montant(summary['wifi_remainder'])}",
            NORMAL_STYLE,
        ),
        Spacer(1, 6 * mm),
    ]

    breakdown = summary.get("charge_breakdown") or []
    if breakdown:
        elements.append(Paragraph("Détail des charges de la maison", SECTION_STYLE))
        detail_rows = [["Type de charge", "Montant total", f"Part / présent ({summary['present_count']})"]]
        detail_rows.append(["Loyer (÷ " + str(summary["total_residents"]) + " résidents)", _montant(summary["rent_total"]), _montant(summary["rent_share"])])
        for item in breakdown:
            detail_rows.append([item["label"], _montant(item["montant_total"]), _montant(item["part_par_present"])])
        detail_table = Table(detail_rows, colWidths=[80 * mm, 45 * mm, 40 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Contribution par résident", SECTION_STYLE))
    data = [["Résident", "Présence", "Loyer", "Autres charges", "Total", "Payé", "Statut"]]
    for line in summary["lines"]:
        data.append([
            str(line["resident"]),
            "Présent" if line["present"] else "Absent",
            _montant(line["rent_share"]),
            _montant(line["other_share"]),
            _montant(line["total"]),
            _montant(line["montant_paye"]),
            _statut_label(line["statut_paiement"]),
        ])
    data.append(["Total", "", "", "", _montant(summary["grand_total"]), "", ""])

    table = Table(data, colWidths=[38 * mm, 20 * mm, 24 * mm, 30 * mm, 22 * mm, 22 * mm, 20 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20335f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("ALIGN", (2, 0), (-2, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f6f8")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
