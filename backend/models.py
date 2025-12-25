from extensions import db
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    filename = db.Column(db.String(255))
    original_path = db.Column(db.Text)
    file_type = db.Column(db.String(10))
    file_size_kb = db.Column(db.Integer)
    ocr_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)
    detected_language = db.Column(db.String(10))
    ocr_confidence = db.Column(db.Float)
    processing_status = db.Column(db.String(20), default='pending')  # pending, processed, failed
    processing_time_ms = db.Column(db.Integer)  # Processing time in milliseconds
    khasra_number = db.Column(db.String(50))
    farmer_name = db.Column(db.String(255))
    district = db.Column(db.String(100))
    tehsil = db.Column(db.String(100))
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'detected_language': self.detected_language,
            'ocr_confidence': self.ocr_confidence,
            'processing_status': self.processing_status,
            'processing_time_ms': self.processing_time_ms,
            'khasra_number': self.khasra_number,
            'farmer_name': self.farmer_name,
            'district': self.district,
            'tehsil': self.tehsil,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Farmer(db.Model):
    __tablename__ = 'farmers'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name_local = db.Column(db.String(255))
    name_english = db.Column(db.String(255))
    father_name = db.Column(db.String(255))
    address = db.Column(db.Text)
    tehsil = db.Column(db.String(100))
    district = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name_local': self.name_local,
            'name_english': self.name_english,
            'father_name': self.father_name,
            'address': self.address,
            'tehsil': self.tehsil,
            'district': self.district,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LandParcel(db.Model):
    __tablename__ = 'land_parcels'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    khasra_number = db.Column(db.String(50), nullable=False)
    mauza = db.Column(db.String(100))
    tehsil = db.Column(db.String(100))
    district = db.Column(db.String(100))
    area_kanal = db.Column(db.Float)
    area_marla = db.Column(db.Float)
    land_type = db.Column(db.String(50))
    ownership_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'khasra_number': self.khasra_number,
            'mauza': self.mauza,
            'tehsil': self.tehsil,
            'district': self.district,
            'area_kanal': self.area_kanal,
            'area_marla': self.area_marla,
            'land_type': self.land_type,
            'ownership_status': self.ownership_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ProcessingStats(db.Model):
    __tablename__ = 'processing_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, unique=True)
    documents_processed = db.Column(db.Integer, default=0)
    documents_failed = db.Column(db.Integer, default=0)
    total_processing_time_ms = db.Column(db.Integer, default=0)
    urdu_count = db.Column(db.Integer, default=0)
    hindi_count = db.Column(db.Integer, default=0)
    english_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'documents_processed': self.documents_processed,
            'documents_failed': self.documents_failed,
            'total_processing_time_ms': self.total_processing_time_ms,
            'urdu_count': self.urdu_count,
            'hindi_count': self.hindi_count,
            'english_count': self.english_count
        }
