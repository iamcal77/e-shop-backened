import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

from app.models import Order


def generate_invoice_pdf(order: Order, file_path: str):

    doc = SimpleDocTemplate(file_path)
    elements = []

    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("<b>INVOICE</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Invoice metadata
    metadata = f"""
    Invoice No: INV-{order.id}<br/>
    Date: {datetime.now().strftime("%Y-%m-%d")}<br/>
    Order ID: {order.id}<br/>
    Status: {order.status}
    """

    elements.append(Paragraph(metadata, styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    # Customer Info
    if order.user:
        customer = f"""
        Customer: {order.user.full_name or ''}<br/>
        Email: {order.user.email}
        """
    else:
        customer = f"Guest: {order.guest_email}"

    elements.append(Paragraph(customer, styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))

    # Table Data
    data = [["Product", "Qty", "Price", "Total"]]

    for item in order.items:
        product_name = item.product_variant.product.name
        total_price = item.quantity * item.price

        data.append([
            product_name,
            str(item.quantity),
            f"{order.currency} {item.price:.2f}",
            f"{order.currency} {total_price:.2f}"
        ])

    # Add shipping
    data.append(["", "", "Shipping", f"{order.currency} {order.shipping_cost:.2f}"])
    data.append(["", "", "Grand Total", f"{order.currency} {order.total:.2f}"])

    table = Table(data, colWidths=[2.5 * inch, 1 * inch, 1.2 * inch, 1.2 * inch])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 0.5 * inch))

    # Payment Info
    if order.payment:
        payment_info = f"""
        Payment Provider: {order.payment.provider}<br/>
        Payment Status: {order.payment.status}<br/>
        Reference: {order.payment.reference}
        """
        elements.append(Paragraph(payment_info, styles["Normal"]))

    doc.build(elements)
