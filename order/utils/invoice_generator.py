from io import BytesIO
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from django.conf import settings
from decimal import Decimal
import os


def generate_invoice(order):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleH = styles["Heading1"]

    # ========== HEADER ==========
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'LeMaillot_final.webp')
    if os.path.exists(logo_path):
        img = Image(logo_path, width=40 * mm, height=40 * mm)
        img.hAlign = 'RIGHT'
        elements.append(img)

    elements.append(Paragraph("<b>COMMANDE</b>", styleH))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"Commande n° {order.order_number}", styleN))
    elements.append(Paragraph(f"Date : {order.created_at.strftime('%d/%m/%Y')}", styleN))
    elements.append(Spacer(1, 16))

    # ========== FROM / TO ==========
    from_info = [
        Paragraph("<b>LEMAILLOT</b>", styleN),
        Paragraph("contact@lemaillot.bj", styleN),
        Paragraph("Cotonou, Bénin", styleN),
    ]

    to_info = [
        Paragraph("<b>À L’ATTENTION DE</b>", styleN),
        Paragraph(f"{order.customer.first_name} {order.customer.last_name}", styleN),
        Paragraph(order.customer.email or "", styleN),
        Paragraph(order.delivery_address or "Adresse non renseignée", styleN),
    ]

    table = Table([ [from_info, to_info] ], colWidths=[250, 250])
    elements.append(table)
    elements.append(Spacer(1, 20))

    # ========== TABLE DES PRODUITS ==========
    data = [["DESCRIPTION", "PRIX", "QUANTITÉ", "TOTAL"]]
    total = Decimal("0.0")

    for item in order.items.all():
        price = item.price
        quantity = item.quantity
        line_total = price * quantity
        total += line_total

        data.append([
            item.product.product_name,
            f"{price:.0f} FCFA",
            f"{quantity}",
            f"{line_total:.0f} FCFA"
        ])

    table = Table(data, colWidths=[250, 90, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))

    # ========== TOTALS ==========
    delivery = 1000
    total_with_delivery = total + delivery

    total_data = [
        ["Sous total :", f"{total:.0f} FCFA"],
        ["Frais de livraison :", f"{delivery:.0f} FCFA"],
        ["TOTAL :", f"{total_with_delivery:.0f} FCFA"],
    ]

    table = Table(total_data, colWidths=[380, 140])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # ========== PAIEMENT ==========
    elements.append(Paragraph("<b>Paiement à l’ordre de : LEMAILLOT</b>", styleN))
    elements.append(Spacer(1, 6))
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("MERCI DE VOTRE CONFIANCE", styleN))

    doc.build(elements)
    buffer.seek(0)
    return buffer
