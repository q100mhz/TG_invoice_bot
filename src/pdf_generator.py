import os
import io
import urllib.request
import qrcode
from datetime import datetime
from num2words import num2words
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_NAME = "DejaVu"

def ensure_font_loaded():
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME

    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_font_path = os.path.join(base_dir, "DejaVuSans.ttf")
    
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        local_font_path,
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]

    for p in font_candidates:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(FONT_NAME, p))
                return FONT_NAME
            except Exception:
                continue

    try:
        font_url = "https://raw.githubusercontent.com/dejavu-fonts/dejavu-fonts/master/ttf/DejaVuSans.ttf"
        urllib.request.urlretrieve(font_url, local_font_path)
        pdfmetrics.registerFont(TTFont(FONT_NAME, local_font_path))
        return FONT_NAME
    except Exception:
        return "Helvetica"

ensure_font_loaded()

def generate_qr_bytes(seller: dict, amount: float, invoice_num: int) -> io.BytesIO:
    amount_kopecks = int(amount * 100)
    qr_data = (
        f"ST00012|Name={seller['company_name']}|PersonalAcc={seller['rs']}|"
        f"BankName={seller['bank_name']}|BIC={seller['bik']}|CorrespAcc={seller['ks']}|"
        f"PayeeINN={seller['inn']}|Purpose=Оплата по счету №{invoice_num}|Sum={amount_kopecks}"
    )
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(qr_data.encode('utf-8'))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

def create_invoice_pdf(seller: dict, buyer_name: str, item_name: str, price: float, invoice_num: int, output_path: str):
    ensure_font_loaded()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle('Normal_CYR', fontName=FONT_NAME, fontSize=9, leading=12)
    bold_style = ParagraphStyle('Bold_CYR', fontName=FONT_NAME, fontSize=9, leading=12)
    title_style = ParagraphStyle('Title_CYR', fontName=FONT_NAME, fontSize=13, leading=16)
    
    elements = []
    
    bank_data = [
        [Paragraph(seller['bank_name'], normal_style), Paragraph("БИК", normal_style), Paragraph(seller['bik'], normal_style)],
        [Paragraph("Банк получателя", normal_style), Paragraph("Сч. №", normal_style), Paragraph(seller['ks'], normal_style)],
        [Paragraph(f"ИНН {seller['inn']}", normal_style), Paragraph("Сч. №", normal_style), Paragraph(seller['rs'], normal_style)],
        [Paragraph(seller['company_name'], normal_style), "", ""]
    ]
    
    bank_table = Table(bank_data, colWidths=[280, 55, 200])
    bank_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (0, 2), (0, 2)),
        ('SPAN', (0, 3), (0, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(bank_table)
    elements.append(Spacer(1, 15))
    
    date_str = datetime.now().strftime("%d.%m.%Y")
    elements.append(Paragraph(f"<b>Счет на оплату № {invoice_num} от {date_str} г.</b>", title_style))
    elements.append(Spacer(1, 12))
    
    info_data = [
        [Paragraph("<b>Поставщик:</b>", normal_style), Paragraph(f"{seller['company_name']}, ИНН {seller['inn']}", normal_style)],
        [Paragraph("<b>Покупатель:</b>", normal_style), Paragraph(buyer_name, normal_style)],
    ]
    info_table = Table(info_data, colWidths=[80, 455])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))
    
    price_formatted = f"{price:,.2f}".replace(",", " ").replace(".", ",")
    items_data = [
        [Paragraph("№", bold_style), Paragraph("Товары (работы, услуги)", bold_style), Paragraph("Кол-во", bold_style), Paragraph("Цена", bold_style), Paragraph("Сумма", bold_style)],
        [Paragraph("1", normal_style), Paragraph(item_name, normal_style), Paragraph("1", normal_style), Paragraph(f"{price_formatted} руб.", normal_style), Paragraph(f"{price_formatted} руб.", normal_style)]
    ]
    items_table = Table(items_data, colWidths=[25, 275, 50, 95, 90])
    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 10))
    
    totals_data = [
        [Paragraph("<b>Итого к оплате:</b>", normal_style), Paragraph(f"<b>{price_formatted} руб.</b>", normal_style)],
        [Paragraph("Без НДС", normal_style), Paragraph("-", normal_style)]
    ]
    totals_table = Table(totals_data, colWidths=[435, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 10))
    
    rubles = int(price)
    kopecks = int(round((price - rubles) * 100))
    words_rub = num2words(rubles, lang='ru')
    summary_text = (
        f"Всего наименований 1, на сумму {price_formatted} руб.<br/>"
        f"<b>{words_rub.capitalize()} рублей {kopecks:02d} копеек</b>"
    )
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 20))
    
    qr_buffer = generate_qr_bytes(seller, price, invoice_num)
    qr_img = Image(qr_buffer, width=105, height=105)
    
    footer_data = [
        [qr_img, Paragraph("<b>QR-код для оплаты в мобильном банке</b><br/>Отсканируйте камерой или приложением банка (Сбер, Т-Банк, ВТБ, Точка) для моментальной оплаты без ручного ввода реквизитов.", normal_style)]
    ]
    footer_table = Table(footer_data, colWidths=[115, 420])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(footer_table)
    
    doc.build(elements)