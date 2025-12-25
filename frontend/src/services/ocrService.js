import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await axios.post(`${API_URL}/ocr/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const processOCR = async (filepath) => {
  const response = await axios.post(`${API_URL}/ocr/process`, { filepath });
  return response.data;
};

export const translateText = async (text, sourceLang, targetLang) => {
  const response = await axios.post(`${API_URL}/translate/text`, {
    text,
    source_lang: sourceLang,
    target_lang: targetLang,
  });
  return response.data;
};

// Translate PDF document with domain-specific terms
export const translateDocument = async (file, sourceLang, targetLang) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_lang', sourceLang);
  formData.append('target_lang', targetLang);
  
  const response = await axios.post(`${API_URL}/translate/document`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 300000, // 5 minute timeout for large documents
  });
  return response.data;
};

// Get real-time stats from backend
export const getStats = async () => {
  try {
    const response = await axios.get(`${API_URL}/ocr/stats`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch stats:', error);
    return {
      success: false,
      data: {
        total_processed: 0,
        success_rate: 0,
        avg_processing_time: 0,
        accuracy_rate: 0,
        farmers_registered: 0,
        parcels_linked: 0,
        pending_records: 0,
        language_distribution: { urdu: 0, hindi: 0, english: 0 }
      }
    };
  }
};

// Get list of documents
export const getDocuments = async (page = 1, perPage = 10, status = null) => {
  try {
    const params = new URLSearchParams({ page, per_page: perPage });
    if (status) params.append('status', status);
    
    const response = await axios.get(`${API_URL}/ocr/documents?${params}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch documents:', error);
    return { success: false, data: { documents: [], total: 0 } };
  }
};

// Get single document details
export const getDocument = async (docId) => {
  try {
    const response = await axios.get(`${API_URL}/ocr/documents/${docId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch document:', error);
    return { success: false, error: 'Failed to fetch document' };
  }
};

// Get district progress
export const getDistrictProgress = async () => {
  try {
    const response = await axios.get(`${API_URL}/ocr/district-progress`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch district progress:', error);
    return { success: false, data: [] };
  }
};

// Check backend health
export const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return { status: 'unhealthy' };
  }
};
