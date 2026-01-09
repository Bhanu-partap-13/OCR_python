"""
Lightweight OCR module using Google Vision API with API Key authentication
"""
import os
import base64
import requests
import logging

logger = logging.getLogger(__name__)


def get_api_key():
    """Get Google Vision API key from environment."""
    api_key = os.environ.get('GOOGLE_VISION_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_VISION_API_KEY environment variable not set")
    return api_key


def extract_text(image_bytes):
    """
    Extracts text from an image using Google Cloud Vision API with API Key.
    """
    result = extract_text_with_details(image_bytes)
    return result.get('text', '')


def extract_text_with_details(image_bytes, language_hints=None):
    """
    Extracts text from an image using Google Cloud Vision REST API with language detection.
    Returns text, detected language, and confidence score.
    
    Args:
        image_bytes: Raw image bytes
        language_hints: List of language codes (e.g., ['ur', 'hi', 'en'])
        
    Returns:
        Dictionary with text, detected_language, and confidence
    """
    api_key = get_api_key()
    vision_api_url = 'https://vision.googleapis.com/v1/images:annotate'
    
    if language_hints is None:
        language_hints = ['ur', 'hi', 'en', 'pa']
    
    try:
        # Encode image to base64
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build request payload
        request_payload = {
            "requests": [
                {
                    "image": {
                        "content": encoded_image
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",
                            "maxResults": 1
                        }
                    ],
                    "imageContext": {
                        "languageHints": language_hints
                    }
                }
            ]
        }
        
        # Make API request
        response = requests.post(
            f"{vision_api_url}?key={api_key}",
            json=request_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code != 200:
            error_msg = f"Vision API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        result = response.json()
        
        # Parse response
        if 'responses' not in result or not result['responses']:
            return {'text': '', 'detected_language': 'unknown', 'confidence': 0.0}
        
        annotation = result['responses'][0]
        
        # Check for errors in response
        if 'error' in annotation:
            error_msg = annotation['error'].get('message', 'Unknown Vision API error')
            logger.error(f"Vision API returned error: {error_msg}")
            raise Exception(error_msg)
        
        # Get full text
        text = ''
        if 'fullTextAnnotation' in annotation:
            text = annotation['fullTextAnnotation'].get('text', '')
        elif 'textAnnotations' in annotation and annotation['textAnnotations']:
            text = annotation['textAnnotations'][0].get('description', '')
        
        # Detect language
        detected_language = 'unknown'
        confidence = 0.0
        
        if 'fullTextAnnotation' in annotation:
            full_annotation = annotation['fullTextAnnotation']
            if 'pages' in full_annotation and full_annotation['pages']:
                page = full_annotation['pages'][0]
                
                # Get detected languages
                if 'property' in page and 'detectedLanguages' in page['property']:
                    lang_info = page['property']['detectedLanguages'][0]
                    detected_language = lang_info.get('languageCode', 'unknown')
                    confidence = lang_info.get('confidence', 0.0) * 100
                
                # Calculate confidence from blocks if not available
                if confidence == 0 and 'blocks' in page:
                    total_confidence = 0
                    block_count = 0
                    for block in page['blocks']:
                        if 'confidence' in block:
                            total_confidence += block['confidence']
                            block_count += 1
                    if block_count > 0:
                        confidence = (total_confidence / block_count) * 100
        
        # Map language codes to standard names
        lang_map = {
            'ur': 'urdu',
            'hi': 'hindi', 
            'en': 'english',
            'pa': 'punjabi',
            'ks': 'kashmiri',
            'ar': 'arabic'
        }
        detected_language = lang_map.get(detected_language, detected_language)
        
        return {
            'text': text,
            'detected_language': detected_language,
            'confidence': round(confidence, 1)
        }
        
    except requests.RequestException as e:
        logger.error(f"Network error calling Vision API: {e}")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in extract_text_with_details: {e}")
        raise
