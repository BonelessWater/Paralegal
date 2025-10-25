#!/usr/bin/env python3
"""
Audio Transcription Pipeline - Local Whisper or OpenAI API

Transcribe audio recordings from PostgreSQL database using either:
1. Local Whisper (FREE, GPU-accelerated) - RECOMMENDED
2. OpenAI Whisper API (costs $0.006/min)

Features:
- Load audio files from database
- Batch transcription with progress tracking
- Cost estimation before processing (API mode)
- Dry-run mode to preview operations
- Save transcripts back to database
- Comprehensive error handling

Usage:
    # LOCAL WHISPER (FREE, GPU-accelerated) - RECOMMENDED
    python transcribe_local.py
    
    # Dry run (preview operations, no transcription)
    python transcribe_local.py --dry-run
    
    # Transcribe specific files
    python transcribe_local.py --limit 5
    
    # Choose model size
    python transcribe_local.py --model-size medium  # faster, less accurate
    python transcribe_local.py --model-size large-v3  # slower, best accuracy
    
    # OPENAI API (use transcribe_api.py for this)
"""

import os
import sys
import time
import argparse
import psycopg2
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.audio_loader import AudioLoader
from audio.whisper_local import WhisperLocalTranscriber


class LocalTranscriptionPipeline:
    """
    End-to-end audio transcription pipeline using local Whisper.
    
    FREE, GPU-accelerated, private transcription on AMD MI300X.
    """
    
    def __init__(
        self,
        model_size: str = "large-v3",
        db_host: str = None,
        db_port: int = 5432,
        db_name: str = None,
        db_user: str = None,
        db_password: str = None
    ):
        """
        Initialize transcription pipeline.
        
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large/large-v3)
            db_*: Database connection parameters (reads from env if not provided)
        """
        # Get credentials from environment if not provided
        db_host = db_host or os.getenv('DB_HOST', 'localhost')
        db_name = db_name or os.getenv('DB_NAME', 'paralegal_db')
        db_user = db_user or os.getenv('DB_USER', 'paralegal_user')
        db_password = db_password or os.getenv('DB_PASSWORD', '')
        
        # Database connection config
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        
        # Initialize components
        print("\n" + "=" * 70)
        print("INITIALIZING TRANSCRIPTION PIPELINE")
        print("=" * 70)
        
        self.loader = AudioLoader(db_host, db_port, db_name, db_user, db_password)
        self.transcriber = WhisperLocalTranscriber(model_size=model_size)
        
        print("\n✓ Pipeline initialized")
        print(f"  Mode: LOCAL (GPU-accelerated)")
        print(f"  Model: Whisper {model_size}")
        print(f"  Database: {db_host}/{db_name}")
        print(f"  Cost: FREE")
    
    def transcribe_all(
        self,
        force: bool = False,
        dry_run: bool = False,
        limit: Optional[int] = None,
        language: str = "en",
        save_progress: bool = True
    ) -> Dict:
        """
        Transcribe all audio recordings and save to database.
        
        Args:
            force: Re-transcribe already transcribed files
            dry_run: Don't save to database (test mode)
            limit: Maximum number of files to process
            language: Audio language code (default: 'en' for English)
            save_progress: Save after each transcription (vs batch at end)
        
        Returns:
            Dictionary with transcription statistics
        """
        print("\n" + "=" * 70)
        print("AUDIO TRANSCRIPTION PIPELINE")
        print("=" * 70)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"Force re-transcription: {force}")
        print(f"Limit: {limit or 'None'}")
        
        # Load audio files
        print("\n" + "-" * 70)
        print("Loading audio files from database...")
        print("-" * 70)
        
        audio_files = self.loader.load_all_audio()
        
        if not audio_files:
            print("\n⚠️  No audio files found in database")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'total_duration': 0
            }
        
        # Filter already transcribed files
        if not force:
            original_count = len(audio_files)
            audio_files = [f for f in audio_files if not f.get('transcript')]
            skipped = original_count - len(audio_files)
            if skipped > 0:
                print(f"ℹ️  Skipping {skipped} already transcribed files")
        else:
            skipped = 0
        
        # Apply limit
        if limit:
            audio_files = audio_files[:limit]
        
        total_files = len(audio_files)
        
        if total_files == 0:
            print("\n✓ All files already transcribed")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'skipped': skipped,
                'total_duration': 0
            }
        
        # Show summary
        print(f"\n📊 Summary:")
        print(f"  Total files: {total_files}")
        print(f"  Already transcribed: {skipped}")
        print(f"  Cost: FREE (local processing)")
        
        # Confirm before proceeding
        if not dry_run:
            response = input(f"\nProceed with transcription? (y/n): ")
            if response.lower() != 'y':
                print("❌ Cancelled")
                return {'total_files': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'total_duration': 0}
        
        # Transcribe files
        print("\n" + "-" * 70)
        print("Transcribing audio files...")
        print("-" * 70)
        
        successful = 0
        failed = 0
        start_time = time.time()
        results = []
        
        for i, audio_file in enumerate(audio_files, 1):
            print(f"\n[{i}/{total_files}] {audio_file['filename']}")
            print(f"  ID: {audio_file['id']}")
            print(f"  Path: {audio_file['file_path']}")
            
            if dry_run:
                print("  ⏭️  Skipped (dry run)")
                continue
            
            try:
                # Transcribe
                file_start = time.time()
                
                result = self.transcriber.transcribe(
                    audio_path=audio_file['file_path'],
                    language=language
                )
                
                file_duration = time.time() - file_start
                
                # Add metadata
                result['record_id'] = audio_file['id']
                result['filename'] = audio_file['filename']
                result['processing_time'] = file_duration
                
                results.append(result)
                
                print(f"  ✓ Transcribed in {file_duration:.2f}s")
                print(f"  Length: {len(result['text'])} characters")
                
                # Save to database
                if save_progress:
                    self._save_transcript(
                        record_id=audio_file['id'],
                        transcript=result['text'],
                        metadata=result
                    )
                    print(f"  ✓ Saved to database")
                
                successful += 1
                
            except Exception as e:
                failed += 1
                print(f"  ✗ Error: {e}")
                results.append({
                    'record_id': audio_file['id'],
                    'filename': audio_file['filename'],
                    'error': str(e),
                    'success': False
                })
        
        # Save all at once if not saving progressively
        if not save_progress and not dry_run and results:
            print("\n" + "-" * 70)
            print("Saving all transcripts to database...")
            print("-" * 70)
            
            for result in results:
                if result.get('text'):
                    try:
                        self._save_transcript(
                            record_id=result['record_id'],
                            transcript=result['text'],
                            metadata=result
                        )
                        print(f"  ✓ Saved: {result['filename']}")
                    except Exception as e:
                        print(f"  ✗ Error saving {result['filename']}: {e}")
        
        # Summary
        total_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("TRANSCRIPTION COMPLETE")
        print("=" * 70)
        print(f"Total files: {total_files}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per file: {total_time/total_files if total_files > 0 else 0:.2f}s")
        print(f"Total cost: $0.00 (FREE!)")
        
        return {
            'total_files': total_files,
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'total_duration': total_time,
            'average_time': total_time / total_files if total_files > 0 else 0,
            'results': results
        }
    
    def _save_transcript(
        self,
        record_id: int,
        transcript: str,
        metadata: Dict = None
    ):
        """
        Save transcript to database.
        
        Args:
            record_id: Document record ID
            transcript: Transcribed text
            metadata: Additional metadata to save
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Update document with transcript
            cur.execute("""
                UPDATE legal_data.documents
                SET 
                    extracted_text = %s,
                    last_modified = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (transcript, record_id))
            
            conn.commit()
            
        finally:
            cur.close()
            conn.close()
    
    def get_transcription_status(self) -> Dict:
        """
        Get status of all audio files.
        
        Returns:
            Dictionary with status counts
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Count transcribed files
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN extracted_text IS NOT NULL AND extracted_text != '' 
                          THEN 1 END) as transcribed,
                    COUNT(CASE WHEN extracted_text IS NULL OR extracted_text = '' 
                          THEN 1 END) as not_transcribed
                FROM legal_data.documents
                WHERE document_type = 'Audio Recording'
            """)
            
            row = cur.fetchone()
            
            return {
                'total': row[0],
                'transcribed': row[1],
                'not_transcribed': row[2],
                'completion_percent': (row[1] / row[0] * 100) if row[0] > 0 else 0
            }
        
        finally:
            cur.close()
            conn.close()


