"""
Translation module using Google Gemini AI for Urdu/Hindi to English translation.
Falls back to dictionary-based translation if Gemini is unavailable.
"""
import os
import requests
import re
import logging

logger = logging.getLogger(__name__)

# Gemini API configuration
GEMINI_API_KEY = None

# Available Gemini models (in order of preference)
# gemini-2.0-flash is the currently working model
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro", 
]

def get_gemini_api_key():
    """Get Gemini API key from environment or Flask config"""
    global GEMINI_API_KEY
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
    
    # Try to get from environment
    GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY')
    
    # Try Flask config if available
    if not GEMINI_API_KEY:
        try:
            from flask import current_app
            GEMINI_API_KEY = current_app.config.get('GOOGLE_GEMINI_API_KEY')
        except:
            pass
    
    return GEMINI_API_KEY

def translate_with_gemini(text, source_lang="Urdu", target_lang="English"):
    """
    Translate text using Google Gemini AI.
    Optimized for land record terminology.
    Tries multiple model versions for reliability.
    """
    api_key = get_gemini_api_key()
    
    if not api_key:
        return None, "Gemini API key not configured"
    
    # Create a specialized prompt for land record translation
    prompt = f"""You are an expert translator specializing in South Asian languages and land record terminology.

Translate the following {source_lang} text to {target_lang}. This text is from a land record document, so pay special attention to:
- Land measurement units (Kanal, Marla, Bigha, Biswa)
- Administrative terms (Tehsil, Mauza, Patwari, Tehsildar)
- Document types (Jamabandi, Fard, Intiqal, Girdawari)
- Ownership terms (Malik, Qabiz, Waris)
- Legal terms

Provide ONLY the translated text without any explanations or notes.

Text to translate:
{text}

Translation:"""

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.1,  # Low temperature for accurate translation
            "maxOutputTokens": 4096,
        }
    }
    
    last_error = None
    
    # Try each model until one works
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        try:
            logger.info(f"Trying Gemini model: {model}")
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 404:
                logger.warning(f"Model {model} not found, trying next...")
                last_error = f"Model {model} not available"
                continue
                
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                translated = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"Translation successful with model: {model}")
                return translated.strip(), None
            else:
                last_error = "No translation generated"
                continue
                
        except requests.exceptions.Timeout:
            last_error = "Translation request timed out"
            continue
        except requests.exceptions.RequestException as e:
            last_error = f"API request failed: {str(e)}"
            logger.warning(f"Model {model} failed: {e}")
            continue
        except Exception as e:
            last_error = f"Translation error: {str(e)}"
            continue
    
    # All models failed
    return None, last_error

def translate_urdu_to_english(text):
    """
    Main translation function: Urdu to English.
    Uses Gemini AI with fallback to dictionary-based translation.
    """
    if not text or not text.strip():
        return ""
    
    # Try Gemini translation first
    translated, error = translate_with_gemini(text, "Urdu", "English")
    
    if translated:
        return translated
    
    # Fallback to dictionary-based translation
    from translation.simple_translator import apply_domain_terms, LAND_RECORD_TERMS
    
    # Apply known term translations
    result = text
    for term, replacement in LAND_RECORD_TERMS.items():
        result = result.replace(term, f"[{replacement}]")
    
    # If we made any replacements, return the partially translated text
    if result != text:
        return f"(Partial translation - Gemini unavailable: {error})\n\n{result}"
    
    # Return original with error message if no translation possible
    return f"(Translation unavailable: {error})\n\nOriginal text:\n{text}"

def translate_hindi_to_english(text):
    """
    Translate Hindi text to English using Gemini AI.
    """
    if not text or not text.strip():
        return ""
    
    translated, error = translate_with_gemini(text, "Hindi", "English")
    
    if translated:
        return translated
    
    # Fallback
    from translation.simple_translator import apply_domain_terms, LAND_RECORD_TERMS
    result = apply_domain_terms(text)
    
    if result != text:
        return f"(Partial translation - Gemini unavailable: {error})\n\n{result}"
    
    return f"(Translation unavailable: {error})\n\nOriginal text:\n{text}"

def detect_language(text):
    """
    Simple language detection based on character ranges.
    """
    if not text:
        return "unknown"
    
    # Check for Arabic script (Urdu)
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]')
    arabic_chars = len(arabic_pattern.findall(text))
    
    # Check for Devanagari script (Hindi)
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')
    devanagari_chars = len(devanagari_pattern.findall(text))
    
    # Check for Latin characters (English)
    latin_pattern = re.compile(r'[a-zA-Z]')
    latin_chars = len(latin_pattern.findall(text))
    
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    
    if total_chars == 0:
        return "unknown"
    
    # Determine dominant script
    if arabic_chars / total_chars > 0.3:
        return "urdu"
    elif devanagari_chars / total_chars > 0.3:
        return "hindi"
    elif latin_chars / total_chars > 0.5:
        return "english"
    
    return "mixed"

def auto_translate_to_english(text):
    """
    Automatically detect language and translate to English.
    """
    lang = detect_language(text)
    
    if lang == "english":
        return text, "english", None
    elif lang == "urdu":
        translated = translate_urdu_to_english(text)
        return translated, "urdu", None
    elif lang == "hindi":
        translated = translate_hindi_to_english(text)
        return translated, "hindi", None
    else:
        # Try Urdu translation for mixed/unknown
        translated, error = translate_with_gemini(text, "Urdu/Hindi", "English")
        if translated:
            return translated, "mixed", None
        return text, "unknown", "Could not detect language"
