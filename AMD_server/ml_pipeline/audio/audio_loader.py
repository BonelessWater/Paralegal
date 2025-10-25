"""
Audio Loader for Morgan & Morgan Call Recordings

Loads audio files from PostgreSQL database and provides access to .m4a recordings.
Used for transcribing Morgan & Morgan client phone calls.

Usage:
    from audio.audio_loader import AudioLoader
    
    loader = AudioLoader()
    audio_files = loader.load_audio_recordings()
    
    for audio in audio_files:
        print(f"ID: {audio['id']}, Title: {audio['title']}")
        print(f"File path: {audio['file_path']}")
"""

import os
import psycopg2
from typing import List, Dict, Optional
from pathlib import Path


class AudioLoader:
    """
    Loads audio recording metadata from PostgreSQL database.
    
    Attributes:
        db_config (dict): Database connection configuration
        conn: PostgreSQL connection object
    """
    
    def __init__(
        self,
        host: str = "134.199.202.8",
        port: int = 5432,
        database: str = "paralegal_db",
        user: str = "paralegal_user",
        password: str = "hackathon2024"
    ):
        """
        Initialize AudioLoader with database credentials.
        
        Args:
            host: PostgreSQL server hostname
            port: PostgreSQL server port
            database: Database name
            user: Database username
            password: Database password
        """
        self.db_config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
    
    def connect(self):
        """Establish connection to PostgreSQL database."""
        if self.conn is None or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
    
    def disconnect(self):
        """Close database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def load_audio_recordings(
        self,
        limit: Optional[int] = None,
        only_untranscribed: bool = False
    ) -> List[Dict]:
        """
        Load audio recording metadata from database.
        
        Args:
            limit: Maximum number of recordings to load (None = all)
            only_untranscribed: If True, only load recordings without transcripts
        
        Returns:
            List of dictionaries containing audio file metadata:
                - id: Database record ID
                - document_id: Unique document identifier
                - title: Recording title
                - url: File path to .m4a file
                - file_path: Same as url (for compatibility)
                - full_text: Existing transcript (if any)
                - created_at: Creation timestamp
                - metadata: Additional metadata (court, jurisdiction, etc.)
        """
        self.connect()
        
        cursor = self.conn.cursor()
        
        # Build query
        query = """
            SELECT 
                id,
                document_id,
                title,
                url,
                full_text,
                created_at,
                document_type,
                jurisdiction,
                court,
                decision_date,
                summary
            FROM legal_data.documents
            WHERE document_type = 'Audio Recording'
        """
        
        # Add filter for untranscribed recordings
        if only_untranscribed:
            query += " AND (full_text IS NULL OR full_text = '')"
        
        # Add ordering and limit
        query += " ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        audio_files = []
        for row in rows:
            audio_files.append({
                'id': row[0],
                'document_id': row[1],
                'title': row[2],
                'url': row[3],
                'file_path': row[3],  # Alias for compatibility
                'full_text': row[4],
                'created_at': row[5],
                'metadata': {
                    'document_type': row[6],
                    'jurisdiction': row[7],
                    'court': row[8],
                    'decision_date': row[9],
                    'summary': row[10]
                }
            })
        
        cursor.close()
        
        return audio_files
    
    def get_audio_file_path(self, audio_record: Dict) -> Optional[Path]:
        """
        Get the file system path for an audio recording.
        
        Args:
            audio_record: Audio metadata dictionary from load_audio_recordings()
        
        Returns:
            Path object pointing to .m4a file, or None if file doesn't exist
        """
        file_path = audio_record.get('file_path') or audio_record.get('url')
        
        if not file_path:
            return None
        
        # Convert to Path object
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            print(f"Warning: Audio file not found: {path}")
            return None
        
        return path
    
    def verify_audio_files(self, audio_files: List[Dict]) -> Dict[str, int]:
        """
        Verify that audio files exist on disk.
        
        Args:
            audio_files: List of audio metadata dictionaries
        
        Returns:
            Dictionary with verification statistics:
                - total: Total number of files
                - found: Number of files found on disk
                - missing: Number of missing files
                - transcribed: Number already transcribed
                - needs_transcription: Number needing transcription
        """
        stats = {
            'total': len(audio_files),
            'found': 0,
            'missing': 0,
            'transcribed': 0,
            'needs_transcription': 0
        }
        
        for audio in audio_files:
            # Check file existence
            path = self.get_audio_file_path(audio)
            if path and path.exists():
                stats['found'] += 1
            else:
                stats['missing'] += 1
            
            # Check transcription status
            if audio.get('full_text') and audio['full_text'].strip():
                stats['transcribed'] += 1
            else:
                stats['needs_transcription'] += 1
        
        return stats
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics about audio recordings in database.
        
        Returns:
            Dictionary with summary statistics:
                - total_recordings: Total number of audio recordings
                - transcribed: Number with transcripts
                - untranscribed: Number without transcripts
        """
        self.connect()
        
        cursor = self.conn.cursor()
        
        # Get total count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM legal_data.documents 
            WHERE document_type = 'Audio Recording'
        """)
        total = cursor.fetchone()[0]
        
        # Get transcribed count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM legal_data.documents 
            WHERE document_type = 'Audio Recording' 
            AND full_text IS NOT NULL 
            AND full_text != ''
        """)
        transcribed = cursor.fetchone()[0]
        
        cursor.close()
        
        return {
            'total_recordings': total,
            'transcribed': transcribed,
            'untranscribed': total - transcribed
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Quick usage example
if __name__ == "__main__":
    # Load all audio recordings
    loader = AudioLoader()
    
    print("=" * 60)
    print("AUDIO LOADER - MORGAN & MORGAN CALL RECORDINGS")
    print("=" * 60)
    
    # Get summary
    summary = loader.get_summary()
    print(f"\nDatabase Summary:")
    print(f"  Total recordings: {summary['total_recordings']}")
    print(f"  Transcribed: {summary['transcribed']}")
    print(f"  Untranscribed: {summary['untranscribed']}")
    
    # Load all audio files
    print("\nLoading audio files...")
    audio_files = loader.load_audio_recordings()
    
    print(f"\nFound {len(audio_files)} audio recordings:")
    print("-" * 60)
    
    for i, audio in enumerate(audio_files, 1):
        print(f"\n{i}. {audio['title']}")
        print(f"   ID: {audio['id']}")
        print(f"   Document ID: {audio['document_id']}")
        print(f"   File: {audio['file_path']}")
        print(f"   Created: {audio['created_at']}")
        
        # Check if transcribed
        if audio['full_text']:
            print(f"   Status: ✓ Transcribed ({len(audio['full_text'])} chars)")
        else:
            print(f"   Status: ✗ Not transcribed")
    
    # Verify files on disk
    print("\n" + "=" * 60)
    print("FILE VERIFICATION")
    print("=" * 60)
    stats = loader.verify_audio_files(audio_files)
    print(f"\nTotal files: {stats['total']}")
    print(f"Found on disk: {stats['found']}")
    print(f"Missing: {stats['missing']}")
    print(f"Already transcribed: {stats['transcribed']}")
    print(f"Need transcription: {stats['needs_transcription']}")
    
    loader.disconnect()
