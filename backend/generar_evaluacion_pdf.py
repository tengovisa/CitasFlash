"""
TengoVisa RD — Generador de PDF de Evaluación Migratoria
Estilo: Informe ejecutivo profesional
"""
import os, sys, json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, KeepTogether, PageBreak)
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF

# ── COLORES TENGOVISA ──
TV_RED    = colors.HexColor('#DC2626')
TV_BLUE   = colors.HexColor('#1D3A8A')
TV_DARK   = colors.HexColor('#111827')
TV_GRAY   = colors.HexColor('#374151')
TV_LIGHT  = colors.HexColor('#F3F4F6')
TV_BORDER = colors.HexColor('#E5E7EB')
GREEN     = colors.HexColor('#16A34A')
GREEN_BG  = colors.HexColor('#DCFCE7')
ORANGE    = colors.HexColor('#D97706')
ORANGE_BG = colors.HexColor('#FEF3C7')
RED_BG    = colors.HexColor('#FEE2E2')
BLUE_BG   = colors.HexColor('#DBEAFE')


def generar_pdf(data: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.5*inch,
        bottomMargin=0.6*inch,
        title=f"Evaluación Migratoria — {data.get('nombre','')} {data.get('apellido','')}",
        author="TengoVisa RD"
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Estilos personalizados ──
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    sTitle = S('tvTitle', fontSize=22, textColor=TV_RED, fontName='Helvetica-Bold',
               spaceAfter=2, leading=26)
    sSub   = S('tvSub', fontSize=11, textColor=TV_BLUE, fontName='Helvetica-Bold',
               spaceAfter=4, leading=14)
    sBody  = S('tvBody', fontSize=9, textColor=TV_GRAY, fontName='Helvetica',
               spaceAfter=3, leading=13)
    sSmall = S('tvSmall', fontSize=8, textColor=TV_GRAY, fontName='Helvetica',
               leading=11)
    sSec   = S('tvSec', fontSize=11, textColor=TV_BLUE, fontName='Helvetica-Bold',
               spaceBefore=10, spaceAfter=4, leading=14,
               borderPad=4, backColor=BLUE_BG, borderColor=TV_BLUE, borderWidth=0)
    sNote  = S('tvNote', fontSize=8.5, textColor=TV_DARK, fontName='Courier',
               leading=12, backColor=TV_LIGHT)

    nombre_completo = f"{data.get('nombre','')} {data.get('apellido','')}".strip()
    fecha = datetime.now().strftime("%d de %B de %Y")
    score = data.get('score', 0)
    ia_texto = data.get('ia_texto', '')

    # ════════════════════════════════
    # HEADER — Logo + Info
    # ════════════════════════════════
    def make_header():
        # Logo TV simulado con texto estilizado
        logo_data = [
            [Paragraph('<font color="#DC2626"><b>T</b></font><font color="#1D3A8A">V</font>',
                ParagraphStyle('logo', fontSize=36, fontName='Helvetica-Bold', leading=40)),
             Paragraph(
                '<font color="#DC2626"><b>TengoVisa RD</b></font><br/>'
                '<font color="#374151" size="8">Servicios Migratorios Profesionales</font><br/>'
                '<font color="#6B7280" size="7">crm.tengovisard.com | +1 (849) 918-9998</font>',
                ParagraphStyle('brand', fontSize=12, fontName='Helvetica-Bold', leading=16)),
             Paragraph(
                f'<font color="#6B7280" size="7">INFORME CONFIDENCIAL<br/>'
                f'Fecha: {fecha}<br/>'
                f'Ref: TV-EVAL-{datetime.now().strftime("%Y%m%d")}</font>',
                ParagraphStyle('ref', fontSize=7, fontName='Helvetica',
                               leading=11, alignment=TA_RIGHT))]
        ]
        t = Table(logo_data, colWidths=[0.7*inch, 4.2*inch, 2.3*inch])
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEBELOW', (0,0), (-1,0), 1.5, TV_RED),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ]))
        return t

    story.append(make_header())
    story.append(Spacer(1, 10))

    # ════════════════════════════════
    # TÍTULO PRINCIPAL
    # ════════════════════════════════
    story.append(Paragraph("EVALUACIÓN DE PERFIL MIGRATORIO", sTitle))
    story.append(Paragraph(f"Visa No Inmigrante B1/B2 — Análisis bajo INA §214(b)", sSub))
    story.append(Spacer(1, 6))

    # ════════════════════════════════
    # DATOS DEL SOLICITANTE
    # ════════════════════════════════
    story.append(Paragraph("◼ DATOS DEL SOLICITANTE", sSec))

    solicitante_data = [
        ['Nombre Completo', nombre_completo, 'Email', data.get('email','—')],
        ['WhatsApp', data.get('whatsapp','—'), 'Edad', f"{data.get('edad','—')} años"],
        ['Ciudad', data.get('ciudad','—'), 'Ocupación', data.get('ocupacion','—')],
        ['Estado Civil', data.get('estado_civil','—'), 'Hijos', str(data.get('hijos', 0))],
    ]
    t = Table(solicitante_data, colWidths=[1.4*inch, 2.3*inch, 1.4*inch, 2.2*inch])
    t.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',  (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 8.5),
        ('TEXTCOLOR', (0,0), (0,-1), TV_BLUE),
        ('TEXTCOLOR', (2,0), (2,-1), TV_BLUE),
        ('BACKGROUND',(0,0), (-1,-1), TV_LIGHT),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [TV_LIGHT, colors.white]),
        ('GRID',      (0,0), (-1,-1), 0.5, TV_BORDER),
        ('PADDING',   (0,0), (-1,-1), 5),
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # ════════════════════════════════
    # SCORING VISUAL
    # ════════════════════════════════
    story.append(Paragraph("◼ SCORING DETALLADO — INA §214(b)", sSec))

    # Score total visual
    score_color = GREEN if score >= 65 else (ORANGE if score >= 40 else TV_RED)
    score_label = 'APROBACIÓN PROBABLE' if score >= 65 else ('RIESGO MODERADO' if score >= 40 else 'ALTO RIESGO')
    prob_actual = f"{min(score, 75)}%" if score >= 65 else (f"{max(score-10,20)}%" if score >= 40 else f"{max(score-15,10)}%")
    prob_mejorada = f"{min(score+20, 85)}%" if score < 80 else "85%"

    # Barra de score
    score_header = [
        [Paragraph(f'<font color="white"><b>SCORE TOTAL: {score}/100</b></font>',
            ParagraphStyle('sh', fontSize=14, fontName='Helvetica-Bold',
                           textColor=colors.white, alignment=TA_CENTER)),
         Paragraph(f'<font color="white"><b>{score_label}</b></font>',
            ParagraphStyle('sl', fontSize=11, fontName='Helvetica-Bold',
                           textColor=colors.white, alignment=TA_CENTER)),
         Paragraph(
            f'<font color="white">Prob. actual: <b>{prob_actual}</b><br/>'
            f'Con mejoras: <b>{prob_mejorada}</b></font>',
            ParagraphStyle('sp', fontSize=9, fontName='Helvetica',
                           textColor=colors.white, alignment=TA_CENTER))]
    ]
    t = Table(score_header, colWidths=[2.2*inch, 3*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), score_color),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [6,6,6,6]),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Tabla de categorías
    categorias = [
        ('Arraigo Económico', data.get('score_economico', min(score//4, 25)), 25),
        ('Arraigo Familiar', data.get('score_familiar', min(score//5, 20)), 20),
        ('Estabilidad Laboral', data.get('score_laboral', min(score//5, 20)), 20),
        ('Historial Migratorio', data.get('score_migratorio', min(score//6, 15)), 15),
        ('Propósito del Viaje', data.get('score_proposito', min(score//10, 10)), 10),
        ('Perfil Demográfico', data.get('score_demografico', min(score//10, 10)), 10),
    ]

    cat_rows = [['Categoría', 'Puntos', 'Máx', 'Nivel', 'Barra']]
    for cat, pts, max_pts in categorias:
        pct = pts / max_pts if max_pts else 0
        nivel = '🟢 ALTO' if pct >= 0.7 else ('🟡 MEDIO' if pct >= 0.4 else '🔴 BAJO')
        barra = '█' * int(pct * 10) + '░' * (10 - int(pct * 10))
        cat_rows.append([cat, str(pts), str(max_pts), nivel, barra])

    cat_rows.append(['TOTAL', str(score), '100', score_label, ''])

    t = Table(cat_rows, colWidths=[2.4*inch, 0.6*inch, 0.5*inch, 1.2*inch, 2.6*inch])
    cat_style = [
        ('FONTNAME',  (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTNAME',  (0,-1),(-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 8.5),
        ('BACKGROUND',(0,0), (-1,0),  TV_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0),  colors.white),
        ('BACKGROUND',(0,-1),(-1,-1), score_color),
        ('TEXTCOLOR', (0,-1),(-1,-1), colors.white),
        ('GRID',      (0,0), (-1,-1), 0.5, TV_BORDER),
        ('PADDING',   (0,0), (-1,-1), 5),
        ('ALIGN',     (1,0), (2,-1),  'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, TV_LIGHT]),
        ('FONTNAME',  (4,1), (4,-2), 'Courier'),
        ('FONTSIZE',  (4,1), (4,-2), 7),
        ('TEXTCOLOR', (4,1), (4,-2), GREEN),
    ]
    t.setStyle(TableStyle(cat_style))
    story.append(t)
    story.append(Spacer(1, 8))

    # ════════════════════════════════
    # ANÁLISIS IA — Parsear el texto
    # ════════════════════════════════
    if ia_texto:
        story.append(Paragraph("◼ ANÁLISIS IA — EVALUACIÓN CONSULAR DETALLADA", sSec))

        # Dividir por secciones del markdown
        import re
        sections = re.split(r'\n##\s+', ia_texto)
        for sec in sections[:8]:  # Máximo 8 secciones
            if not sec.strip(): continue
            lines = sec.strip().split('\n')
            title = lines[0].strip().replace('#','').replace('*','').strip()
            body = '\n'.join(lines[1:]).strip()

            if title:
                story.append(Paragraph(f"<b>{title}</b>",
                    ParagraphStyle('secTitle', fontSize=9, fontName='Helvetica-Bold',
                                   textColor=TV_BLUE, spaceBefore=6, spaceAfter=2)))

            # Procesar el body
            for line in body.split('\n'):
                line = line.strip()
                if not line: continue
                line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
                line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', line)
                line = line.replace('✅','✓').replace('❌','✗').replace('🔴','[!]').replace('🟢','[OK]').replace('🟡','[-]')

                if line.startswith('|'):
                    # Es una tabla de markdown — ignorar por ahora
                    continue
                elif line.startswith('-') or line.startswith('•'):
                    story.append(Paragraph(f"  • {line[1:].strip()}",
                        ParagraphStyle('li', fontSize=8.5, fontName='Helvetica',
                                       textColor=TV_GRAY, leading=12, leftIndent=10)))
                elif line.startswith('[') or line.startswith('NIV'):
                    story.append(Paragraph(line,
                        ParagraphStyle('note', fontSize=8, fontName='Courier',
                                       textColor=TV_DARK, leading=11,
                                       backColor=TV_LIGHT, leftIndent=5)))
                else:
                    story.append(Paragraph(line, sBody))

    else:
        # Si no hay análisis IA, mostrar resumen basado en el score
        story.append(Paragraph("◼ RESUMEN DE EVALUACIÓN", sSec))
        story.append(Paragraph(
            f"Score obtenido: <b>{score}/100</b>. Nivel: <b>{score_label}</b>. "
            f"Probabilidad actual de aprobación: <b>{prob_actual}</b>. "
            f"Con las mejoras recomendadas puede alcanzar: <b>{prob_mejorada}</b>.",
            sBody))

    story.append(Spacer(1, 8))

    # ════════════════════════════════
    # DOCUMENTOS RECOMENDADOS
    # ════════════════════════════════
    story.append(Paragraph("◼ DOCUMENTOS REQUERIDOS", sSec))

    docs_criticos = [
        'Pasaporte vigente (mínimo 6 meses de validez)',
        'Carta empleador (membretada, teléfono verificable)',
        'Extractos bancarios — últimos 3 meses',
        'Talones de pago — últimos 3 meses',
        'Certificado laboral (antigüedad, salario, cargo)',
    ]
    docs_recomendados = [
        'Título de propiedad o vehículo (prueba de activos)',
        'Itinerario de viaje (hoteles/vuelos pre-reservados)',
        'Carta de invitación (si aplica)',
        'Fotos de bienes y propiedades en RD',
    ]

    doc_rows = [['☐', 'DOCUMENTO', 'IMPORTANCIA']]
    for d in docs_criticos:
        doc_rows.append(['☐', d, 'IMPRESCINDIBLE'])
    doc_rows.append(['', '', ''])
    for d in docs_recomendados:
        doc_rows.append(['☐', d, 'RECOMENDADO'])

    t = Table(doc_rows, colWidths=[0.3*inch, 5.2*inch, 1.8*inch])
    t.setStyle(TableStyle([
        ('FONTNAME',  (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',  (0,0), (-1,-1), 8.5),
        ('BACKGROUND',(0,0), (-1,0),  TV_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0),  colors.white),
        ('GRID',      (0,1), (-1,-1), 0.3, TV_BORDER),
        ('PADDING',   (0,0), (-1,-1), 4),
        ('TEXTCOLOR', (2,1), (2,5),   TV_RED),
        ('FONTNAME',  (2,1), (2,5),   'Helvetica-Bold'),
        ('TEXTCOLOR', (2,7), (2,-1),  GREEN),
        ('FONTNAME',  (2,7), (2,-1),  'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, TV_LIGHT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # ════════════════════════════════
    # PLAN DE ACCIÓN
    # ════════════════════════════════
    story.append(Paragraph("◼ PLAN DE ACCIÓN RECOMENDADO", sSec))

    if score >= 65:
        plan_color = GREEN_BG
        plan_title = "OPCIÓN A — APLICAR AHORA ✓ RECOMENDADO"
        plan_body = (f"Su perfil presenta una probabilidad de aprobación de <b>{prob_actual}</b>. "
                     "Se recomienda proceder con la aplicación inmediata una vez completa "
                     "la documentación listada. El riesgo de negación es bajo con los documentos correctos.")
        plan_costo = "RD$30,000 (servicio completo)"
        plan_tiempo = "Inmediato"
    elif score >= 40:
        plan_color = ORANGE_BG
        plan_title = "OPCIÓN B — FORTALECER PRIMERO ⚡ RECOMENDADO"
        plan_body = (f"Con un score de <b>{score}/100</b>, se recomienda fortalecer el perfil antes de aplicar. "
                     f"Con las mejoras indicadas puede alcanzar {prob_mejorada} de probabilidad. "
                     "Tiempo estimado de preparación: 60-90 días.")
        plan_costo = "RD$30,000 (servicio completo)"
        plan_tiempo = "60-90 días"
    else:
        plan_color = RED_BG
        plan_title = "OPCIÓN C — REESTRUCTURAR PERFIL ⚠️"
        plan_body = (f"El perfil actual presenta un score de <b>{score}/100</b>, lo que indica alto riesgo. "
                     "Se requieren cambios estructurales antes de aplicar para evitar una negación "
                     "que pueda afectar futuras solicitudes. Tiempo mínimo: 3-6 meses.")
        plan_costo = "Consultar según caso"
        plan_tiempo = "3-6 meses"

    plan_data = [
        [Paragraph(f'<b>{plan_title}</b>',
            ParagraphStyle('pt', fontSize=9, fontName='Helvetica-Bold', textColor=TV_DARK))],
        [Paragraph(plan_body, ParagraphStyle('pb', fontSize=8.5, fontName='Helvetica',
                                              textColor=TV_GRAY, leading=12))],
        [Paragraph(f'<b>Inversión estimada:</b> {plan_costo} &nbsp;&nbsp; | &nbsp;&nbsp; '
                   f'<b>Tiempo:</b> {plan_tiempo}',
            ParagraphStyle('pi', fontSize=8.5, fontName='Helvetica-Bold', textColor=TV_BLUE))]
    ]
    t = Table(plan_data, colWidths=[7.1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), plan_color),
        ('BOX',        (0,0), (-1,-1), 1, score_color),
        ('PADDING',    (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # ════════════════════════════════
    # NOTA CONSULAR SIMULADA
    # ════════════════════════════════
    story.append(Paragraph("◼ NOTA INTERNA SIMULADA — OFICIAL CONSULAR", sSec))

    nota_text = (
        f"NIV NOTES [{datetime.now().strftime('%Y-%m-%d')}] — SIMULACIÓN EDUCATIVA\n"
        f"Applicant: {nombre_completo} | Nationality: DO | Age: {data.get('edad','—')}\n"
        f"Employment: {data.get('ocupacion','Unspecified')} — REVIEW REQUIRED\n"
        f"Financial: Score {score}/100 — {'ADEQUATE' if score >= 50 else 'INSUFFICIENT'}\n"
        f"Home country ties: {'STRONG' if score >= 65 else ('MODERATE' if score >= 40 else 'WEAK')}\n"
        f"Purpose coherence: {'CONSISTENT' if score >= 50 else 'NEEDS CLARIFICATION'}\n"
        f"RECOMMENDATION: {'APPROVE - Ties appear sufficient' if score >= 65 else ('REVIEW - Additional documentation required' if score >= 40 else 'REFUSE §214(b) - Insufficient ties demonstrated')}\n"
        f"Evaluador: TengoVisa RD IA System | Ref: {datetime.now().strftime('%Y%m%d%H%M')}"
    )
    story.append(Paragraph(nota_text.replace('\n','<br/>'),
        ParagraphStyle('nota', fontSize=7.5, fontName='Courier', textColor=TV_DARK,
                       leading=13, backColor=TV_LIGHT, borderPad=8,
                       borderColor=TV_BORDER, borderWidth=1)))

    story.append(Spacer(1, 10))

    # ════════════════════════════════
    # FOOTER / FIRMA
    # ════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1.5, color=TV_RED))
    story.append(Spacer(1, 6))

    footer_data = [[
        Paragraph(
            '<b><font color="#DC2626">TengoVisa RD</font></b><br/>'
            '<font size="7" color="#6B7280">Servicios Migratorios Profesionales<br/>'
            'crm.tengovisard.com | +1 (849) 918-9998</font>',
            ParagraphStyle('fl', fontSize=9, fontName='Helvetica', leading=13)),
        Paragraph(
            '<font size="7" color="#6B7280"><i>Este documento es de carácter confidencial y fue '
            'generado por el sistema IA de TengoVisa RD basado en los datos proporcionados. '
            'No constituye asesoría legal oficial. La evaluación está basada en políticas '
            'vigentes del Departamento de Estado EE.UU. a la fecha de emisión.</i></font>',
            ParagraphStyle('fd', fontSize=7, fontName='Helvetica', textColor=TV_GRAY,
                           leading=10, alignment=TA_CENTER)),
        Paragraph(
            f'<font size="7" color="#6B7280">Generado: {fecha}<br/>'
            f'Score: {score}/100<br/>'
            f'Política: INA §214(b) 2026</font>',
            ParagraphStyle('fr', fontSize=7, fontName='Helvetica',
                           textColor=TV_GRAY, alignment=TA_RIGHT, leading=11)),
    ]]
    t = Table(footer_data, colWidths=[2*inch, 3.5*inch, 1.8*inch])
    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(t)

    doc.build(story)
    print(f"✅ PDF generado: {output_path}")
    return output_path


# ── Test con datos de ejemplo ──
if __name__ == '__main__':
    test_data = {
        'nombre': 'Felix Manuel',
        'apellido': 'Monte de Oca',
        'email': 'diocuma@gmail.com',
        'whatsapp': '8295599999',
        'edad': 37,
        'ciudad': 'Santiago',
        'ocupacion': 'Empresario',
        'estado_civil': 'casado',
        'hijos': 2,
        'score': 65,
        'ia_texto': '## VEREDICTO INMEDIATO\nRiesgo moderado. Score 65/100. Probabilidad actual 55%.\n## FORTALEZAS\n- Empleo estable 5 años\n- Propiedad inmueble en RD\n## VULNERABILIDADES\n- Sin visa previa\n- Familia en EEUU sin documentar',
    }
    generar_pdf(test_data, '/tmp/test_evaluacion.pdf')
