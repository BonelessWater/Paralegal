#!/usr/bin/env python3
"""
Process Morgan & Morgan case files, perform OCR, and load into PostgreSQL.
"""

import os
import re
import magic
import PyPDF2
from PIL import Image
import pytesseract
import librosa
import psycopg2
from psycopg2.extras import RealDictCursor
import configparser
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MorganFileLoader:
    def __init__(self, config_path='config.ini'):
        config = configparser.ConfigParser()
        config.read(config_path)
        self.db_config = dict(config['database'])
        self.base_dir = Path('Morgan&Morgan')

    def get_db_connection(self):
        return psycopg2.connect(**self.db_config)

    def process_pdf(self, file_path):
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            if not text.strip():
                logger.warning(f"No text extracted from {file_path}, trying OCR...")
                text = pytesseract.image_to_string(Image.open(file_path))
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
        return text

    def process_image(self, file_path):
        try:
            return pytesseract.image_to_string(Image.open(file_path))
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
        return ""

    def process_audio(self, file_path):
        try:
            duration = librosa.get_duration(path=file_path)
            return f"Audio file, duration: {duration:.2f} seconds."
        except Exception as e:
            logger.error(f"Error processing audio {file_path}: {e}")
        return ""

    def insert_document(self, case_number, file_path, content):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO legal_data.documents (case_number, title, full_text, document_type)
                VALUES (%s, %s, %s, %s)
            """, (case_number, file_path.name, content, file_path.suffix.lower()))
            conn.commit()
            logger.info(f"Inserted {file_path.name} for case {case_number}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting {file_path.name}: {e}")
        finally:
            cursor.close()
            conn.close()

    def process_files(self):
        for file_dir in self.base_dir.iterdir():
            if file_dir.is_dir():
                match = re.search(r'File \d+-(\d+)', file_dir.name)
                if match:
                    case_number = match.group(1)
                    logger.info(f"Processing case: {case_number}")
                    for file_path in file_dir.rglob('*'):
                        if file_path.is_file():
                            self.process_file(case_number, file_path)

    def process_file(self, case_number, file_path):
        mime_type = magic.from_file(str(file_path), mime=True)
        content = ""
        if 'pdf' in mime_type:
            content = self.process_pdf(file_path)
        elif 'image' in mime_type:
            content = self.process_image(file_path)
        elif 'audio' in mime_type:
            content = self.process_audio(file_path)
        else:
            logger.warning(f"Unsupported file type: {mime_type} for {file_path}")

        if content:
            self.insert_document(case_number, file_path, content)

def main():
    loader = MorganFileLoader()
    loader.process_files()

if __name__ == '__main__':
    main()
