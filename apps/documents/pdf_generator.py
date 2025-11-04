"""
Generador de PDFs con ReportLab
Sistema profesional para crear documentos PDF personalizados
"""
from io import BytesIO
from datetime import datetime
from django.conf import settings
from django.core.files import File
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, ListFlowable, ListItem
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Clase principal para generar PDFs profesionales
    """
    
    def __init__(self, template=None, page_size=letter):
        """
        Inicializa el generador de PDF
        
        Args:
            template: Instancia de DocumentTemplate (opcional)
            page_size: Tamaño de página (letter o A4)
        """
        self.template = template
        self.page_size = page_size
        self.buffer = BytesIO()
        self.styles = self._create_styles()
        self.story = []
        
        # Configuración del documento
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.page_size,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1.2*inch,
            bottomMargin=1*inch,
        )
        
        # Colores corporativos (pueden ser personalizados por template)
        self.primary_color = colors.HexColor('#1a365d')  # Azul oscuro
        self.secondary_color = colors.HexColor('#2c5282')  # Azul medio
        self.accent_color = colors.HexColor('#4299e1')  # Azul claro
        self.text_color = colors.HexColor('#2d3748')  # Gris oscuro
        
    def _create_styles(self):
        """Crea y retorna los estilos personalizados"""
        styles = getSampleStyleSheet()
        
        # Estilo para el título principal
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=self.primary_color,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulos
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.primary_color,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para secciones
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.secondary_color,
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para texto normal
        styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=styles['BodyText'],
            fontSize=11,
            textColor=self.text_color,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Estilo para listas
        styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=self.text_color,
            leftIndent=20,
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        return styles
    
    def _header_footer(self, canvas, doc):
        """
        Dibuja el encabezado y pie de página
        """
        canvas.saveState()
        
        # Encabezado
        if self.template and self.template.logo:
            try:
                logo_path = self.template.logo.path
                canvas.drawImage(
                    logo_path,
                    0.75*inch,
                    doc.height + 1.5*inch,
                    width=1.5*inch,
                    height=0.5*inch,
                    preserveAspectRatio=True
                )
            except Exception as e:
                logger.warning(f"No se pudo cargar el logo: {e}")
        
        # Línea del encabezado
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(2)
        canvas.line(
            0.75*inch,
            doc.height + 1.3*inch,
            doc.width + 1.25*inch,
            doc.height + 1.3*inch
        )
        
        # Texto del encabezado
        if self.template and self.template.header_text:
            canvas.setFont('Helvetica', 9)
            canvas.setFillColor(self.text_color)
            canvas.drawRightString(
                doc.width + 1.25*inch,
                doc.height + 1.5*inch,
                self.template.header_text
            )
        
        # Pie de página
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        
        # Número de página
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"
        canvas.drawRightString(
            doc.width + 1.25*inch,
            0.5*inch,
            text
        )
        
        # Texto del pie de página
        if self.template and self.template.footer_text:
            canvas.drawString(
                0.75*inch,
                0.5*inch,
                self.template.footer_text
            )
        
        # Fecha de generación
        date_text = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        canvas.drawCentredString(
            doc.width / 2 + 1*inch,
            0.5*inch,
            date_text
        )
        
        canvas.restoreState()
    
    def add_title(self, text):
        """Añade un título principal"""
        self.story.append(Paragraph(text, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_heading(self, text, level=1):
        """Añade un encabezado"""
        style = 'CustomHeading1' if level == 1 else 'CustomHeading2'
        self.story.append(Paragraph(text, self.styles[style]))
    
    def add_paragraph(self, text):
        """Añade un párrafo de texto"""
        self.story.append(Paragraph(text, self.styles['CustomBodyText']))
    
    def add_spacer(self, height=0.2):
        """Añade un espacio en blanco"""
        self.story.append(Spacer(1, height*inch))
    
    def add_page_break(self):
        """Añade un salto de página"""
        self.story.append(PageBreak())
    
    def add_bullet_list(self, items):
        """Añade una lista con viñetas"""
        bullet_list = []
        for item in items:
            bullet_list.append(ListItem(
                Paragraph(item, self.styles['CustomBullet']),
                leftIndent=20
            ))
        self.story.append(ListFlowable(
            bullet_list,
            bulletType='bullet',
            start='•',
        ))
        self.story.append(Spacer(1, 0.1*inch))
    
    def add_table(self, data, col_widths=None, style='default'):
        """
        Añade una tabla
        
        Args:
            data: Lista de listas con los datos
            col_widths: Anchos de columnas (opcional)
            style: Estilo de la tabla ('default', 'zebra', 'simple')
        """
        # Crear la tabla
        table = Table(data, colWidths=col_widths)
        
        # Estilos predefinidos
        if style == 'default':
            table.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Contenido
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), self.text_color),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Bordes
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 2, self.primary_color),
            ]))
        elif style == 'zebra':
            # Estilo con rayas alternadas
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_info_box(self, title, content):
        """Añade un cuadro de información destacada"""
        # Crear tabla para el cuadro
        data = [
            [Paragraph(f"<b>{title}</b>", self.styles['CustomBodyText'])],
            [Paragraph(content, self.styles['CustomBodyText'])]
        ]
        
        table = Table(data, colWidths=[6.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.accent_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('BOX', (0, 0), (-1, -1), 2, self.accent_color),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_two_column_section(self, left_data, right_data):
        """Añade una sección con dos columnas"""
        data = [[left_data, right_data]]
        table = Table(data, colWidths=[3.25*inch, 3.25*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.2*inch))
    
    def generate(self):
        """
        Genera el PDF y retorna el buffer
        """
        try:
            # Construir el documento con encabezado y pie de página
            self.doc.build(
                self.story,
                onFirstPage=self._header_footer,
                onLaterPages=self._header_footer
            )
            
            # Resetear el buffer al inicio
            self.buffer.seek(0)
            return self.buffer
            
        except Exception as e:
            logger.error(f"Error al generar PDF: {e}")
            raise


class ProfilePDFGenerator(PDFGenerator):
    """
    Generador especializado para PDFs de Perfiles de Reclutamiento
    """
    
    def generate_profile_pdf(self, profile):
        """
        Genera un PDF completo del perfil
        
        Args:
            profile: Instancia del modelo Profile
        """
        # Título
        self.add_title(f"Perfil de Reclutamiento: {profile.position_title}")
        
        # Información del cliente
        self.add_heading("Información del Cliente")
        client_data = [
            ["Empresa:", profile.client.company_name],
            ["Industria:", profile.client.industry],
            ["Contacto:", f"{profile.client.contact_name} ({profile.client.contact_position})"],
            ["Email:", profile.client.contact_email],
            ["Teléfono:", profile.client.contact_phone],
        ]
        self.add_table(client_data, col_widths=[2*inch, 4.5*inch], style='simple')
        self.add_spacer()
        
        # Detalles de la posición
        self.add_heading("Detalles de la Posición")
        self.add_paragraph(f"<b>Posición:</b> {profile.position_title}")
        self.add_paragraph(f"<b>Departamento:</b> {profile.department or 'No especificado'}")
        self.add_paragraph(f"<b>Nivel:</b> {profile.get_level_display()}")
        self.add_paragraph(f"<b>Tipo de contrato:</b> {profile.get_contract_type_display()}")
        self.add_paragraph(f"<b>Modalidad:</b> {profile.get_work_modality_display()}")
        self.add_spacer()
        
        # Rango salarial
        if profile.salary_min and profile.salary_max:
            self.add_info_box(
                "Rango Salarial",
                f"${profile.salary_min:,.2f} - ${profile.salary_max:,.2f} {profile.salary_currency}"
            )
        
        # Descripción del puesto
        if profile.job_description:
            self.add_heading("Descripción del Puesto")
            self.add_paragraph(profile.job_description)
            self.add_spacer()
        
        # Responsabilidades
        if profile.responsibilities:
            self.add_heading("Responsabilidades Principales")
            responsibilities = profile.responsibilities.split('\n') if isinstance(profile.responsibilities, str) else profile.responsibilities
            self.add_bullet_list([r.strip() for r in responsibilities if r.strip()])
            self.add_spacer()
        
        # Requisitos
        self.add_heading("Requisitos")
        
        # Educación
        self.add_paragraph(f"<b>Educación requerida:</b> {profile.get_education_level_display()}")
        if profile.required_degrees:
            self.add_paragraph(f"<b>Carreras:</b> {profile.required_degrees}")
        
        # Experiencia
        if profile.years_experience_min or profile.years_experience_max:
            exp_text = "Experiencia: "
            if profile.years_experience_min and profile.years_experience_max:
                exp_text += f"{profile.years_experience_min} - {profile.years_experience_max} años"
            elif profile.years_experience_min:
                exp_text += f"Mínimo {profile.years_experience_min} años"
            else:
                exp_text += f"Máximo {profile.years_experience_max} años"
            self.add_paragraph(f"<b>{exp_text}</b>")
        
        # Idiomas
        if profile.required_languages:
            langs = ', '.join([f"{lang['language']} ({lang['level']})" for lang in profile.required_languages])
            self.add_paragraph(f"<b>Idiomas:</b> {langs}")
        
        self.add_spacer()
        
        # Habilidades técnicas
        if profile.technical_skills:
            self.add_heading("Habilidades Técnicas Requeridas", level=2)
            skills = [skill['skill'] for skill in profile.technical_skills]
            self.add_bullet_list(skills)
            self.add_spacer()
        
        # Habilidades blandas
        if profile.soft_skills:
            self.add_heading("Habilidades Blandas", level=2)
            soft_skills = [skill['skill'] for skill in profile.soft_skills]
            self.add_bullet_list(soft_skills)
            self.add_spacer()
        
        # Beneficios
        if profile.benefits:
            self.add_heading("Beneficios Ofrecidos")
            benefits = profile.benefits.split('\n') if isinstance(profile.benefits, str) else profile.benefits
            self.add_bullet_list([b.strip() for b in benefits if b.strip()])
        
        # Página de resumen
        self.add_page_break()
        self.add_heading("Resumen del Perfil")
        
        summary_data = [
            ["Campo", "Valor"],
            ["Vacantes", str(profile.vacancies)],
            ["Estado", profile.get_status_display()],
            ["Prioridad", profile.get_priority_display()],
            ["Fecha límite", profile.deadline.strftime('%d/%m/%Y') if profile.deadline else 'No especificada'],
            ["Asignado a", profile.assigned_to.get_full_name() if profile.assigned_to else 'No asignado'],
        ]
        self.add_table(summary_data, style='zebra')
        
        return self.generate()


class CandidateReportGenerator(PDFGenerator):
    """
    Generador especializado para reportes de candidatos
    """
    
    def generate_candidate_report(self, candidate, profile=None):
        """
        Genera un reporte completo del candidato
        
        Args:
            candidate: Instancia del modelo Candidate
            profile: Perfil al que aplica (opcional)
        """
        # Título
        title = f"Reporte de Candidato: {candidate.get_full_name()}"
        if profile:
            title += f" - {profile.position_title}"
        self.add_title(title)
        
        # Información personal
        self.add_heading("Información Personal")
        personal_data = [
            ["Nombre completo:", candidate.get_full_name()],
            ["Email:", candidate.email],
            ["Teléfono:", candidate.phone],
            ["Ubicación:", f"{candidate.city}, {candidate.state}"],
        ]
        if candidate.date_of_birth:
            from datetime import date
            age = (date.today() - candidate.date_of_birth).days // 365
            personal_data.append(["Edad:", f"{age} años"])
        
        self.add_table(personal_data, col_widths=[2*inch, 4.5*inch], style='simple')
        self.add_spacer()
        
        # Experiencia profesional
        if candidate.work_experience:
            self.add_heading("Experiencia Profesional")
            for exp in candidate.work_experience:
                self.add_paragraph(f"<b>{exp.get('position', 'Posición')}</b> en {exp.get('company', 'Empresa')}")
                self.add_paragraph(f"{exp.get('start_date', '')} - {exp.get('end_date', 'Actual')}")
                if exp.get('description'):
                    self.add_paragraph(exp['description'])
                self.add_spacer(0.1)
        
        # Educación
        if candidate.education:
            self.add_heading("Educación")
            for edu in candidate.education:
                self.add_paragraph(f"<b>{edu.get('degree', 'Título')}</b> - {edu.get('institution', 'Institución')}")
                self.add_paragraph(f"{edu.get('field', 'Campo de estudio')} ({edu.get('year', 'Año')})")
                self.add_spacer(0.1)
        
        # Habilidades
        if candidate.skills:
            self.add_heading("Habilidades")
            skills = [skill['skill'] for skill in candidate.skills]
            self.add_bullet_list(skills)
        
        # Análisis de IA (si está disponible)
        if hasattr(candidate, 'ai_analysis') and candidate.ai_analysis:
            self.add_page_break()
            self.add_heading("Análisis con Inteligencia Artificial")
            self.add_info_box(
                "Resumen del Análisis",
                candidate.ai_analysis.get('summary', 'No disponible')
            )
            
            if candidate.ai_analysis.get('match_score'):
                score = candidate.ai_analysis['match_score']
                self.add_paragraph(f"<b>Puntuación de compatibilidad:</b> {score}%")
        
        return self.generate()


# Funciones auxiliares

def generate_profile_pdf(profile, template=None):
    """
    Función auxiliar para generar PDF de perfil
    
    Args:
        profile: Instancia del modelo Profile
        template: Plantilla a usar (opcional)
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    generator = ProfilePDFGenerator(template=template)
    return generator.generate_profile_pdf(profile)


def generate_candidate_report_pdf(candidate, profile=None, template=None):
    """
    Función auxiliar para generar reporte de candidato
    
    Args:
        candidate: Instancia del modelo Candidate
        profile: Perfil relacionado (opcional)
        template: Plantilla a usar (opcional)
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    generator = CandidateReportGenerator(template=template)
    return generator.generate_candidate_report(candidate, profile)