"""
Data Organizer Module
Uses regex and pandas for cleaning, transformation, and structured output
of translated land record documents.
"""

import re
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class LandRecordField:
    """Represents a parsed field from land record"""
    field_name: str
    field_value: str
    field_type: str  # 'text', 'number', 'date', 'area', 'name', 'location'
    confidence: float = 1.0


class LandRecordDataOrganizer:
    """
    Organizes and structures translated land record data using
    regex pattern matching and pandas for data transformation.
    """
    
    # Regex patterns for common land record fields
    PATTERNS = {
        # Survey/Khasra numbers
        'survey_number': [
            r'(?:survey\s*(?:no\.?|number)|khasra\s*(?:no\.?|number)?|plot\s*(?:no\.?|number))[:\s]*([0-9/\-A-Za-z]+)',
            r'(?:khasra|khata)[:\s]*(\d+(?:[/\-]\d+)*)',
            r'survey\s+(\d+(?:[/\-]\d+)*)',
        ],
        
        # Area measurements
        'area': [
            r'(?:area|total\s*area|extent)[:\s]*([\d.,]+)\s*(?:acres?|hectares?|sq\.?\s*(?:ft|feet|m|meters?)|bigha|kanal|marla)',
            r'([\d.,]+)\s*(?:acres?|hectares?|bigha|kanal|marla|gunta|guntha|biswa)',
            r'(?:acres?|hectares?)[:\s]*([\d.,]+)',
        ],
        
        # Owner/Name patterns
        'owner_name': [
            r'(?:owner|owner\'s?\s*name|proprietor|title\s*holder|pattadar|khatedar)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
            r'(?:name\s*of\s*(?:the\s*)?owner)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
            r'(?:son\s*of|s/o|d/o|w/o)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
        ],
        
        # Father's name
        'father_name': [
            r'(?:father\'s?\s*name|s/o|son\s*of)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
            r'(?:bin|ibn)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
        ],
        
        # Village/Location
        'village': [
            r'(?:village|gram|mauza|mouza|gaon)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
            r'(?:location|locality)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
        ],
        
        # Tehsil/Taluka
        'tehsil': [
            r'(?:tehsil|tahsil|taluka|taluk|mandal)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
        ],
        
        # District
        'district': [
            r'(?:district|zila|jila)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
        ],
        
        # State
        'state': [
            r'(?:state|pradesh)[:\s]*([A-Za-z\s.,]+?)(?:\n|,|$)',
        ],
        
        # Date patterns
        'date': [
            r'(?:date|dated|on)[:\s]*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*,?\s*\d{2,4})',
            r'(?:year|sal)[:\s]*(\d{4})',
        ],
        
        # Land type/classification
        'land_type': [
            r'(?:land\s*type|land\s*classification|category|land\s*use)[:\s]*([A-Za-z\s]+?)(?:\n|,|$)',
            r'(?:agricultural|cultivable|barren|waste|residential|commercial)\s*land',
        ],
        
        # Revenue/Tax
        'revenue': [
            r'(?:revenue|tax|khazana|lagaan|malia)[:\s]*(?:rs\.?|₹)?\s*([\d,]+(?:\.\d{2})?)',
            r'(?:rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)',
        ],
        
        # Boundaries
        'boundary_north': [
            r'(?:north|uttar)[:\s]*([A-Za-z0-9\s.,]+?)(?:\n|,|east|south|west|$)',
        ],
        'boundary_south': [
            r'(?:south|dakshin)[:\s]*([A-Za-z0-9\s.,]+?)(?:\n|,|east|north|west|$)',
        ],
        'boundary_east': [
            r'(?:east|purva)[:\s]*([A-Za-z0-9\s.,]+?)(?:\n|,|south|north|west|$)',
        ],
        'boundary_west': [
            r'(?:west|paschim)[:\s]*([A-Za-z0-9\s.,]+?)(?:\n|,|east|south|north|$)',
        ],
        
        # Registration details
        'registration_number': [
            r'(?:registration\s*(?:no\.?|number)|deed\s*(?:no\.?|number)|document\s*(?:no\.?|number))[:\s]*([A-Za-z0-9/\-]+)',
        ],
        
        # Book/Volume numbers
        'book_number': [
            r'(?:book\s*(?:no\.?|number)|volume)[:\s]*([A-Za-z0-9/\-]+)',
        ],
    }
    
    # Field display names for PDF
    FIELD_LABELS = {
        'survey_number': 'Survey/Khasra Number',
        'area': 'Land Area',
        'owner_name': 'Owner Name',
        'father_name': "Father's Name",
        'village': 'Village',
        'tehsil': 'Tehsil/Taluka',
        'district': 'District',
        'state': 'State',
        'date': 'Date',
        'land_type': 'Land Type',
        'revenue': 'Revenue/Tax Amount',
        'boundary_north': 'North Boundary',
        'boundary_south': 'South Boundary',
        'boundary_east': 'East Boundary',
        'boundary_west': 'West Boundary',
        'registration_number': 'Registration Number',
        'book_number': 'Book/Volume Number',
    }
    
    def __init__(self):
        self.extracted_data: Dict[str, List[str]] = {}
        self.raw_text: str = ""
        self.structured_paragraphs: List[str] = []
        
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize the translated text.
        
        Args:
            text: Raw translated text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace while preserving paragraph structure
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Fix common OCR/translation artifacts
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between camelCase
        text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)  # Space between number and letter
        text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)  # Space between letter and number
        
        # Fix punctuation spacing
        text = re.sub(r'\s+([,.:;])', r'\1', text)
        text = re.sub(r'([,.:;])([A-Za-z])', r'\1 \2', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s.,;:\'\"()\-/₹$%@#&*+=\n]', '', text)
        
        # Standardize currency symbols
        text = re.sub(r'Rs\.?\s*', 'Rs. ', text, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Strip leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def extract_fields(self, text: str) -> Dict[str, List[str]]:
        """
        Extract structured fields from text using regex patterns.
        
        Args:
            text: Cleaned text to extract from
            
        Returns:
            Dictionary of field names to extracted values
        """
        extracted = {}
        text_lower = text.lower()
        
        for field_name, patterns in self.PATTERNS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text_lower if field_name != 'owner_name' else text, re.IGNORECASE | re.MULTILINE)
                for match in found:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                    match = str(match).strip()
                    if match and len(match) > 1 and match not in matches:
                        # Capitalize names properly
                        if field_name in ['owner_name', 'father_name', 'village', 'tehsil', 'district', 'state']:
                            match = match.title()
                        matches.append(match)
            
            if matches:
                extracted[field_name] = matches
        
        self.extracted_data = extracted
        return extracted
    
    def create_dataframe(self, extracted_data: Dict[str, List[str]]) -> pd.DataFrame:
        """
        Create a pandas DataFrame from extracted data for structured output.
        
        Args:
            extracted_data: Dictionary of extracted fields
            
        Returns:
            Structured DataFrame
        """
        # Create rows for the dataframe
        rows = []
        
        for field_name, values in extracted_data.items():
            label = self.FIELD_LABELS.get(field_name, field_name.replace('_', ' ').title())
            for value in values:
                rows.append({
                    'Field': label,
                    'Value': value,
                    'Category': self._get_category(field_name)
                })
        
        if not rows:
            return pd.DataFrame(columns=['Field', 'Value', 'Category'])
        
        df = pd.DataFrame(rows)
        
        # Sort by category for better organization
        category_order = ['Identification', 'Owner Details', 'Location', 'Area & Boundaries', 'Administrative', 'Other']
        df['Category'] = pd.Categorical(df['Category'], categories=category_order, ordered=True)
        df = df.sort_values('Category').reset_index(drop=True)
        
        return df
    
    def _get_category(self, field_name: str) -> str:
        """Get category for a field name"""
        categories = {
            'Identification': ['survey_number', 'registration_number', 'book_number'],
            'Owner Details': ['owner_name', 'father_name'],
            'Location': ['village', 'tehsil', 'district', 'state'],
            'Area & Boundaries': ['area', 'boundary_north', 'boundary_south', 'boundary_east', 'boundary_west'],
            'Administrative': ['date', 'land_type', 'revenue'],
        }
        
        for category, fields in categories.items():
            if field_name in fields:
                return category
        return 'Other'
    
    def structure_paragraphs(self, text: str) -> List[Dict[str, str]]:
        """
        Split text into structured paragraphs with headings.
        
        Args:
            text: Cleaned text
            
        Returns:
            List of paragraph dictionaries with heading and content
        """
        structured = []
        
        # Common section headers in land records
        section_patterns = [
            (r'(?:^|\n)((?:survey|khasra|plot)\s*(?:details?|information)?)', 'Survey Details'),
            (r'(?:^|\n)((?:owner|proprietor|pattadar)\s*(?:details?|information)?)', 'Owner Information'),
            (r'(?:^|\n)((?:land|property)\s*(?:details?|description|particulars)?)', 'Property Details'),
            (r'(?:^|\n)((?:boundary|boundaries|hadood))', 'Boundaries'),
            (r'(?:^|\n)((?:area|measurement|extent))', 'Area Measurements'),
            (r'(?:^|\n)((?:encumbrance|mortgage|lien))', 'Encumbrances'),
            (r'(?:^|\n)((?:remarks?|notes?|observations?))', 'Remarks'),
            (r'(?:^|\n)((?:schedule|particulars|description))', 'Schedule'),
        ]
        
        # Split by page markers first
        pages = re.split(r'---\s*Page\s+\d+\s*---', text)
        
        for page_num, page_content in enumerate(pages, 1):
            if not page_content.strip():
                continue
            
            # Try to identify sections within the page
            current_section = f"Page {page_num}" if len(pages) > 1 else "Document Content"
            current_content = []
            
            lines = page_content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line is a section header
                is_header = False
                for pattern, header_name in section_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Save previous section
                        if current_content:
                            structured.append({
                                'heading': current_section,
                                'content': '\n'.join(current_content)
                            })
                        current_section = header_name
                        current_content = []
                        is_header = True
                        break
                
                if not is_header:
                    current_content.append(line)
            
            # Add remaining content
            if current_content:
                structured.append({
                    'heading': current_section,
                    'content': '\n'.join(current_content)
                })
        
        self.structured_paragraphs = structured
        return structured
    
    def organize_for_pdf(self, translated_text: str) -> Dict[str, Any]:
        """
        Main method to organize translated text for PDF generation.
        
        Args:
            translated_text: Raw translated text
            
        Returns:
            Dictionary with all organized data for PDF generation
        """
        self.raw_text = translated_text
        
        # Step 1: Clean the text
        cleaned_text = self.clean_text(translated_text)
        
        # Step 2: Extract structured fields
        extracted_fields = self.extract_fields(cleaned_text)
        
        # Step 3: Create DataFrame for tabular data
        df = self.create_dataframe(extracted_fields)
        
        # Step 4: Structure paragraphs
        structured_paragraphs = self.structure_paragraphs(cleaned_text)
        
        # Step 5: Compile organized data
        organized_data = {
            'cleaned_text': cleaned_text,
            'extracted_fields': extracted_fields,
            'field_labels': self.FIELD_LABELS,
            'dataframe': df,
            'structured_paragraphs': structured_paragraphs,
            'summary': self._generate_summary(extracted_fields),
            'metadata': {
                'original_length': len(translated_text),
                'cleaned_length': len(cleaned_text),
                'fields_extracted': len(extracted_fields),
                'total_values': sum(len(v) for v in extracted_fields.values()),
                'sections_found': len(structured_paragraphs),
                'processed_at': datetime.now().isoformat()
            }
        }
        
        return organized_data
    
    def _generate_summary(self, extracted_fields: Dict[str, List[str]]) -> str:
        """Generate a brief summary of the document"""
        summary_parts = []
        
        if 'survey_number' in extracted_fields:
            summary_parts.append(f"Survey/Plot: {extracted_fields['survey_number'][0]}")
        
        if 'owner_name' in extracted_fields:
            summary_parts.append(f"Owner: {extracted_fields['owner_name'][0]}")
        
        if 'village' in extracted_fields:
            location_parts = [extracted_fields['village'][0]]
            if 'tehsil' in extracted_fields:
                location_parts.append(extracted_fields['tehsil'][0])
            if 'district' in extracted_fields:
                location_parts.append(extracted_fields['district'][0])
            summary_parts.append(f"Location: {', '.join(location_parts)}")
        
        if 'area' in extracted_fields:
            summary_parts.append(f"Area: {extracted_fields['area'][0]}")
        
        return ' | '.join(summary_parts) if summary_parts else "Land Record Document"
    
    def to_json(self) -> str:
        """Export organized data as JSON"""
        data = {
            'extracted_fields': self.extracted_data,
            'structured_paragraphs': self.structured_paragraphs,
        }
        return json.dumps(data, indent=2)


def organize_translated_data(text: str) -> Dict[str, Any]:
    """
    Convenience function to organize translated text.
    
    Args:
        text: Translated text to organize
        
    Returns:
        Organized data dictionary
    """
    organizer = LandRecordDataOrganizer()
    return organizer.organize_for_pdf(text)
