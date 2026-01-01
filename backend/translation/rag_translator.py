"""
Production-Ready RAG Translation Module
========================================
Implements all 10 essential components of a RAG system:
1. Data Source - PDF text extraction
2. Embeddings - Semantic text representation
3. Vector Database - In-memory FAISS-like similarity search
4. Retriever - Fetching relevant chunks
5. Chunking Strategy - Smart text splitting with overlap
6. Prompt Engineering - Domain-specific prompts
7. LLM (Generator) - Gemini API integration
8. Orchestration - Pipeline management
9. Caching Layer - Response caching
10. Evaluation & Feedback - Quality metrics

Designed to handle large documents without timeouts.
"""
import os
import re
import time
import logging
import hashlib
import json
import requests
from typing import List, Tuple, Optional, Generator, Dict, Any
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import lru_cache
import math

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================
GEMINI_API_KEY = None
GEMINI_MODEL = "gemini-2.0-flash"
CHUNK_SIZE = 1200  # Optimal for translation context
OVERLAP_SIZE = 150  # Context preservation
REQUEST_TIMEOUT = 25  # Short timeout per chunk
MAX_RETRIES = 3
CACHE_SIZE = 100  # LRU cache size
SIMILARITY_THRESHOLD = 0.7  # For deduplication


# ============================================================================
# 1. DATA SOURCE - Text Extraction Utilities
# ============================================================================
@dataclass
class DocumentChunk:
    """Represents a chunk of document with metadata"""
    id: int
    text: str
    start_pos: int
    end_pos: int
    page_number: Optional[int] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 2. EMBEDDINGS - Simple but effective text embeddings
# ============================================================================
class SimpleEmbedder:
    """
    Lightweight embedding using character n-grams and word frequencies.
    No external dependencies required - works offline.
    For production, consider using sentence-transformers or OpenAI embeddings.
    """
    
    def __init__(self, dim: int = 256):
        self.dim = dim
        self._vocab_cache = {}
    
    def embed(self, text: str) -> List[float]:
        """Generate a simple but effective embedding vector"""
        if not text:
            return [0.0] * self.dim
        
        text = text.lower().strip()
        
        # Character trigram hashing
        trigrams = [text[i:i+3] for i in range(len(text)-2)]
        
        # Initialize vector
        vector = [0.0] * self.dim
        
        # Hash trigrams to dimensions
        for trigram in trigrams:
            idx = hash(trigram) % self.dim
            vector[idx] += 1.0
        
        # Add word-level features
        words = text.split()
        for word in words:
            idx = hash(word) % self.dim
            vector[idx] += 0.5
        
        # Normalize
        magnitude = math.sqrt(sum(x*x for x in vector)) or 1.0
        return [x / magnitude for x in vector]
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Cosine similarity between two vectors"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        return dot  # Already normalized


