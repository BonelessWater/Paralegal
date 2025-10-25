#!/usr/bin/env python3
"""
Load Morgan & Morgan case files into PostgreSQL database
Processes PDFs, audio files, and other documents from case folders
"""

import os
import sys
import re
import configparser
from pathlib import Path
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# PDF processing
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Document processing
try:
    import docx
except ImportError:
    docx = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MorganFileLoader:
    """Load Morgan & Morgan case files into database"""
    
    def __init__(self, config_path='config.ini', morgan_dir=None):
        """Initialize with database config and Morgan & Morgan directory"""
        config = configparser.ConfigParser()
        config.read(config_path)
        
        self.db_config = dict(config['database'])
        self.morgan_dir = Path(morgan_dir) if morgan_dir else None
        
        # Document type mapping based on filename patterns
        self.doc_type_patterns = {
            r'police|crash': 'Police Report',
            r'pip': 'PIP Document',
            r'offer|settlement': 'Settlement Offer',
            r'property\s*damage|estimate': 'Property Damage',
            r'lien': 'Medical Lien',
            r'negotiation': 'Negotiation Document',
            r'insurance': 'Insurance Document',
            r'demand': 'Demand Letter',
            r'tender': 'Tender Document',
            r'\.m4a$|\.mp3$|\.wav$': 'Audio Recording'
        }
        
        # Stats tracking
        self.stats = {
            'cases_processed': 0,
            'documents_inserted': 0,
            'pdfs_processed': 0,
            'audio_files_found': 0,
            'errors': 0
        }
    
    def get_db_connection(self):
        """Create database connection"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['username'],
            password=self.db_config['password']
        )
    
    def classify_document(self, filename):
        """Classify document type based on filename"""
        filename_lower = filename.lower()
        
        for pattern, doc_type in self.doc_type_patterns.items():
            if re.search(pattern, filename_lower):
                return doc_type
        
        # Default classification based on extension
        if filename_lower.endswith('.pdf'):
            return 'Legal Document'
        elif filename_lower.endswith(('.m4a', '.mp3', '.wav')):
            return 'Audio Recording'
        elif filename_lower.endswith('.docx'):
            return 'Word Document'
        else:
            return 'Other Document'
    
    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF file"""
        if not PyPDF2:
            logger.warning("PyPDF2 not installed, skipping text extraction")
            return None
        
        try:
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            return '\n\n'.join(text_content) if text_content else None
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return None
    
    def extract_docx_text(self, docx_path):
        """Extract text from DOCX file"""
        if not docx:
            logger.warning("python-docx not installed, skipping text extraction")
            return None
        
        try:
            doc = docx.Document(docx_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return '\n\n'.join(paragraphs) if paragraphs else None
        except Exception as e:
            logger.error(f"Error extracting text from {docx_path}: {e}")
            return None
    
    def create_search_session(self, conn):
        """Create a search session for Morgan & Morgan import"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO legal_data.search_sessions 
            (search_query, search_url, notes, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (
            'Morgan & Morgan Case Files Import',
            'file://~/Morgan&Morgan',
            'Manual upload of Morgan & Morgan case files (v1.0)',
            'completed'
        ))
        
        session_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        logger.info(f"Created search session: {session_id}")
        return session_id
    
    def ensure_morgan_law_firm(self, conn):
        """Ensure Morgan & Morgan exists in law_firms table"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO legal_data.law_firms 
            (firm_name, city, state, website)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (firm_name) DO UPDATE SET
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                website = EXCLUDED.website
            RETURNING id
        """, (
            'Morgan & Morgan',
            'Orlando',
            'Florida',
            'https://www.forthepeople.com'
        ))
        
        firm_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        logger.info(f"Morgan & Morgan law firm ID: {firm_id}")
        return firm_id
    
    def extract_case_number(self, folder_name):
        """Extract case number from folder name (e.g., 'File 1-12564888' -> '12564888')"""
        match = re.search(r'File\s+\d+-(\d+)', folder_name)
        return match.group(1) if match else folder_name
    
    def process_file(self, file_path, case_number, session_id, conn):
        """Process a single file and insert into database"""
        file_path = Path(file_path)
        filename = file_path.name
        
        # Skip system files
        if filename.startswith('.') or filename == 'Thumbs.db':
            return None
        
        # Classify document
        doc_type = self.classify_document(filename)
        
        # Extract text based on file type
        full_text = None
        if file_path.suffix.lower() == '.pdf':
            full_text = self.extract_pdf_text(file_path)
            self.stats['pdfs_processed'] += 1
        elif file_path.suffix.lower() == '.docx':
            full_text = self.extract_docx_text(file_path)
        elif file_path.suffix.lower() in ['.m4a', '.mp3', '.wav']:
            self.stats['audio_files_found'] += 1
            # For audio files, just store the path for now
            full_text = f"Audio file: {filename}"
        
        # Create title from filename
        title = filename.replace('_', ' ').replace('.pdf', '').replace('.m4a', '')
        if case_number:
            title = f"Case {case_number} - {title}"
        
        # Generate summary
        summary = f"{doc_type} from Morgan & Morgan case file {case_number}"
        if full_text:
            # Use first 500 characters as summary
            summary = full_text[:500] + '...' if len(full_text) > 500 else full_text
        
        # Create unique document_id from case number and filename hash
        import hashlib
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        unique_doc_id = f"{case_number}-{file_hash}"
        
        # Insert document - using actual column names from schema
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO legal_data.documents
                (session_id, document_id, title, document_type, summary, full_text, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                session_id,
                unique_doc_id,  # document_id field stores unique document identifier
                title,
                doc_type,
                summary,
                full_text,
                str(file_path.absolute())  # url field stores file path
            ))
            
            doc_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"  ✓ Inserted: {filename} (ID: {doc_id}, Type: {doc_type})")
            self.stats['documents_inserted'] += 1
            
            return doc_id
            
        except Exception as e:
            logger.error(f"  ✗ Error inserting {filename}: {e}")
            conn.rollback()
            self.stats['errors'] += 1
            return None
        finally:
            cursor.close()
    
    def link_document_to_firm(self, doc_id, firm_id, conn):
        """Link a document to Morgan & Morgan law firm"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO legal_data.document_law_firms
                (document_id, law_firm_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (document_id, law_firm_id, role) DO NOTHING
            """, (doc_id, firm_id, 'Plaintiff Counsel'))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error linking document {doc_id} to firm: {e}")
            conn.rollback()
        finally:
            cursor.close()
    
    def process_case_folder(self, case_folder, session_id, firm_id, conn):
        """Process all files in a case folder"""
        case_folder = Path(case_folder)
        case_number = self.extract_case_number(case_folder.name)
        
        logger.info(f"\nProcessing case: {case_folder.name} (Case #: {case_number})")
        
        # Walk through all files in the case folder (including subdirectories)
        for root, dirs, files in os.walk(case_folder):
            for filename in files:
                file_path = Path(root) / filename
                doc_id = self.process_file(file_path, case_number, session_id, conn)
                
                # Link document to Morgan & Morgan
                if doc_id:
                    self.link_document_to_firm(doc_id, firm_id, conn)
        
        self.stats['cases_processed'] += 1
    
    def load_all_files(self):
        """Load all Morgan & Morgan case files"""
        if not self.morgan_dir or not self.morgan_dir.exists():
            logger.error(f"Morgan & Morgan directory not found: {self.morgan_dir}")
            return
        
        logger.info("=" * 60)
        logger.info("Morgan & Morgan File Loader")
        logger.info(f"Source Directory: {self.morgan_dir}")
        logger.info("=" * 60)
        
        # Connect to database
        conn = self.get_db_connection()
        
        try:
            # Create search session
            session_id = self.create_search_session(conn)
            
            # Ensure Morgan & Morgan law firm exists
            firm_id = self.ensure_morgan_law_firm(conn)
            
            # Process each case folder
            case_folders = [
                d for d in self.morgan_dir.iterdir()
                if d.is_dir() and d.name.startswith('File ')
            ]
            
            logger.info(f"\nFound {len(case_folders)} case folders")
            
            for case_folder in sorted(case_folders):
                self.process_case_folder(case_folder, session_id, firm_id, conn)
            
            # Update session with total results
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE legal_data.search_sessions
                SET total_results = %s
                WHERE id = %s
            """, (self.stats['documents_inserted'], session_id))
            conn.commit()
            cursor.close()
            
        finally:
            conn.close()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Loading Complete!")
        logger.info("=" * 60)
        logger.info(f"Cases Processed: {self.stats['cases_processed']}")
        logger.info(f"Documents Inserted: {self.stats['documents_inserted']}")
        logger.info(f"PDFs Processed: {self.stats['pdfs_processed']}")
        logger.info(f"Audio Files Found: {self.stats['audio_files_found']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)


def main():
    """Main function"""
    # Default Morgan & Morgan directory
    default_dir = Path.home() / 'Desktop' / 'Morgan&Morgan'
    
    # Allow custom directory via command line argument
    if len(sys.argv) > 1:
        morgan_dir = Path(sys.argv[1])
    else:
        morgan_dir = default_dir
    
    if not morgan_dir.exists():
        logger.error(f"Morgan & Morgan directory not found: {morgan_dir}")
        logger.error("Usage: python load_morgan_files.py [path/to/Morgan&Morgan]")
        sys.exit(1)
    
    loader = MorganFileLoader(config_path='config.ini', morgan_dir=morgan_dir)
    loader.load_all_files()


if __name__ == '__main__':
    main()
