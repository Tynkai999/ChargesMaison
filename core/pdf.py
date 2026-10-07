"""Génération de PDF pour les contributions de la maison, avec reportlab."""
import datetime
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
    HRFlowable
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("TitleFR", parent=STYLES["Heading1"], fontSize=18, textColor=colors.HexColor("#20335f"), spaceAfter=10)
SUBTITLE_STYLE = ParagraphStyle("SubtitleFR", parent=STYLES["Normal"], fontSize=12, textColor=colors.HexColor("#555555"), spaceAfter=20)
SECTION_STYLE = ParagraphStyle("SectionFR", parent=STYLES["Heading2"], fontSize=14, textColor=colors.HexColor("#20335f"), spaceBefore=15, spaceAfter=8)
NORMAL_STYLE = STYLES["Normal"]
RIGHT_STYLE = ParagraphStyle("RightFR", parent=STYLES["Normal"], alignment=TA_RIGHT)
CENTER_FOOTER = ParagraphStyle("CenterFooter", parent=STYLES["Normal"], alignment=TA_CENTER, fontSize=8, textColor=colors.grey)

def _montant(v):
    return f"{v:,.0f} FCFA".replace(",", " ")

def _statut_label(statut):
    return {"paye": "Payé", "partiel": "Partiel", "impaye": "Impayé"}.get(statut, statut.capitalize())

def build_resident_pdf(period, line, summary=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25 * mm, bottomMargin=25 * mm, rightMargin=20 * mm, leftMargin=20 * mm)
    resident = line["resident"]
    date_edition = datetime.date.today().strftime("%d/%m/%Y")

    elements = []

    # En-tête professionnel
    header_data = [
        [
            Paragraph("<b>GESTION DES CHARGES</b><br/>Maison Commune", NORMAL_STYLE),
            Paragraph(f"<b>Destinataire :</b> {resident}<br/><b>Date d'édition :</b> {date_edition}", RIGHT_STYLE)
        ]
    ]
    header_table = Table(header_data, colWidths=[85 * mm, 85 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 20),
    ]))
    elements.append(header_table)
    
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#20335f"), spaceAfter=15))

    # Titre du document
    elements.append(Paragraph(f"APPEL DE FONDS - {str(period).upper()}", TITLE_STYLE))
    
    presence_text = "Présent" if line['present'] else "Absent"
    elements.append(Paragraph(f"<b>Statut du résident pour la période :</b> {presence_text}", NORMAL_STYLE))
    elements.append(Spacer(1, 10 * mm))

    # Synthèse de la contribution
    elements.append(Paragraph("Synthèse de la contribution", SECTION_STYLE))
    data = [
        ["Désignation", "Montant"],
        ["Quote-part Loyer", _montant(line["rent_share"])],
        ["Quote-part Charges annexes", _montant(line["other_share"])],
        ["Total Mensuel", _montant(line["total"])],
    ]
    table = Table(data, colWidths=[120 * mm, 50 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20335f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#20335f")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f9fa")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)

    # Détail des charges
    breakdown = (summary or {}).get("charge_breakdown") or []
    if breakdown and line["present"]:
        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph("Détail des charges annexes (mutualisées)", SECTION_STYLE))
        
        detail_rows = [["Nature de la charge", "Montant total", "Base de répartition", "Quote-part"]]
        for item in breakdown:
            present_count = (summary or {}).get("present_count") or 1
            detail_rows.append([
                item["label"],
                _montant(item["montant_total"]),
                f"{present_count} présent(s)",
                _montant(item["part_par_present"]),
            ])
        detail_rows.append(["Total Charges Annexes", "", "", _montant(line["other_share"])])
        detail_table = Table(detail_rows, colWidths=[65 * mm, 35 * mm, 35 * mm, 35 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f9fa")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(detail_table)
        
        # Notes
        notes = [item["note"] for item in breakdown if item.get("note")]
        if notes:
            elements.append(Spacer(1, 4 * mm))
            for note in notes:
                elements.append(Paragraph(f"<i>* {note}</i>", ParagraphStyle("Note", parent=STYLES["Normal"], fontSize=8, textColor=colors.grey)))

    # Suivi des paiements
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph("Situation de compte", SECTION_STYLE))
    pay_data = [
        ["État d'avancement", _statut_label(line["statut_paiement"])],
        ["Montant réglé", _montant(line["montant_paye"])],
        ["Solde à régler", _montant(line["reste_a_payer"])],
    ]
    pay_table = Table(pay_data, colWidths=[120 * mm, 50 * mm])
    pay_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(pay_table)
    
    # Pied de page
    elements.append(Spacer(1, 20 * mm))
    elements.append(HRFlowable(width="50%", thickness=0.5, color=colors.grey, spaceAfter=5, hAlign='CENTER'))
    elements.append(Paragraph("Document généré informatiquement par le système de gestion des charges.<br/>Pour toute question, veuillez vous rapprocher de l'administration.", CENTER_FOOTER))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def build_period_pdf(summary):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25 * mm, bottomMargin=25 * mm, leftMargin=15*mm, rightMargin=15*mm)
    period = summary["period"]
    date_edition = datetime.date.today().strftime("%d/%m/%Y")

    elements = []

    # En-tête professionnel
    header_data = [
        [
            Paragraph("<b>GESTION DES CHARGES</b><br/>Maison Commune", NORMAL_STYLE),
            Paragraph(f"<b>Période :</b> {period}<br/><b>Édité le :</b> {date_edition}", RIGHT_STYLE)
        ]
    ]
    header_table = Table(header_data, colWidths=[90 * mm, 90 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#20335f"), spaceAfter=15))

    elements.append(Paragraph(f"ÉTAT RÉCAPITULATIF - {str(period).upper()}", TITLE_STYLE))
    
    # Résumé global
    summary_data = [
        ["Total Loyer", "Total Charges Annexes", "Solde Wifi Mutualisé"],
        [_montant(summary['rent_total']), _montant(summary['other_total']), _montant(summary['wifi_remainder'])]
    ]
    sum_table = Table(summary_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8f9fa")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(sum_table)
    elements.append(Spacer(1, 10 * mm))

    breakdown = summary.get("charge_breakdown") or []
    if breakdown:
        elements.append(Paragraph("Ventilation des charges", SECTION_STYLE))
        detail_rows = [["Nature de la charge", "Montant total", f"Base / présent ({summary['present_count']})"]]
        detail_rows.append([f"Loyer ({summary['total_residents']} résidents)", _montant(summary["rent_total"]), _montant(summary["rent_share"])])
        for item in breakdown:
            detail_rows.append([item["label"], _montant(item["montant_total"]), _montant(item["part_par_present"])])
        detail_table = Table(detail_rows, colWidths=[80 * mm, 50 * mm, 50 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("Répartition par résident", SECTION_STYLE))
    data = [["Résident", "Statut", "Loyer", "Charges", "Total", "Réglé", "État"]]
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
    data.append(["TOTAL", "", "", "", _montant(summary["grand_total"]), "", ""])

    table = Table(data, colWidths=[40 * mm, 18 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm, 22 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20335f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("ALIGN", (2, 0), (-2, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (-1, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8f9fa")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table)
    
    elements.append(Spacer(1, 20 * mm))
    elements.append(HRFlowable(width="50%", thickness=0.5, color=colors.grey, spaceAfter=5, hAlign='CENTER'))
    elements.append(Paragraph("Document interne généré informatiquement.", CENTER_FOOTER))

    doc.build(elements)
    buffer.seek(0)
    return buffer