def main():
    """
    Command-line interface for transcription pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Transcribe audio recordings using local Whisper (FREE, GPU-accelerated)"
    )
    
    parser.add_argument(
        '--model-size',
        type=str,
        default='large-v3',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v3'],
        help='Whisper model size (default: large-v3 for best accuracy)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview operations without transcribing'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-transcribe already transcribed files'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of files to process'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        default='en',
        help='Audio language code (default: en)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show transcription status and exit'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    try:
        pipeline = LocalTranscriptionPipeline(model_size=args.model_size)
    except Exception as e:
        print(f"\n❌ Error initializing pipeline: {e}")
        print("\nMake sure you have:")
        print("1. Set database credentials in .env file")
        print("2. Installed dependencies: pip install torch transformers accelerate")
        sys.exit(1)
    
    # Show status if requested
    if args.status:
        print("\n" + "=" * 70)
        print("TRANSCRIPTION STATUS")
        print("=" * 70)
        
        status = pipeline.get_transcription_status()
        
        print(f"Total audio files: {status['total']}")
        print(f"Transcribed: {status['transcribed']}")
        print(f"Not transcribed: {status['not_transcribed']}")
        print(f"Completion: {status['completion_percent']:.1f}%")
        
        sys.exit(0)
    
    # Run transcription
    try:
        results = pipeline.transcribe_all(
            force=args.force,
            dry_run=args.dry_run,
            limit=args.limit,
            language=args.language
        )
        
        print("\n✓ Pipeline completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
