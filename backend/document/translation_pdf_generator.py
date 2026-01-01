"""
Enhanced Translation PDF Generator
Creates professional, well-organized PDF documents from translated land records.
Uses data_organizer for structure and pandas for tabular data.
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional, List

from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, ListFlowable, ListItem
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor, black, white, grey, lightgrey
from reportlab.lib import colors

from document.data_organizer import organize_translated_data, LandRecordDataOrganizer


class TranslationPDFGenerator:
    """
    Generates professional PDF documents from translated land records
    with organized sections, tables, and proper formatting.
    """
    
    # Color scheme
    COLORS = {
        'primary': HexColor('#292929'),
        'secondary': HexColor('#4a4a4a'),
        'accent': HexColor('#1a5f7a'),
        'light_bg': HexColor('#f5f5f5'),
        'border': HexColor('#cccccc'),
        'success': HexColor('#2e7d32'),
        'header_bg': HexColor('#e8e8e8'),
    }
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom paragraph styles for the PDF"""
        
        # Document title
        self.title_style = ParagraphStyle(
            'DocTitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            textColor=self.COLORS['primary'],
            spaceAfter=20,
            spaceBefore=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=28
        )
        
        # Section headers
        self.section_style = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.COLORS['primary'],
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold',
            borderColor=self.COLORS['primary'],
            borderWidth=0,
            borderPadding=0,
            leading=18
        )
        
        # Subsection headers
        self.subsection_style = ParagraphStyle(
            'SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=self.COLORS['secondary'],
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            leading=15
        )
        
        # Body text
        self.body_style = ParagraphStyle(
            'BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=black,
            alignment=TA_JUSTIFY,
            spaceBefore=4,
            spaceAfter=8,
            leading=14,
            firstLineIndent=0
        )
        
        # Metadata/info text
        self.meta_style = ParagraphStyle(
            'MetaText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.COLORS['secondary'],
            spaceAfter=4,
            leading=12
        )
        
        # Field label style
        self.label_style = ParagraphStyle(
            'FieldLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.COLORS['secondary'],
            fontName='Helvetica-Bold',
            spaceAfter=2
        )
        
        # Field value style
        self.value_style = ParagraphStyle(
            'FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=black,
            spaceAfter=6,
            leading=13
        )
        
        # Summary box style
        self.summary_style = ParagraphStyle(
            'Summary',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.COLORS['primary'],
            alignment=TA_CENTER,
            spaceBefore=8,
            spaceAfter=8,
            leading=14,
            fontName='Helvetica-Bold'
        )
        
        # Footer style
        self.footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=grey,
            alignment=TA_CENTER
        )
        
    def generate_pdf(
        self,
        translated_text: str,
        original_text: str = "",
        source_lang: str = "Urdu",
        target_lang: str = "English",
        total_pages: int = 1,
        filename: str = "document"
    ) -> io.BytesIO:
        """
        Generate a professional PDF from translated text.
        
        Args:
            translated_text: The translated text content
            original_text: Original text (for reference)
            source_lang: Source language name
            target_lang: Target language name
            total_pages: Number of pages in source document
            filename: Original filename
            
        Returns:
            BytesIO buffer containing the PDF
        """
        # Organize the data
        organized = organize_translated_data(translated_text)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=0.6*inch,
            bottomMargin=0.6*inch,
            leftMargin=0.7*inch,
            rightMargin=0.7*inch,
            title=f"Translated Document - {filename}",
            author="AgriStack Translation System"
        )
        
        # Build elements
        elements = []
        
        # Add header
        elements.extend(self._create_header(source_lang, target_lang, total_pages, filename))
        
        # Add document summary if available
        if organized.get('summary'):
            elements.extend(self._create_summary_box(organized['summary']))
        
        # Add extracted fields table if data was extracted
        if organized.get('extracted_fields'):
            elements.extend(self._create_extracted_fields_section(organized))
        
        # Add structured content
        if organized.get('structured_paragraphs'):
            elements.extend(self._create_content_sections(organized['structured_paragraphs']))
        else:
            # Fallback to cleaned text
            elements.extend(self._create_full_text_section(organized.get('cleaned_text', translated_text)))
        
        # Add metadata footer
        elements.extend(self._create_footer(organized.get('metadata', {})))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    def _create_header(
        self, 
        source_lang: str, 
        target_lang: str, 
        total_pages: int,
        filename: str
    ) -> List:
        """Create document header elements"""
        elements = []
        
        # Title
        elements.append(Paragraph("📄 Translated Land Record", self.title_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Horizontal line
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=self.COLORS['primary'],
            spaceBefore=5,
            spaceAfter=15
        ))
        
        # Metadata table
        meta_data = [
            ['Source Language:', source_lang.title()],
            ['Target Language:', target_lang.title()],
            ['Pages Processed:', str(total_pages)],
            ['Generated On:', datetime.now().strftime('%B %d, %Y at %H:%M')],
        ]
        
        if filename and filename != "document":
            meta_data.insert(0, ['Original File:', filename])
        
        meta_table = Table(meta_data, colWidths=[1.5*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['secondary']),
            ('TEXTCOLOR', (1, 0), (1, -1), black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(meta_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_summary_box(self, summary: str) -> List:
        """Create a summary box at the top"""
        elements = []
        
        # Summary table with background
        summary_data = [[Paragraph(f"📋 {summary}", self.summary_style)]]
        summary_table = Table(summary_data, colWidths=[6.3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['light_bg']),
            ('BOX', (0, 0), (-1, -1), 1, self.COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_extracted_fields_section(self, organized: Dict[str, Any]) -> List:
        """Create section with extracted field data in table format"""
        elements = []
        
        extracted = organized.get('extracted_fields', {})
        field_labels = organized.get('field_labels', {})
        
        if not extracted:
            return elements
        
        elements.append(Paragraph("📊 Extracted Information", self.section_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Group fields by category
        categories = {
            'Identification': ['survey_number', 'registration_number', 'book_number'],
            'Owner Details': ['owner_name', 'father_name'],
            'Location': ['village', 'tehsil', 'district', 'state'],
            'Area & Measurements': ['area'],
            'Boundaries': ['boundary_north', 'boundary_south', 'boundary_east', 'boundary_west'],
            'Administrative': ['date', 'land_type', 'revenue'],
        }
        
        for category, fields in categories.items():
            category_data = []
            for field in fields:
                if field in extracted:
                    label = field_labels.get(field, field.replace('_', ' ').title())
                    values = extracted[field]
                    # Join multiple values with comma
                    value_text = ', '.join(values[:3])  # Limit to 3 values
                    if len(values) > 3:
                        value_text += f' (+{len(values)-3} more)'
                    category_data.append([label, value_text])
            
            if category_data:
                # Category header
                elements.append(Paragraph(f"▸ {category}", self.subsection_style))
                
                # Category table
                cat_table = Table(category_data, colWidths=[2*inch, 4.3*inch])
                cat_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), self.COLORS['secondary']),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('LINEBELOW', (0, 0), (-1, -2), 0.5, self.COLORS['light_bg']),
                    ('BACKGROUND', (0, 0), (-1, -1), white),
                ]))
                
                elements.append(cat_table)
                elements.append(Spacer(1, 0.1*inch))
        
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.COLORS['border'],
            spaceBefore=10,
            spaceAfter=15
        ))
        
        return elements
    
    def _create_content_sections(self, structured_paragraphs: List[Dict[str, str]]) -> List:
        """Create content sections from structured paragraphs"""
        elements = []
        
        elements.append(Paragraph("📝 Document Content", self.section_style))
        elements.append(Spacer(1, 0.1*inch))
        
        current_heading = None
        
        for item in structured_paragraphs:
            heading = item.get('heading', '')
            content = item.get('content', '')
            
            if not content.strip():
                continue
            
            # Add section heading if different from current
            if heading and heading != current_heading:
                elements.append(Paragraph(f"▸ {heading}", self.subsection_style))
                current_heading = heading
            
            # Process content - escape special characters
            safe_content = self._escape_text(content)
            
            # Split into paragraphs
            paragraphs = safe_content.split('\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    elements.append(Paragraph(para, self.body_style))
            
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_full_text_section(self, text: str) -> List:
        """Create section with full translated text (fallback)"""
        elements = []
        
        elements.append(Paragraph("📝 Translated Content", self.section_style))
        elements.append(Spacer(1, 0.1*inch))
        
        if not text:
            elements.append(Paragraph("<i>No text content available</i>", self.meta_style))
            return elements
        
        # Escape and split into paragraphs
        safe_text = self._escape_text(text)
        paragraphs = safe_text.split('\n')
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Check if it looks like a heading
                if len(para) < 50 and para.endswith(':'):
                    elements.append(Paragraph(para, self.subsection_style))
                else:
                    elements.append(Paragraph(para, self.body_style))
        
        return elements
    
    def _create_footer(self, metadata: Dict[str, Any]) -> List:
        """Create document footer"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=self.COLORS['border'],
            spaceBefore=10,
            spaceAfter=10
        ))
        
        # Statistics
        if metadata:
            stats_parts = []
            if metadata.get('fields_extracted'):
                stats_parts.append(f"Fields Extracted: {metadata['fields_extracted']}")
            if metadata.get('sections_found'):
                stats_parts.append(f"Sections: {metadata['sections_found']}")
            if metadata.get('cleaned_length'):
                stats_parts.append(f"Characters: {metadata['cleaned_length']:,}")
            
            if stats_parts:
                elements.append(Paragraph(' | '.join(stats_parts), self.meta_style))
        
        # Footer note
        footer_text = "This document was automatically translated using AI-powered translation technology. " \
                     "Please verify critical information with official sources."
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(footer_text, self.footer_style))
        
        # Branding
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(
            "Generated by AgriStack Translation System | " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.footer_style
        ))
        
        return elements
    
    def _escape_text(self, text: str) -> str:
        """Escape special characters for ReportLab"""
        if not text:
            return ""
        
        # Escape HTML/XML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Handle other problematic characters
        text = text.replace('\t', '    ')  # Convert tabs to spaces
        
        return text


def generate_translation_pdf(
    translated_text: str,
    original_text: str = "",
    source_lang: str = "Urdu",
    target_lang: str = "English",
    total_pages: int = 1,
    filename: str = "document"
) -> io.BytesIO:
    """
    Convenience function to generate a translation PDF.
    
    Args:
        translated_text: The translated text content
        original_text: Original text (for reference)
        source_lang: Source language name
        target_lang: Target language name
        total_pages: Number of pages in source document
        filename: Original filename
        
    Returns:
        BytesIO buffer containing the PDF
    """
    generator = TranslationPDFGenerator()
    return generator.generate_pdf(
        translated_text=translated_text,
        original_text=original_text,
        source_lang=source_lang,
        target_lang=target_lang,
        total_pages=total_pages,
        filename=filename
    )