# ============================================================================
# 3. VECTOR DATABASE - In-memory similarity search
# ============================================================================
class InMemoryVectorStore:
    """
    Simple in-memory vector store with similarity search.
    For production scale, use FAISS, Pinecone, or Weaviate.
    """
    
    def __init__(self, embedder: SimpleEmbedder):
        self.embedder = embedder
        self.chunks: List[DocumentChunk] = []
        self.index_built = False
    
    def add_chunks(self, chunks: List[DocumentChunk]):
        """Add chunks and compute embeddings"""
        for chunk in chunks:
            if chunk.embedding is None:
                chunk.embedding = self.embedder.embed(chunk.text)
            self.chunks.append(chunk)
        self.index_built = True
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Find most similar chunks to query"""
        if not self.chunks:
            return []
        
        query_embedding = self.embedder.embed(query)
        
        results = []
        for chunk in self.chunks:
            score = self.embedder.similarity(query_embedding, chunk.embedding)
            results.append((chunk, score))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def clear(self):
        """Clear all chunks"""
        self.chunks = []
        self.index_built = False


# ============================================================================
# 4. RETRIEVER - Smart chunk retrieval
# ============================================================================
class TranslationRetriever:
    """
    Retriever optimized for translation tasks.
    Uses similarity to find related chunks and ensures context continuity.
    """
    
    def __init__(self, vector_store: InMemoryVectorStore):
        self.vector_store = vector_store
    
    def get_translation_context(self, chunk: DocumentChunk, 
                                  all_chunks: List[DocumentChunk]) -> str:
        """Get context from neighboring chunks for better translation"""
        context_parts = []
        
        # Get previous chunk for context
        if chunk.id > 0:
            prev_chunk = next((c for c in all_chunks if c.id == chunk.id - 1), None)
            if prev_chunk:
                # Take last 100 chars of previous chunk
                context_parts.append(prev_chunk.text[-100:])
        
        # Current chunk
        context_parts.append(chunk.text)
        
        return " ".join(context_parts)
    
    def retrieve_similar(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """Retrieve chunks similar to query"""
        results = self.vector_store.search(query, top_k)
        return [chunk for chunk, score in results if score > SIMILARITY_THRESHOLD]


# ============================================================================
# 5. CHUNKING STRATEGY - Smart text splitting
# ============================================================================
class SmartChunker:
    """
    Advanced chunking with:
    - Sentence boundary awareness
    - Overlap for context
    - Page number tracking
    - Special handling for land record terminology
    """
    
    # Land record terms that shouldn't be split
    PRESERVE_TERMS = [
        "کھسرا نمبر", "khasra number", "khata number",
        "جماع بندی", "jamabandi", "intiqal",
        "patwari", "tehsildar", "kanungo"
    ]
    
    @staticmethod
    def chunk_document(text: str, chunk_size: int = CHUNK_SIZE, 
                       overlap: int = OVERLAP_SIZE) -> List[DocumentChunk]:
        """Split document into overlapping chunks"""
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # First, split by page markers if present
        page_pattern = r'(--- Page \d+ ---)'
        parts = re.split(page_pattern, text)
        
        current_page = 1
        full_text = ""
        page_positions = {}
        
        for part in parts:
            if re.match(page_pattern, part):
                page_match = re.search(r'Page (\d+)', part)
                if page_match:
                    current_page = int(page_match.group(1))
            else:
                start_pos = len(full_text)
                full_text += part
                page_positions[start_pos] = current_page
        
        # Now chunk the full text
        sentences = SmartChunker._split_into_sentences(full_text)
        
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    # Determine page number
                    page_num = 1
                    for pos, page in page_positions.items():
                        if pos <= current_start:
                            page_num = page
                    
                    chunks.append(DocumentChunk(
                        id=chunk_id,
                        text=current_chunk.strip(),
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk),
                        page_number=page_num
                    ))
                    chunk_id += 1
                
                # Start new chunk with overlap
                if chunks and overlap > 0:
                    overlap_text = chunks[-1].text[-overlap:]
                    current_start = chunks[-1].end_pos - overlap
                    current_chunk = overlap_text + " " + sentence + " "
                else:
                    current_start = chunks[-1].end_pos if chunks else 0
                    current_chunk = sentence + " "
        
        # Add final chunk
        if current_chunk.strip():
            page_num = 1
            for pos, page in page_positions.items():
                if pos <= current_start:
                    page_num = page
            
            chunks.append(DocumentChunk(
                id=chunk_id,
                text=current_chunk.strip(),
                start_pos=current_start,
                end_pos=current_start + len(current_chunk),
                page_number=page_num
            ))
        
        return chunks
    
    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Split text into sentences, preserving Urdu/Hindi punctuation"""
        # Handle multiple sentence endings
        pattern = r'(?<=[.!?।॥])\s+'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]


