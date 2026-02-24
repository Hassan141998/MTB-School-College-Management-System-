"""
PDF Generator using ReportLab
Generates fee receipts and result cards.
"""
import io
from datetime import date

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                     TableStyle, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Brand colors
PRIMARY = colors.HexColor('#FF6B35')
SECONDARY = colors.HexColor('#004E89')
ACCENT = colors.HexColor('#F7B801')
LIGHT_GRAY = colors.HexColor('#f8f9fa')
WHITE = colors.white


def generate_fee_receipt(payment):
    """
    Generate PDF fee receipt for a FeePayment object.
    Returns bytes or None.
    """
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold',
                                  fontSize=22, textColor=PRIMARY, alignment=TA_CENTER)
    sub_style = ParagraphStyle('Sub', fontName='Helvetica',
                                fontSize=11, textColor=SECONDARY, alignment=TA_CENTER)
    small_style = ParagraphStyle('Small', fontName='Helvetica',
                                  fontSize=9, textColor=colors.gray, alignment=TA_CENTER)

    story.append(Paragraph('MTB School & College', title_style))
    story.append(Paragraph('Providing Quality Education Since 2005', sub_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
    story.append(Spacer(1, 4))

    receipt_style = ParagraphStyle('Receipt', fontName='Helvetica-Bold',
                                    fontSize=16, textColor=SECONDARY, alignment=TA_CENTER)
    story.append(Paragraph('FEE RECEIPT', receipt_style))
    story.append(Spacer(1, 10))

    # Receipt meta
    meta_data = [
        ['Receipt No:', payment.receipt_no or 'N/A',
         'Date:', payment.payment_date.strftime('%d-%b-%Y') if payment.payment_date else date.today().strftime('%d-%b-%Y')],
        ['Payment Method:', (payment.payment_method or 'Cash').title(),
         'Academic Year:', '2024-25'],
    ]
    meta_table = Table(meta_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), SECONDARY),
        ('TEXTCOLOR', (2, 0), (2, -1), SECONDARY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 10))

    # Student info
    student = payment.student
    reg_no = student.reg_no if student else 'N/A'
    student_name = student.full_name if student else 'N/A'
    father_name = student.father_name if student else 'N/A'
    class_name = student.class_section.display_name if student and student.class_section else 'N/A'

    student_data = [
        ['Student Name:', student_name, 'Reg. No:', reg_no],
        ["Father's Name:", father_name, 'Class:', class_name],
    ]
    student_table = Table(student_data, colWidths=[3*cm, 7*cm, 3*cm, 5*cm])
    student_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT_GRAY, WHITE]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(student_table)
    story.append(Spacer(1, 14))

    # Fee details
    fee_header = [['Sr.', 'Description', 'Month/Period', 'Amount (PKR)']]
    fee_name = payment.fee_structure.name if payment.fee_structure else 'Fee Payment'
    period = f"{payment.month or ''} {payment.year or ''}".strip() or 'N/A'
    fee_rows = [[1, fee_name, period, f'Rs. {payment.amount:,.0f}']]
    if payment.discount and payment.discount > 0:
        fee_rows.append(['', 'Discount', '', f'-Rs. {payment.discount:,.0f}'])
    if payment.fine and payment.fine > 0:
        fee_rows.append(['', 'Late Fine', '', f'+Rs. {payment.fine:,.0f}'])

    all_rows = fee_header + fee_rows + [['', '', 'TOTAL PAID', f'Rs. {payment.total_paid:,.0f}']]
    fee_table = Table(all_rows, colWidths=[1*cm, 9*cm, 4*cm, 4*cm])
    fee_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, -1), (-1, -1), PRIMARY),
        ('TEXTCOLOR', (0, -1), (-1, -1), WHITE),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(fee_table)
    story.append(Spacer(1, 20))

    # Footer
    footer_data = [
        ['Collected By:', payment.collected_by or 'Accounts Department', '', 'Signature: _______________']
    ]
    footer_table = Table(footer_data, colWidths=[3*cm, 8*cm, 2*cm, 5*cm])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(footer_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 6))
    story.append(Paragraph('This is a computer-generated receipt. No signature required.',
                             ParagraphStyle('footer', fontName='Helvetica',
                                             fontSize=8, textColor=colors.gray, alignment=TA_CENTER)))
    story.append(Paragraph('MTB School & College | Phone: +92-XXX-XXXXXXX | Email: info@mtbschool.edu.pk',
                             ParagraphStyle('footer2', fontName='Helvetica',
                                             fontSize=8, textColor=colors.gray, alignment=TA_CENTER)))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_result_card(student, exam, subject_marks):
    """
    Generate PDF result card.
    subject_marks: list of dicts {subject_name, obtained, total, grade}
    Returns bytes or None.
    """
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold',
                                  fontSize=22, textColor=PRIMARY, alignment=TA_CENTER)
    sub_style = ParagraphStyle('Sub', fontName='Helvetica',
                                fontSize=11, textColor=SECONDARY, alignment=TA_CENTER)

    story.append(Paragraph('MTB School & College', title_style))
    story.append(Paragraph('Result Card', sub_style))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
    story.append(Spacer(1, 10))

    # Exam & Student Details
    class_name = student.class_section.display_name if student.class_section else 'N/A'
    info_data = [
        ['Student Name:', student.full_name, 'Exam:', exam.name],
        ['Reg. No:', student.reg_no, 'Class:', class_name],
        ["Father's Name:", student.father_name or 'N/A', 'Academic Year:', exam.academic_year or '2024-25'],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # Marks Table
    headers = [['Sr.', 'Subject', 'Total Marks', 'Obtained', 'Percentage', 'Grade']]
    rows = []
    total_obtained = 0
    total_marks_sum = 0
    for i, sm in enumerate(subject_marks, 1):
        pct = round((sm['obtained'] / sm['total']) * 100, 1) if sm['total'] > 0 else 0
        rows.append([str(i), sm['subject_name'], str(sm['total']),
                     str(sm['obtained']), f"{pct}%", sm['grade']])
        total_obtained += sm['obtained']
        total_marks_sum += sm['total']

    total_pct = round((total_obtained / total_marks_sum) * 100, 1) if total_marks_sum > 0 else 0
    from app.utils.helpers import calculate_grade
    overall_grade = calculate_grade(total_pct)
    rows.append(['', 'TOTAL', str(total_marks_sum), str(total_obtained),
                 f"{total_pct}%", overall_grade])

    all_rows = headers + rows
    marks_table = Table(all_rows, colWidths=[1*cm, 7*cm, 3*cm, 3*cm, 3*cm, 2*cm])
    marks_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, -1), (-1, -1), PRIMARY),
        ('TEXTCOLOR', (0, -1), (-1, -1), WHITE),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, LIGHT_GRAY]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(marks_table)
    story.append(Spacer(1, 16))

    # Grade legend
    legend_style = ParagraphStyle('legend', fontName='Helvetica',
                                   fontSize=9, textColor=colors.gray)
    story.append(Paragraph('Grade Scale: A+ (≥90%) | A (80-89%) | B (70-79%) | C (60-69%) | D (50-59%) | F (<50%)',
                             legend_style))
    story.append(Spacer(1, 20))

    # Signatures
    sig_data = [['Principal Signature', 'Class Teacher Signature', 'Parent Signature']]
    sig_table = Table(sig_data, colWidths=[6*cm, 6*cm, 6*cm])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOX', (0, 0), (0, 0), 0.5, colors.grey),
        ('BOX', (1, 0), (1, 0), 0.5, colors.grey),
        ('BOX', (2, 0), (2, 0), 0.5, colors.grey),
    ]))
    story.append(sig_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
