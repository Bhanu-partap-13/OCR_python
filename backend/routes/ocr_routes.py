from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime, date
from document.upload_handler import save_file
from ocr.lightweight_pipeline import ocr_pipeline
from extensions import db
from models import Document, Farmer, LandParcel, ProcessingStats
from sqlalchemy import func

ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    
    try:
        filepath = save_file(file, current_app.config['UPLOAD_FOLDER'])
        return jsonify({
            "success": True, 
            "message": "File uploaded successfully",
            "data": {
                "filepath": filepath,
                "filename": file.filename
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@ocr_bp.route('/process', methods=['POST'])
def process_ocr():
    data = request.get_json()
    filepath = data.get('filepath')
    if not filepath:
        return jsonify({"success": False, "error": "No filepath provided"}), 400
        
    try:
        start_time = time.time()
        
        with open(filepath, 'rb') as f:
            image_bytes = f.read()
            
        result = ocr_pipeline.process(image_bytes)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Detect language from result
        detected_lang = result.get('detected_language', 'unknown')
        
        # Create document record
        doc = Document(
            filename=os.path.basename(filepath),
            original_path=filepath,
            file_type=os.path.splitext(filepath)[1][1:].lower(),
            file_size_kb=len(image_bytes) // 1024,
            ocr_text=result.get('text', ''),
            detected_language=detected_lang,
            ocr_confidence=result.get('confidence', 0),
            processing_status='processed',
            processing_time_ms=processing_time_ms,
            processed_at=datetime.utcnow()
        )
        db.session.add(doc)
        
        # Update daily stats
        today = date.today()
        stats = ProcessingStats.query.filter_by(date=today).first()
        if not stats:
            stats = ProcessingStats(date=today)
            db.session.add(stats)
        
        stats.documents_processed += 1
        stats.total_processing_time_ms += processing_time_ms
        
        if detected_lang in ['ur', 'urd', 'urdu']:
            stats.urdu_count += 1
        elif detected_lang in ['hi', 'hin', 'hindi']:
            stats.hindi_count += 1
        else:
            stats.english_count += 1
            
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "data": {
                **result,
                "document_id": doc.id,
                "processing_time_ms": processing_time_ms
            }
        })
    except Exception as e:
        # Log failed processing
        try:
            today = date.today()
            stats = ProcessingStats.query.filter_by(date=today).first()
            if not stats:
                stats = ProcessingStats(date=today)
                db.session.add(stats)
            stats.documents_failed += 1
            db.session.commit()
        except:
            pass
        return jsonify({"success": False, "error": str(e)}), 500

@ocr_bp.route('/batch', methods=['POST'])
def batch_process():
    # TODO: Implement batch processing
    return jsonify({"success": True, "message": "Batch processing started"})

@ocr_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get real processing statistics from database"""
    try:
        # Total documents processed
        total_processed = db.session.query(func.count(Document.id)).filter(
            Document.processing_status == 'processed'
        ).scalar() or 0
        
        # Total failed
        total_failed = db.session.query(func.count(Document.id)).filter(
            Document.processing_status == 'failed'
        ).scalar() or 0
        
        # Success rate
        total_attempts = total_processed + total_failed
        success_rate = (total_processed / total_attempts * 100) if total_attempts > 0 else 0
        
        # Average processing time
        avg_time_result = db.session.query(func.avg(Document.processing_time_ms)).filter(
            Document.processing_status == 'processed'
        ).scalar()
        avg_processing_time = round(avg_time_result / 1000, 2) if avg_time_result else 0
        
        # Language distribution
        urdu_count = db.session.query(func.count(Document.id)).filter(
            Document.detected_language.in_(['ur', 'urd', 'urdu'])
        ).scalar() or 0
        
        hindi_count = db.session.query(func.count(Document.id)).filter(
            Document.detected_language.in_(['hi', 'hin', 'hindi'])
        ).scalar() or 0
        
        english_count = db.session.query(func.count(Document.id)).filter(
            Document.detected_language.in_(['en', 'eng', 'english'])
        ).scalar() or 0
        
        # Unique farmers (from farmer table)
        farmers_registered = db.session.query(func.count(Farmer.id)).scalar() or 0
        
        # Unique parcels
        parcels_linked = db.session.query(func.count(LandParcel.id)).scalar() or 0
        
        # Pending documents
        pending_records = db.session.query(func.count(Document.id)).filter(
            Document.processing_status == 'pending'
        ).scalar() or 0
        
        # Accuracy rate (based on confidence scores)
        avg_confidence = db.session.query(func.avg(Document.ocr_confidence)).filter(
            Document.processing_status == 'processed'
        ).scalar()
        accuracy_rate = round(avg_confidence, 1) if avg_confidence else 0
        
        return jsonify({
            "success": True,
            "data": {
                "total_processed": total_processed,
                "success_rate": round(success_rate, 1),
                "avg_processing_time": avg_processing_time,
                "accuracy_rate": accuracy_rate,
                "farmers_registered": farmers_registered,
                "parcels_linked": parcels_linked,
                "pending_records": pending_records,
                "language_distribution": {
                    "urdu": urdu_count,
                    "hindi": hindi_count,
                    "english": english_count
                }
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {
                "total_processed": 0,
                "success_rate": 0,
                "avg_processing_time": 0,
                "accuracy_rate": 0,
                "farmers_registered": 0,
                "parcels_linked": 0,
                "pending_records": 0,
                "language_distribution": {"urdu": 0, "hindi": 0, "english": 0}
            }
        })

@ocr_bp.route('/documents', methods=['GET'])
def get_documents():
    """Get list of processed documents"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Document.query.order_by(Document.created_at.desc())
        
        if status:
            query = query.filter(Document.processing_status == status)
        
        documents = query.limit(per_page).offset((page - 1) * per_page).all()
        total = query.count()
        
        return jsonify({
            "success": True,
            "data": {
                "documents": [doc.to_dict() for doc in documents],
                "total": total,
                "page": page,
                "per_page": per_page
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@ocr_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Get single document details"""
    try:
        doc = Document.query.get(doc_id)
        if not doc:
            return jsonify({"success": False, "error": "Document not found"}), 404
        
        return jsonify({
            "success": True,
            "data": {
                **doc.to_dict(),
                "ocr_text": doc.ocr_text,
                "translated_text": doc.translated_text
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@ocr_bp.route('/district-progress', methods=['GET'])
def get_district_progress():
    """Get progress by district"""
    try:
        # Group documents by district
        district_stats = db.session.query(
            Document.district,
            func.count(Document.id).label('completed')
        ).filter(
            Document.processing_status == 'processed',
            Document.district.isnot(None)
        ).group_by(Document.district).all()
        
        # Estimated totals per district (you can adjust these)
        district_targets = {
            'Srinagar': 5000,
            'Jammu': 4500,
            'Anantnag': 3000,
            'Baramulla': 2500,
            'Udhampur': 2000,
            'Pulwama': 1500,
            'Budgam': 1500,
            'Kupwara': 1500
        }
        
        progress = []
        for dist, completed in district_stats:
            total = district_targets.get(dist, 1000)
            progress.append({
                'name': dist,
                'total': total,
                'completed': completed,
                'percentage': round((completed / total) * 100, 1) if total > 0 else 0
            })
        
        # Add districts with no processed documents yet
        processed_districts = {p['name'] for p in progress}
        for dist, total in district_targets.items():
            if dist not in processed_districts:
                progress.append({
                    'name': dist,
                    'total': total,
                    'completed': 0,
                    'percentage': 0
                })
        
        # Sort by percentage descending
        progress.sort(key=lambda x: x['percentage'], reverse=True)
        
        return jsonify({
            "success": True,
            "data": progress
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "data": []})