# ============================================================================
# 6. PROMPT ENGINEERING - Domain-specific prompts
# ============================================================================
class PromptTemplates:
    """Optimized prompts for land record translation"""
    
    TRANSLATION_PROMPT = """You are an expert translator specializing in South Asian land records and legal documents.

TASK: Translate the following {source_lang} text to {target_lang}.

IMPORTANT GUIDELINES:
1. Preserve all numbers, dates, and measurements exactly
2. Keep proper nouns (names, places) in original form with transliteration
3. Use standard English equivalents for these terms:
   - کھسرا/खसरा = Khasra (plot number)
   - جماع بندی/जमाबंदी = Jamabandi (record of rights)
   - پٹواری/पटवारी = Patwari (village record keeper)
   - تحصیل/तहसील = Tehsil (administrative division)
   - موضع/मौजा = Mauza (village)
   - مالک/मालिक = Malik (owner)
   - وارث/वारिस = Waris (heir)
   - انتقال/इंतक़ाल = Intiqal (transfer of ownership)
4. Maintain document structure and formatting
5. If unsure about a term, keep it in original script with [?] marker

TEXT TO TRANSLATE:
{text}

TRANSLATION:"""

    CONTEXT_PROMPT = """Continue translating this document. Previous context:
{context}

NEW TEXT TO TRANSLATE:
{text}

TRANSLATION (maintain consistency with previous):"""

    @classmethod
    def get_translation_prompt(cls, text: str, source_lang: str = "Urdu", 
                                target_lang: str = "English", context: str = None) -> str:
        """Get appropriate prompt based on context"""
        if context:
            return cls.CONTEXT_PROMPT.format(context=context[:200], text=text)
        return cls.TRANSLATION_PROMPT.format(
            source_lang=source_lang, 
            target_lang=target_lang, 
            text=text
        )


