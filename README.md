# Land Record OCR & Translation System

A comprehensive system for digitizing land records in Jammu & Kashmir. This application combines Optical Character Recognition (OCR) with advanced translation capabilities to convert multi-lingual land records (Urdu, Hindi, English) into digital formats.

## 🎯 Overview

This project addresses the challenge of digitizing legacy land records under the AgriStack implementation. It handles physical, scanned, and handwritten documents, providing accurate text extraction and translation from Urdu to English.

### Key Features
- **Multi-Language OCR**: Support for English, Hindi, and Urdu using Tesseract 5.x.
- **PDF Processing**: Robust handling of PDF documents using PyMuPDF (no external Poppler dependency required).
- **Intelligent Translation**: 
  - Uses AI4Bharat's **IndicTrans2** model for high-quality Urdu-to-English translation.
  - Specialized handling for land record terminology (e.g., "Jamabandi" -> "Land Revenue Record").
- **Document Generation**: Export translated results to professional PDF format.
- **Modular Architecture**: Clean separation of concerns (OCR, Translation, Document Handling).

## 🏗️ Architecture

The project is split into a Flask backend and a React frontend.

### Backend Structure (`/backend`)
The backend is organized into domain-specific modules:

- **`ocr/`**: Core OCR logic, Tesseract integration, and image processing.
- **`translation/`**: Translation services (IndicTrans2), language detection, and transliteration.
- **`document/`**: File upload handling, PDF generation, and RAG processing.
- **`common/`**: Shared utilities like text cleaning and response formatting.
- **`routes/`**: API endpoints for OCR, Translation, and Health checks.
- **`tessdata/`**: Local storage for Tesseract language models (`urd`, `hin`) to ensure portability.

### Frontend (`/frontend`)
- Built with **React** and **Vite**.
- Modern UI using **Tailwind CSS**.
- Features drag-and-drop uploads and real-time processing status.

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 18.0 or higher
- **Tesseract OCR**: Must be installed on the system.
  - Windows: [Download Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - Linux: `sudo apt-get install tesseract-ocr`

## 🚀 Installation & Setup

### 1. Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Tesseract Configuration**:
    - The system is configured to look for Tesseract at `C:\Program Files\Tesseract-OCR\tesseract.exe` (Windows default).
    - Language data (`urd.traineddata`, `hin.traineddata`) is included in `backend/tessdata` to avoid permission issues.

5.  Start the server:
    ```bash
    python app.py
    ```
    The server will run at `http://127.0.0.1:5000`.

### 2. Frontend Setup

1.  Open a new terminal and navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

## 📖 Usage

1.  Open the web application in your browser.
2.  **Translation Mode**:
    - Navigate to the "Translation" tab.
    - Upload a PDF or Image containing Urdu land records (e.g., `Atmapur.pdf`).
    - Click **Translate**.
    - View the extracted text and its English translation side-by-side.
    - Download the result as a PDF.
3.  **OCR Mode**:
    - Use the "OCR" tab for raw text extraction without translation.

## 🔧 Troubleshooting

-   **"Tesseract not found"**: Ensure Tesseract is installed and the path in `backend/config.py` matches your installation.
-   **"Original Character Count: 0"**: This usually means OCR failed. The system now uses PyMuPDF for better PDF handling, so ensure your PDF is readable.
-   **Permission Errors**: The application uses a local `backend/tessdata` folder for language models to avoid writing to system directories.

## 📄 License

This project is licensed under the MIT License.
