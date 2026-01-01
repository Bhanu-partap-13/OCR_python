from flask import Blueprint, request, jsonify, send_file, Response, stream_with_context
import os
import time
import io
import json
import fitz  # PyMuPDF for PDF parsing
from datetime import datetime
from translation.ai4bharat_translator import (
    translate_urdu_to_english, 
    translate_hindi_to_english,
    auto_translate_to_english,
    detect_language
)
from translation.rag_translator import translate_with_rag, get_rag_translator
from translation.simple_translator import apply_domain_terms, LAND_RECORD_TERMS
from document.translation_pdf_generator import generate_translation_pdf
from document.data_organizer import organize_translated_data

translation_bp = Blueprint('translation', __name__)

@translation_bp.route('', methods=['POST'])
@translation_bp.route('/', methods=['POST'])
def translate_file():
    """Main translation endpoint - handles file uploads and routes to appropriate handler"""
    if 'file' in request.files:
        # File upload - route to document translation
        return translate_document()
    elif request.is_json:
        # JSON body - route to text translation
        return translate_text()
    else:
        return jsonify({"success": False, "error": "No file or text provided"}), 400

@translation_bp.route('/text', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text')
    source_lang = data.get('source_lang', 'auto')
    target_lang = data.get('target_lang', 'en')
    
    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400
        
    try:
        start_time = time.time()
        
        # Auto-detect language if not specified
        if source_lang == 'auto':
            detected_lang = detect_language(text)
        else:
            detected_lang = source_lang
        
        # Translate based on detected/specified language
        if detected_lang == 'en' or detected_lang == 'english':
            translated_text = text  # Already in English
        elif detected_lang == 'ur' or detected_lang == 'urdu':
            translated_text = translate_urdu_to_english(text)
        elif detected_lang == 'hi' or detected_lang == 'hindi':
            translated_text = translate_hindi_to_english(text)
        else:
            # Try auto translation for unknown languages
            translated_text, detected_lang, error = auto_translate_to_english(text)
        
        # Apply domain-specific land record terms
        translated_text = apply_domain_terms(translated_text)
        
        # Find which domain terms were applied
        terms_applied = []
        for term in LAND_RECORD_TERMS.keys():
            if term in text:
                terms_applied.append(LAND_RECORD_TERMS[term])
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            "success": True, 
            "data": {
                "translated": translated_text,
                "detected_language": detected_lang,
                "domain_terms_applied": terms_applied,
                "processing_time_ms": processing_time
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@translation_bp.route('/document', methods=['POST'])
def translate_document():
    """Translate PDF document using RAG-based chunking to avoid timeouts"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    source_lang = request.form.get('source_lang', 'ur')
    target_lang = request.form.get('target_lang', 'en')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"success": False, "error": "Only PDF files are supported"}), 400
    
    try:
        start_time = time.time()
        
        # Read PDF content
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        total_pages = len(doc)
        extracted_text = []
        
        # Extract text from each page
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
        
        doc.close()
        
        # Combine all text
        full_text = "\n\n".join(extracted_text)
        
        if not full_text.strip():
            return jsonify({
                "success": False, 
                "error": "No text could be extracted from the PDF. The document may be scanned images. Please use OCR first."
            }), 400
        
        # Use RAG-based translation for efficient processing
        source_lang_name = "Urdu" if source_lang in ['ur', 'urdu'] else "Hindi" if source_lang in ['hi', 'hindi'] else "Urdu"
        translated_text, metadata = translate_with_rag(full_text, source_lang_name, "English")
        
        # Apply domain-specific land record terms
        translated_text = apply_domain_terms(translated_text)
        
        # Find which domain terms were applied
        terms_applied = []
        for term, replacement in LAND_RECORD_TERMS.items():
            if term in full_text:
                terms_applied.append(replacement)
        
        processing_time = metadata.get('processing_time_ms', int((time.time() - start_time) * 1000))
        
        # Check if PDF output is requested
        output_format = request.form.get('output_format', 'json')
        
        if output_format == 'pdf':
            # Generate organized PDF using enhanced generator
            pdf_buffer = generate_translation_pdf(
                translated_text=translated_text,
                original_text=full_text[:3000],
                source_lang=source_lang_name,
                target_lang="English",
                total_pages=total_pages,
                filename=file.filename
            )
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'translated_document_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
        
        # Organize the translated data for JSON response
        organized_data = organize_translated_data(translated_text)
        
        return jsonify({
            "success": True,
            "data": {
                "translated_text": translated_text,
                "original_text": full_text[:2000] + ("..." if len(full_text) > 2000 else ""),
                "pages_processed": total_pages,
                "total_characters": len(full_text),
                "chunks_processed": metadata.get('total_chunks', 1),
                "domain_terms_applied": list(set(terms_applied)),
                "processing_time_ms": processing_time,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "extracted_fields": organized_data.get('extracted_fields', {}),
                "summary": organized_data.get('summary', ''),
                "has_structured_data": len(organized_data.get('extracted_fields', {})) > 0
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@translation_bp.route('/document/stream', methods=['POST'])
def translate_document_stream():
    """Stream translation progress for real-time updates"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    
    file = request.files['file']
    source_lang = request.form.get('source_lang', 'ur')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    try:
        # Read PDF content
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        total_pages = len(doc)
        extracted_text = []
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                extracted_text.append(text)
        
        doc.close()
        full_text = "\n\n".join(extracted_text)
        
        if not full_text.strip():
            return jsonify({"success": False, "error": "No text could be extracted"}), 400
        
        source_lang_name = "Urdu" if source_lang in ['ur', 'urdu'] else "Hindi"
        translator = get_rag_translator()
        
        def generate():
            for update in translator.translate_document_streaming(full_text, source_lang_name, "English"):
                yield f"data: {json.dumps(update)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@translation_bp.route('/terms', methods=['GET'])
def get_domain_terms():
    """Get list of supported domain-specific land record terms"""
    return jsonify({
        "success": True,
        "data": {
            "terms": LAND_RECORD_TERMS,
            "count": len(LAND_RECORD_TERMS)
        }
    })
