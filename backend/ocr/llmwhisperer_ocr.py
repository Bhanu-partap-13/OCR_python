"""
LLMWhisperer OCR Implementation
High-quality OCR service optimized for LLM processing
https://unstract.com/llmwhisperer/
"""
import os
import requests
import time
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class LLMWhispererOCR:
    """LLMWhisperer API OCR processor"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLMWhisperer OCR
        Args:
            api_key: LLMWhisperer API Key (optional, can be set via environment)
        """
        self.api_key = api_key or os.environ.get('LLMWHISPERER_API_KEY')
        self.base_url = os.environ.get('LLMWHISPERER_BASE_URL', 'https://llmwhisperer-api.unstract.com/api/v1')
        
        if not self.api_key:
            logger.warning("No LLMWhisperer API Key provided. Set LLMWHISPERER_API_KEY environment variable.")
    
    def process(self, file_path: str, processing_mode: str = "ocr", 
                output_mode: str = "line-printer", force_text_processing: bool = False,
                pages_to_extract: str = "", timeout: int = 200) -> Dict:
        """
        Process document with LLMWhisperer API
        
        Args:
            file_path: Path to the file (PDF, image, etc.)
            processing_mode: "ocr" for OCR, "text" for text extraction
            output_mode: "line-printer" (default) or "text"
            force_text_processing: Force text extraction even for scanned docs
            pages_to_extract: Specific pages to extract (e.g., "1-5,8,11-13")
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with OCR results:
            {
                'text': str,
                'confidence': float,
                'detected_language': str,
                'pages': int,
                'processing_time_ms': int
            }
        """
        if not self.api_key:
            raise ValueError("LLMWhisperer API Key is required. Set LLMWHISPERER_API_KEY environment variable.")
        
        try:
            start_time = time.time()
            
            # Prepare headers
            headers = {
                'unstract-key': self.api_key
            }
            
            # Prepare query parameters
            params = {
                'processing_mode': processing_mode,
                'output_mode': output_mode,
                'force_text_processing': str(force_text_processing).lower(),
                'pages_to_extract': pages_to_extract,
                'timeout': timeout
            }
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Determine content type
            file_ext = os.path.splitext(file_path)[1].lower()
            content_types = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff',
                '.bmp': 'image/bmp',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            content_type = content_types.get(file_ext, 'application/octet-stream')
            
            headers['Content-Type'] = content_type
            
            logger.info(f"Processing with LLMWhisperer: {file_path}, mode: {processing_mode}")
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/whisper",
                headers=headers,
                params=params,
                data=file_data,
                timeout=timeout + 30  # Extra buffer for network
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                
                extracted_text = result.get('extracted_text', '')
                
                # Detect language from text (simple heuristic)
                detected_language = self._detect_language(extracted_text)
                
                # Estimate confidence based on response
                confidence = 85.0  # LLMWhisperer generally has high accuracy
                if result.get('status') == 'processed':
                    confidence = 90.0
                
                return {
                    'text': extracted_text,
                    'confidence': confidence,
                    'detected_language': detected_language,
                    'pages': result.get('page_count', 1),
                    'processing_time_ms': processing_time_ms,
                    'whisper_hash': result.get('whisper_hash', ''),
                    'status': result.get('status', 'completed')
                }
            
            elif response.status_code == 202:
                # Async processing - need to poll for result
                result = response.json()
                whisper_hash = result.get('whisper_hash')
                
                if whisper_hash:
                    # Poll for result
                    return self._poll_for_result(whisper_hash, timeout, start_time)
                else:
                    raise Exception("No whisper_hash returned for async processing")
            
            elif response.status_code == 400:
                error_data = response.json()
                raise Exception(f"Bad request: {error_data.get('message', response.text)}")
            
            elif response.status_code == 401:
                raise Exception("Invalid API key. Please check your LLMWHISPERER_API_KEY.")
            
            elif response.status_code == 402:
                raise Exception("LLMWhisperer API credits exhausted. Please add more credits.")
            
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded. Please try again later.")
            
            else:
                raise Exception(f"LLMWhisperer API error: {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"Network error calling LLMWhisperer API: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error in LLMWhisperer process: {e}")
            raise
    
    def _poll_for_result(self, whisper_hash: str, timeout: int, start_time: float) -> Dict:
        """Poll for async processing result"""
        headers = {'unstract-key': self.api_key}
        
        poll_interval = 5  # seconds
        max_polls = timeout // poll_interval
        
        for _ in range(max_polls):
            time.sleep(poll_interval)
            
            response = requests.get(
                f"{self.base_url}/whisper-status",
                headers=headers,
                params={'whisper_hash': whisper_hash},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                if status == 'processed':
                    # Get the actual text
                    text_response = requests.get(
                        f"{self.base_url}/whisper-retrieve",
                        headers=headers,
                        params={'whisper_hash': whisper_hash},
                        timeout=30
                    )
                    
                    if text_response.status_code == 200:
                        text_result = text_response.json()
                        processing_time_ms = int((time.time() - start_time) * 1000)
                        
                        extracted_text = text_result.get('extracted_text', '')
                        
                        return {
                            'text': extracted_text,
                            'confidence': 90.0,
                            'detected_language': self._detect_language(extracted_text),
                            'pages': text_result.get('page_count', 1),
                            'processing_time_ms': processing_time_ms,
                            'whisper_hash': whisper_hash,
                            'status': 'processed'
                        }
                
                elif status == 'failed':
                    raise Exception(f"Processing failed: {result.get('message', 'Unknown error')}")
        
        raise Exception("Timeout waiting for LLMWhisperer processing")
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection based on character analysis"""
        if not text:
            return 'unknown'
        
        # Count different script characters
        urdu_arabic_chars = 0
        hindi_devanagari_chars = 0
        english_latin_chars = 0
        
        for char in text:
            code = ord(char)
            # Arabic/Urdu script range
            if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
                urdu_arabic_chars += 1
            # Devanagari (Hindi) script range
            elif 0x0900 <= code <= 0x097F:
                hindi_devanagari_chars += 1
            # Latin characters
            elif 0x0041 <= code <= 0x007A:
                english_latin_chars += 1
        
        total = urdu_arabic_chars + hindi_devanagari_chars + english_latin_chars
        if total == 0:
            return 'unknown'
        
        if urdu_arabic_chars > hindi_devanagari_chars and urdu_arabic_chars > english_latin_chars:
            return 'urdu'
        elif hindi_devanagari_chars > urdu_arabic_chars and hindi_devanagari_chars > english_latin_chars:
            return 'hindi'
        else:
            return 'english'
    
    def get_usage(self) -> Dict:
        """Get API usage information"""
        if not self.api_key:
            raise ValueError("LLMWhisperer API Key is required")
        
        headers = {'unstract-key': self.api_key}
        
        response = requests.get(
            f"{self.base_url}/get-usage-info",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get usage info: {response.status_code}")


def process_with_llmwhisperer(file_path: str, processing_mode: str = "ocr") -> Dict:
    """
    Convenience function to process a file with LLMWhisperer
    
    Args:
        file_path: Path to the file
        processing_mode: "ocr" or "text"
        
    Returns:
        OCR result dictionary
    """
    ocr = LLMWhispererOCR()
    return ocr.process(file_path, processing_mode=processing_mode)


# Singleton instance
_llmwhisperer_instance = None

def get_llmwhisperer() -> LLMWhispererOCR:
    """Get singleton LLMWhisperer instance"""
    global _llmwhisperer_instance
    if _llmwhisperer_instance is None:
        _llmwhisperer_instance = LLMWhispererOCR()
    return _llmwhisperer_instance