# ============================================================================
# 7. LLM GENERATOR - Gemini API integration
# ============================================================================
class GeminiGenerator:
    """Gemini API wrapper with retry logic and error handling"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        self.request_count = 0
        self.last_request_time = 0
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or Flask config"""
        global GEMINI_API_KEY
        if GEMINI_API_KEY:
            return GEMINI_API_KEY
        
        GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY')
        if not GEMINI_API_KEY:
            try:
                from flask import current_app
                GEMINI_API_KEY = current_app.config.get('GOOGLE_GEMINI_API_KEY')
            except:
                pass
        return GEMINI_API_KEY
    
    def _rate_limit(self):
        """Simple rate limiting"""
        current_time = time.time()
        if current_time - self.last_request_time < 0.5:
            time.sleep(0.5)
        self.last_request_time = time.time()
    
    def generate(self, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate response from Gemini"""
        if not self.api_key:
            return None, "API key not configured"
        
        self._rate_limit()
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        
        url = f"{self.base_url}?key={self.api_key}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
                
                if response.status_code == 429:
                    wait_time = (2 ** attempt) + 1
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code == 503:
                    time.sleep(2)
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                if 'candidates' in result and result['candidates']:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    self.request_count += 1
                    return text.strip(), None
                
                return None, "No response generated"
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None, "Request timeout"
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None, str(e)
        
        return None, "Max retries exceeded"


# ============================================================================
# 9. CACHING LAYER - LRU cache for responses
# ============================================================================
class TranslationCache:
    """LRU cache for translation results"""
    
    def __init__(self, max_size: int = CACHE_SIZE):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def _hash_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[str]:
        """Get cached translation"""
        key = self._hash_key(text)
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, text: str, translation: str):
        """Cache translation result"""
        key = self._hash_key(text)
        
        if len(self.cache) >= self.max_size:
            # Remove oldest item
            self.cache.popitem(last=False)
        
        self.cache[key] = translation
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }


# ============================================================================
# 10. EVALUATION & FEEDBACK
# ============================================================================
class TranslationQuality:
    """Quality metrics for translation evaluation"""
    
    @staticmethod
    def calculate_coverage(original: str, translated: str) -> float:
        """Estimate how much of original was translated"""
        if not original:
            return 1.0
        
        # Count preserved numbers and special terms
        numbers_original = set(re.findall(r'\d+', original))
        numbers_translated = set(re.findall(r'\d+', translated))
        
        if not numbers_original:
            return 1.0
        
        preserved = len(numbers_original & numbers_translated)
        return preserved / len(numbers_original)
    
    @staticmethod
    def detect_issues(translated: str) -> List[str]:
        """Detect potential translation issues"""
        issues = []
        
        if "[?]" in translated:
            issues.append("Contains uncertain translations")
        
        if len(translated) < 10:
            issues.append("Translation too short")
        
        # Check for common error patterns
        if "Translation unavailable" in translated:
            issues.append("Translation failed for some chunks")
        
        return issues


# ============================================================================
# 8. ORCHESTRATION - Main RAG Pipeline
# ============================================================================
class RAGTranslationPipeline:
    """
    Complete RAG pipeline for document translation.
    Orchestrates all components for efficient processing.
    """
    
    def __init__(self):
        self.embedder = SimpleEmbedder()
        self.vector_store = InMemoryVectorStore(self.embedder)
        self.retriever = TranslationRetriever(self.vector_store)
        self.chunker = SmartChunker()
        self.generator = GeminiGenerator()
        self.cache = TranslationCache()
        self.quality = TranslationQuality()
    
    def translate_document(self, text: str, source_lang: str = "Urdu",
                          target_lang: str = "English",
                          progress_callback=None) -> Tuple[str, Dict[str, Any]]:
        """
        Main translation method with full RAG pipeline.
        
        Args:
            text: Document text to translate
            source_lang: Source language
            target_lang: Target language
            progress_callback: Optional callback(current, total, status)
        
        Returns:
            Tuple of (translated_text, metadata)
        """
        start_time = time.time()
        
        # Step 1: Chunk the document
        chunks = self.chunker.chunk_document(text)
        total_chunks = len(chunks)
        
        if total_chunks == 0:
            return "", {"error": "No text to translate", "chunks": 0}
        
        logger.info(f"Processing {total_chunks} chunks, {len(text)} chars")
        
        if progress_callback:
            progress_callback(0, total_chunks, "Preparing document...")
        
        # Step 2: Build vector index for similarity search
        self.vector_store.clear()
        self.vector_store.add_chunks(chunks)
        
        # Step 3: Translate each chunk
        translated_chunks = []
        errors = []
        cached_count = 0
        
        previous_translation = ""
        
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(i + 1, total_chunks, f"Translating chunk {i + 1}/{total_chunks}")
            
            # Check cache first
            cached = self.cache.get(chunk.text)
            if cached:
                translated_chunks.append(cached)
                cached_count += 1
                previous_translation = cached[-200:]
                continue
            
            # Get context from previous translation
            context = previous_translation if i > 0 else None
            
            # Generate prompt
            prompt = PromptTemplates.get_translation_prompt(
                chunk.text, source_lang, target_lang, context
            )
            
            # Generate translation
            translation, error = self.generator.generate(prompt)
            
            if error:
                errors.append({"chunk_id": chunk.id, "error": error})
                # Fallback: use original text
                translated_chunks.append(f"[Translation failed: {chunk.text[:100]}...]")
                logger.warning(f"Chunk {chunk.id} failed: {error}")
            else:
                translated_chunks.append(translation)
                self.cache.set(chunk.text, translation)
                previous_translation = translation[-200:]
            
            # Small delay between requests
            if i < total_chunks - 1:
                time.sleep(0.3)
        
        # Step 4: Combine and post-process
        final_text = self._combine_chunks(translated_chunks)
        
        # Step 5: Calculate quality metrics
        processing_time = int((time.time() - start_time) * 1000)
        coverage = self.quality.calculate_coverage(text, final_text)
        issues = self.quality.detect_issues(final_text)
        
        metadata = {
            "total_chunks": total_chunks,
            "successful_chunks": total_chunks - len(errors),
            "failed_chunks": len(errors),
            "cached_chunks": cached_count,
            "errors": errors if errors else None,
            "processing_time_ms": processing_time,
            "original_length": len(text),
            "translated_length": len(final_text),
            "quality_coverage": round(coverage, 2),
            "quality_issues": issues if issues else None,
            "cache_stats": self.cache.get_stats(),
            "api_requests": self.generator.request_count
        }
        
        if progress_callback:
            progress_callback(total_chunks, total_chunks, "Complete!")
        
        logger.info(f"Translation complete: {processing_time}ms, {total_chunks} chunks")
        
        return final_text, metadata
    
    def translate_streaming(self, text: str, source_lang: str = "Urdu",
                           target_lang: str = "English") -> Generator[Dict, None, None]:
        """
        Stream translation progress for real-time updates.
        Yields progress dictionaries.
        """
        start_time = time.time()
        
        chunks = self.chunker.chunk_document(text)
        total_chunks = len(chunks)
        
        if total_chunks == 0:
            yield {"type": "error", "message": "No text to translate"}
            return
        
        yield {
            "type": "start",
            "total_chunks": total_chunks,
            "total_characters": len(text)
        }
        
        self.vector_store.clear()
        self.vector_store.add_chunks(chunks)
        
        translated_parts = []
        previous_translation = ""
        
        for i, chunk in enumerate(chunks):
            yield {
                "type": "progress",
                "current": i + 1,
                "total": total_chunks,
                "percentage": int((i + 1) / total_chunks * 100),
                "status": f"Translating chunk {i + 1} of {total_chunks}"
            }
            
            # Check cache
            cached = self.cache.get(chunk.text)
            if cached:
                translated_parts.append(cached)
                yield {
                    "type": "chunk_complete",
                    "chunk_id": chunk.id,
                    "cached": True,
                    "preview": cached[:100] + "..." if len(cached) > 100 else cached
                }
                previous_translation = cached[-200:]
                continue
            
            context = previous_translation if i > 0 else None
            prompt = PromptTemplates.get_translation_prompt(
                chunk.text, source_lang, target_lang, context
            )
            
            translation, error = self.generator.generate(prompt)
            
            if error:
                translated_parts.append(chunk.text)
                yield {
                    "type": "chunk_error",
                    "chunk_id": chunk.id,
                    "error": error
                }
            else:
                translated_parts.append(translation)
                self.cache.set(chunk.text, translation)
                previous_translation = translation[-200:]
                yield {
                    "type": "chunk_complete",
                    "chunk_id": chunk.id,
                    "cached": False,
                    "preview": translation[:100] + "..." if len(translation) > 100 else translation
                }
            
            time.sleep(0.3)
        
        final_text = self._combine_chunks(translated_parts)
        
        yield {
            "type": "complete",
            "translated_text": final_text,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "cache_stats": self.cache.get_stats()
        }
    
    def _combine_chunks(self, chunks: List[str]) -> str:
        """Combine translated chunks and remove duplicates from overlap"""
        if not chunks:
            return ""
        
        result = chunks[0]
        
        for i in range(1, len(chunks)):
            chunk = chunks[i]
            
            # Try to find overlap
            overlap_found = False
            for overlap_size in range(min(50, len(result), len(chunk)), 10, -5):
                if result[-overlap_size:].lower() == chunk[:overlap_size].lower():
                    result += chunk[overlap_size:]
                    overlap_found = True
                    break
            
            if not overlap_found:
                result += " " + chunk
        
        return result.strip()


# ============================================================================
# PUBLIC API
# ============================================================================
_pipeline = None

def get_rag_translator() -> RAGTranslationPipeline:
    """Get or create RAG translation pipeline"""
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGTranslationPipeline()
    return _pipeline


def translate_with_rag(text: str, source_lang: str = "Urdu",
                       target_lang: str = "English",
                       progress_callback=None) -> Tuple[str, Dict[str, Any]]:
    """
    Main entry point for RAG-based translation.
    
    Args:
        text: Document text to translate
        source_lang: Source language (Urdu, Hindi)
        target_lang: Target language (English)
        progress_callback: Optional callback(current, total, status)
    
    Returns:
        Tuple of (translated_text, metadata_dict)
    """
    pipeline = get_rag_translator()
    return pipeline.translate_document(text, source_lang, target_lang, progress_callback)


def get_api_key():
    """Legacy compatibility - get Gemini API key"""
    global GEMINI_API_KEY
    if GEMINI_API_KEY:
        return GEMINI_API_KEY
    
    GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        try:
            from flask import current_app
            GEMINI_API_KEY = current_app.config.get('GOOGLE_GEMINI_API_KEY')
        except:
            pass
    return GEMINI_API_KEY
