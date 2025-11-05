"""
OCR and Text Extraction Service
Handles PDF, Image, and Text file processing
"""
try:
    import pytesseract
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Tesseract/pdf2image not available - OCR features disabled")

from PIL import Image
from PyPDF2 import PdfReader
import io
import os
import logging
from typing import Tuple, List
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRService:
    """Service for extracting text from various file formats"""
    
    def __init__(self):
        """Initialize OCR service"""
        # Configure Tesseract path for Windows (adjust if needed)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    async def extract_text(self, file_path: str, file_type: str) -> Tuple[str, List[str]]:
        """
        Extract text from file based on type
        
        Args:
            file_path: Path to the uploaded file
            file_type: Type of file (pdf, image, text)
            
        Returns:
            Tuple of (extracted_text, list_of_errors)
        """
        try:
            if file_type == "pdf":
                return await self._extract_from_pdf(file_path)
            elif file_type in ["image", "png", "jpg", "jpeg"]:
                return await self._extract_from_image(file_path)
            elif file_type == "text":
                return await self._extract_from_text(file_path)
            else:
                return "", [f"Unsupported file type: {file_type}"]
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return "", [str(e)]
    
    async def _extract_from_pdf(self, file_path: str) -> Tuple[str, List[str]]:
        """
        Extract text from PDF using PyPDF2
        Falls back to OCR if text extraction fails
        """
        errors = []
        extracted_text = ""
        
        try:
            # Try direct text extraction first
            reader = PdfReader(file_path)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text)
                else:
                    # Page has no text, try OCR
                    logger.info(f"Page {page_num} has no text, attempting OCR")
                    errors.append(f"Page {page_num} required OCR")
            
            extracted_text = "\n\n".join(text_parts)
            
            # If very little text extracted, try OCR on entire PDF
            if len(extracted_text.strip()) < 100:
                logger.info("Insufficient text extracted, falling back to OCR")
                extracted_text = await self._ocr_pdf(file_path)
                errors.append("Used OCR for entire PDF")
            
            return extracted_text, errors
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            # Try OCR as last resort
            try:
                extracted_text = await self._ocr_pdf(file_path)
                return extracted_text, [f"Direct extraction failed, used OCR: {str(e)}"]
            except Exception as ocr_error:
                return "", [f"PDF extraction failed: {str(e)}", f"OCR failed: {str(ocr_error)}"]
    
    async def _ocr_pdf(self, file_path: str) -> str:
        """Convert PDF to images and apply OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(file_path)
            text_parts = []
            
            for i, image in enumerate(images):
                logger.info(f"OCR processing page {i+1}/{len(images)}")
                text = pytesseract.image_to_string(image, lang='eng')
                text_parts.append(text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"OCR PDF error: {e}")
            raise
    
    async def _extract_from_image(self, file_path: str) -> Tuple[str, List[str]]:
        """Extract text from image using Tesseract OCR"""
        try:
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Apply OCR
            text = pytesseract.image_to_string(image, lang='eng')
            
            if not text.strip():
                return "", ["No text detected in image"]
            
            return text, []
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            return "", [str(e)]
    
    async def _extract_from_text(self, file_path: str) -> Tuple[str, List[str]]:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text, []
        except UnicodeDecodeError:
            # Try different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
                return text, ["Used latin-1 encoding"]
            except Exception as e:
                return "", [f"Text file reading error: {str(e)}"]
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return "", [str(e)]
    
    def preprocess_image(self, image_path: str) -> Image:
        """
        Preprocess image to improve OCR accuracy
        Apply techniques like grayscale conversion, noise removal, etc.
        """
        try:
            image = Image.open(image_path)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # You can add more preprocessing steps here:
            # - Noise removal
            # - Thresholding
            # - Deskewing
            
            return image
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            raise


# Singleton instance
ocr_service = OCRService()
