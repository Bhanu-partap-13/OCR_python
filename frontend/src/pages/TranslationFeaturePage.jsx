import React, { useState, useRef } from 'react';
// eslint-disable-next-line no-unused-vars
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Languages, Upload, ArrowRight, FileText, CheckCircle, Loader2, Download, Sparkles, Zap, Table, MapPin, User, Calendar, Hash } from 'lucide-react';
import Footer from '../components/Footer';
import Navbar from '../components/Navbar';
import axios from 'axios';

const TranslationFeaturePage = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, status: '', percentage: 0 });
  const abortControllerRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      setError(null);
      setProgress({ current: 0, total: 0, status: '', percentage: 0 });
    }
  };

  const handleTranslate = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setProgress({ current: 0, total: 0, status: 'Uploading document...', percentage: 5 });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      
      // Use regular endpoint with timeout handling
      setProgress({ current: 0, total: 1, status: 'Processing with AI...', percentage: 20 });
      
      const response = await axios.post(`${apiUrl}/api/translate`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000, // 10 minutes for large documents
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(prev => ({ ...prev, status: `Uploading: ${percentCompleted}%`, percentage: Math.min(percentCompleted / 5, 15) }));
        }
      });
      
      setProgress({ current: 1, total: 1, status: 'Complete!', percentage: 100 });
      
      // Handle response data structure
      if (response.data.success && response.data.data) {
        setResult({
          translated_text: response.data.data.translated_text,
          original_text: response.data.data.original_text,
          pages_processed: response.data.data.pages_processed,
          processing_time_ms: response.data.data.processing_time_ms
        });
      } else {
        setResult(response.data);
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('Translation is taking longer than expected. Please try with a smaller document.');
      } else {
        setError(err.response?.data?.error || 'Translation failed. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadText = () => {
    if (!result) return;
    
    const blob = new Blob([result.translated_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'translated_text.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPdf = async () => {
    if (!file) return;
    
    setDownloadingPdf(true);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
      const formData = new FormData();
      formData.append('file', file);
      formData.append('output_format', 'pdf');
      
      const response = await axios.post(`${apiUrl}/api/translate`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `translated_document_${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download PDF. Please try again.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  return (
    <div className="min-h-screen bg-white text-[#292929]">
      <Navbar />
      
      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-[#292929] mb-6">
              <Languages className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              AI-Powered Translation
            </h1>
            <p className="text-xl text-[#292929] max-w-3xl mx-auto">
              Translate Urdu and Hindi land records to English instantly with AI4Bharat's state-of-the-art models
            </p>
          </motion.div>
        </div>
      </section>

      {/* Upload & Translation Section */}
      <section className="py-20 px-4 bg-neutral-50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12">Try Translation Now</h2>
          
          <div className="bg-white rounded-2xl p-8 shadow-xl">
            {/* Upload Area */}
            <div className="mb-8">
              <label className="block text-sm font-semibold mb-4">Upload Document</label>
              <div className="border-2 border-dashed border-neutral-300 rounded-xl p-12 text-center hover:border-[#292929] transition-colors cursor-pointer">
                <input
                  type="file"
                  onChange={handleFileChange}
                  accept=".pdf,.jpg,.jpeg,.png,.txt"
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-16 h-16 mx-auto mb-4 text-neutral-400" />
                  <p className="text-lg font-semibold mb-2">
                    {file ? file.name : 'Click to upload or drag and drop'}
                  </p>
                  <p className="text-sm text-neutral-500">
                    PDF, JPEG, PNG, or TXT (Max 50MB)
                  </p>
                </label>
              </div>
            </div>

            {/* Translate Button */}
            <button
              onClick={handleTranslate}
              disabled={!file || uploading}
              className="w-full py-4 bg-[#292929] text-white rounded-xl font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 transition-transform flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Translating...
                </>
              ) : (
                <>
                  <Languages className="w-5 h-5" />
                  Translate to English
                </>
              )}
            </button>

            {/* Processing Animation */}
            <AnimatePresence>
              {uploading && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-6 bg-gradient-to-r from-neutral-50 to-neutral-100 rounded-xl p-6 border border-neutral-200"
                >
                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-medium text-neutral-700">{progress.status || 'Processing...'}</span>
                      <span className="text-neutral-500">{progress.percentage}%</span>
                    </div>
                    <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-gradient-to-r from-[#292929] to-[#444]"
                        initial={{ width: '0%' }}
                        animate={{ width: `${progress.percentage}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                      />
                    </div>
                  </div>

                  {/* Animated Processing Visual */}
                  <div className="flex items-center justify-center py-8">
                    <div className="relative">
                      {/* Outer ring */}
                      <motion.div
                        className="w-24 h-24 rounded-full border-4 border-neutral-200"
                        style={{ borderTopColor: '#292929', borderRightColor: '#292929' }}
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                      />
                      
                      {/* Inner content */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                        >
                          <Languages className="w-8 h-8 text-[#292929]" />
                        </motion.div>
                      </div>
                      
                      {/* Floating particles */}
                      {[...Array(6)].map((_, i) => (
                        <motion.div
                          key={i}
                          className="absolute w-2 h-2 bg-[#292929] rounded-full"
                          style={{
                            top: '50%',
                            left: '50%',
                          }}
                          animate={{
                            x: [0, Math.cos(i * 60 * Math.PI / 180) * 50, 0],
                            y: [0, Math.sin(i * 60 * Math.PI / 180) * 50, 0],
                            opacity: [0, 1, 0],
                            scale: [0.5, 1, 0.5],
                          }}
                          transition={{
                            duration: 2,
                            repeat: Infinity,
                            delay: i * 0.2,
                            ease: 'easeInOut',
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Status Messages */}
                  <div className="flex items-center justify-center gap-2 text-sm text-neutral-600">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    >
                      AI is processing your document in chunks for accuracy...
                    </motion.span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl"
              >
                {error}
              </motion.div>
            )}

            {/* Results */}
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="mt-8 space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="w-5 h-5" />
                      <span className="font-semibold">Translation Complete!</span>
                    </div>
                    {result.processing_time_ms && (
                      <div className="flex items-center gap-1 text-sm text-neutral-500">
                        <Zap className="w-4 h-4" />
                        <span>{(result.processing_time_ms / 1000).toFixed(1)}s</span>
                      </div>
                    )}
                  </div>

                  {/* Document Summary */}
                  {result.summary && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-gradient-to-r from-[#292929] to-[#444] text-white rounded-xl p-4"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <Sparkles className="w-5 h-5 text-amber-400" />
                        <span className="font-semibold">Document Summary</span>
                      </div>
                      <p className="text-sm opacity-90">{result.summary}</p>
                    </motion.div>
                  )}

                  {/* Extracted Fields Table */}
                  {result.extracted_fields && Object.keys(result.extracted_fields).length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 }}
                    >
                      <h3 className="font-bold mb-3 flex items-center gap-2">
                        <Table className="w-5 h-5" />
                        Extracted Information
                      </h3>
                      <div className="bg-neutral-50 rounded-xl border border-neutral-200 overflow-hidden">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
                          {Object.entries(result.extracted_fields).map(([key, values], index) => {
                            const fieldIcons = {
                              survey_number: <Hash className="w-4 h-4" />,
                              owner_name: <User className="w-4 h-4" />,
                              village: <MapPin className="w-4 h-4" />,
                              tehsil: <MapPin className="w-4 h-4" />,
                              district: <MapPin className="w-4 h-4" />,
                              date: <Calendar className="w-4 h-4" />,
                            };
                            const fieldLabels = {
                              survey_number: 'Survey/Khasra No.',
                              owner_name: 'Owner Name',
                              father_name: "Father's Name",
                              village: 'Village',
                              tehsil: 'Tehsil',
                              district: 'District',
                              state: 'State',
                              area: 'Land Area',
                              land_type: 'Land Type',
                              revenue: 'Revenue',
                              date: 'Date',
                              registration_number: 'Reg. No.',
                            };
                            return (
                              <div
                                key={key}
                                className={`flex items-start gap-3 p-3 ${
                                  index % 2 === 0 ? 'bg-white' : 'bg-neutral-50'
                                } border-b border-neutral-100`}
                              >
                                <span className="text-neutral-400 mt-0.5">
                                  {fieldIcons[key] || <FileText className="w-4 h-4" />}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs text-neutral-500 font-medium uppercase tracking-wide">
                                    {fieldLabels[key] || key.replace(/_/g, ' ')}
                                  </p>
                                  <p className="text-sm font-semibold text-neutral-800 truncate">
                                    {Array.isArray(values) ? values.join(', ') : values}
                                  </p>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Original Text */}
                  <div>
                    <h3 className="font-bold mb-2 flex items-center gap-2">
                      <FileText className="w-5 h-5" />
                      Original Text (Urdu/Hindi)
                    </h3>
                    <div className="bg-neutral-100 rounded-xl p-4 max-h-32 overflow-y-auto">
                      <p className="text-sm text-right font-urdu">{result.original_text || 'Original text extracted'}</p>
                    </div>
                  </div>

                  {/* Translated Text */}
                  <div>
                    <h3 className="font-bold mb-2 flex items-center gap-2">
                      <Languages className="w-5 h-5" />
                      Translated Text (English)
                    </h3>
                    <motion.div 
                      className="bg-gradient-to-br from-neutral-50 to-neutral-100 rounded-xl p-4 max-h-60 overflow-y-auto border border-neutral-200"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.translated_text || result.translation}</p>
                    </motion.div>
                    {result.pages_processed && (
                      <p className="text-xs text-neutral-500 mt-2">
                        Processed {result.pages_processed} page(s) • {result.chunks_processed || 1} chunks
                      </p>
                    )}
                  </div>

                  {/* Download Buttons */}
                  <div className="flex gap-4">
                    <button
                      onClick={handleDownloadText}
                      className="flex-1 py-3 border-2 border-[#292929] text-[#292929] rounded-xl font-semibold hover:bg-[#292929] hover:text-white transition-all flex items-center justify-center gap-2"
                    >
                      <Download className="w-5 h-5" />
                      Download TXT
                    </button>
                    <button
                      onClick={handleDownloadPdf}
                      disabled={downloadingPdf}
                      className="flex-1 py-3 bg-[#292929] text-white rounded-xl font-semibold hover:bg-[#444] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {downloadingPdf ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Generating PDF...
                        </>
                      ) : (
                        <>
                          <FileText className="w-5 h-5" />
                          Download PDF
                        </>
                      )}
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12">Why Our Translation?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-[#292929] mx-auto mb-4 flex items-center justify-center">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Context-Aware</h3>
              <p className="text-[#292929]">
                Preserves legal and agricultural terminology specific to land records
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-[#292929] mx-auto mb-4 flex items-center justify-center">
                <Languages className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Multiple Languages</h3>
              <p className="text-[#292929]">
                Support for Urdu, Hindi, and major Indian regional languages
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full bg-[#292929] mx-auto mb-4 flex items-center justify-center">
                <FileText className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold mb-2">Batch Processing</h3>
              <p className="text-[#292929]">
                Translate multiple documents simultaneously for efficiency
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-[#292929]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Need Full Translation Pipeline?
          </h2>
          <p className="text-xl text-neutral-300 mb-8">
            Access OCR, Translation, and Database Storage in one platform
          </p>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-[#292929] rounded-full font-bold hover:scale-105 transition-transform"
          >
            Go to Dashboard
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default TranslationFeaturePage;
