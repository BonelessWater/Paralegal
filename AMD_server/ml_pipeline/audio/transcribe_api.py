#!/usr/bin/env python3
"""
Transcribe Morgan & Morgan Call Recordings using OpenAI Whisper API

This script:
1. Loads audio files from PostgreSQL database
2. Transcribes them using OpenAI's Whisper API
3. Saves transcripts back to database

Usage:
    # Transcribe all untranscribed recordings
    python transcribe_api.py
    
    # Transcribe specific recordings by ID
    python transcribe_api.py --ids 1 2 3
    
    # Dry run (don't save to database)
    python transcribe_api.py --dry-run
    
    # Force re-transcribe already transcribed files
    python transcribe_api.py --force
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
import psycopg2
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.audio_loader import AudioLoader
from audio.whisper_api import WhisperAPITranscriber


class TranscriptionPipeline:
    """
    End-to-end pipeline for transcribing Morgan & Morgan call recordings.
    """
    
    def __init__(
        self,
        api_key: str = None,
        db_host: str = "134.199.202.8",
        db_port: int = 5432,
        db_name: str = "paralegal_db",
        db_user: str = "paralegal_user",
        db_password: str = "hackathon2024"
    ):
        """
        Initialize transcription pipeline.
        
        Args:
            api_key: OpenAI API key (reads from env if not provided)
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_name: Database name
            db_user: Database username
            db_password: Database password
        """
        # Initialize components
        self.loader = AudioLoader(db_host, db_port, db_name, db_user, db_password)
        self.transcriber = WhisperAPITranscriber(api_key=api_key)
        
        # Database connection config
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
    
    def transcribe_all(
        self,
        force: bool = False,
        dry_run: bool = False,
        record_ids: List[int] = None,
        language: str = "en",
        save_progress: bool = True
    ) -> Dict:
        """
        Transcribe all audio recordings and save to database.
        
        Args:
            force: Re-transcribe already transcribed files
            dry_run: Don't save to database (test mode)
            record_ids: Specific record IDs to transcribe (None = all)
            language: Audio language code (default: 'en' for English)
            save_progress: Save after each transcription (vs batch at end)
        
        Returns:
            Dictionary with transcription statistics:
                - total_files: Total number of files processed
                - successful: Number successfully transcribed
                - failed: Number of failures
                - skipped: Number skipped (already transcribed)
                - total_cost: Estimated cost in USD
                - total_duration: Total processing time in seconds
        """
        print("=" * 70)
        print("MORGAN & MORGAN CALL TRANSCRIPTION PIPELINE")
        print("=" * 70)
        
        # Load audio files
        print("\n📁 Loading audio files from database...")
        if record_ids:
            # Load specific records
            all_files = self.loader.load_audio_recordings()
            audio_files = [f for f in all_files if f['id'] in record_ids]
            print(f"   Found {len(audio_files)} matching records")
        else:
            # Load all or only untranscribed
            audio_files = self.loader.load_audio_recordings(
                only_untranscribed=not force
            )
            print(f"   Found {len(audio_files)} audio recordings")
        
        if not audio_files:
            print("\n✓ No files to transcribe!")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'total_cost': 0.0,
                'total_duration': 0.0
            }
        
        # Verify files exist
        print("\n🔍 Verifying audio files...")
        stats = self.loader.verify_audio_files(audio_files)
        print(f"   Total: {stats['total']}")
        print(f"   Found on disk: {stats['found']}")
        print(f"   Missing: {stats['missing']}")
        if not force:
            print(f"   Already transcribed: {stats['transcribed']}")
            print(f"   Need transcription: {stats['needs_transcription']}")
        
        # Filter out missing files
        valid_files = [
            f for f in audio_files 
            if self.loader.get_audio_file_path(f) is not None
        ]
        
        if not valid_files:
            print("\n❌ No valid audio files found on disk!")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'total_cost': 0.0,
                'total_duration': 0.0
            }
        
        # Estimate cost (assuming 15 min per call)
        estimated_minutes = len(valid_files) * 15
        estimated_cost = self.transcriber.estimate_cost(estimated_minutes)
        
        print(f"\n💰 Cost Estimation:")
        print(f"   Files to transcribe: {len(valid_files)}")
        print(f"   Estimated duration: {estimated_minutes} minutes (~15 min/call)")
        print(f"   Estimated cost: ${estimated_cost:.2f}")
        
        if dry_run:
            print("\n⚠️  DRY RUN MODE - Will not save to database")
        
        # Confirm
        print("\n" + "=" * 70)
        response = input("Continue with transcription? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'total_cost': 0.0,
                'total_duration': 0.0
            }
        
        # Transcribe files
        print("\n🎙️  Starting transcription...")
        print("=" * 70)
        
        results = {
            'total_files': len(valid_files),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_cost': 0.0,
            'total_duration': 0.0
        }
        
        start_time = time.time()
        
        for i, audio_file in enumerate(valid_files, 1):
            print(f"\n[{i}/{len(valid_files)}] {audio_file['title']}")
            print(f"   ID: {audio_file['id']}")
            
            file_path = self.loader.get_audio_file_path(audio_file)
            
            try:
                # Transcribe
                file_start = time.time()
                transcript_result = self.transcriber.transcribe(
                    audio_path=file_path,
                    language=language,
                    prompt="This is a legal consultation phone call between a lawyer and a client discussing a personal injury case."
                )
                file_duration = time.time() - file_start
                
                transcript_text = transcript_result['text']
                file_size_mb = transcript_result.get('file_size_mb', 0)
                
                print(f"   ✓ Transcribed in {file_duration:.2f}s")
                print(f"   Transcript length: {len(transcript_text)} characters")
                print(f"   File size: {file_size_mb:.2f} MB")
                
                # Save to database
                if not dry_run:
                    self.save_transcript(
                        record_id=audio_file['id'],
                        transcript=transcript_text
                    )
                    print(f"   ✓ Saved to database")
                
                results['successful'] += 1
                results['total_duration'] += file_duration
                
                # Estimate cost (rough: $0.006/min, assume file_size correlates with duration)
                # More accurate: use actual audio duration if available
                estimated_file_cost = file_size_mb * 0.10  # Rough estimate
                results['total_cost'] += estimated_file_cost
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
                results['failed'] += 1
        
        total_time = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 70)
        print("TRANSCRIPTION SUMMARY")
        print("=" * 70)
        print(f"\nTotal files: {results['total_files']}")
        print(f"✓ Successful: {results['successful']}")
        print(f"✗ Failed: {results['failed']}")
        print(f"⊘ Skipped: {results['skipped']}")
        print(f"\n⏱️  Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"💰 Estimated cost: ${results['total_cost']:.2f}")
        
        if not dry_run and results['successful'] > 0:
            print(f"\n✓ {results['successful']} transcripts saved to database!")
        
        return results
    
    def save_transcript(self, record_id: int, transcript: str):
        """
        Save transcript to database.
        
        Args:
            record_id: Database record ID
            transcript: Transcribed text
        """
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Update full_text field with transcript
        cursor.execute("""
            UPDATE legal_data.documents
            SET full_text = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (transcript, record_id))
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_transcript(self, record_id: int) -> str:
        """
        Retrieve transcript from database.
        
        Args:
            record_id: Database record ID
        
        Returns:
            Transcript text or None if not found
        """
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT full_text
            FROM legal_data.documents
            WHERE id = %s
        """, (record_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result[0] if result else None


def main():
    """Main entry point for transcription script."""
    parser = argparse.ArgumentParser(
        description="Transcribe Morgan & Morgan call recordings using OpenAI Whisper API"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Re-transcribe already transcribed files"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Test mode - don't save to database"
    )
    parser.add_argument(
        '--ids',
        type=int,
        nargs='+',
        help="Specific record IDs to transcribe"
    )
    parser.add_argument(
        '--language',
        type=str,
        default='en',
        help="Audio language code (default: en)"
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help="OpenAI API key (default: read from OPENAI_API_KEY env)"
    )
    
    args = parser.parse_args()
    
    # Check API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ Error: OpenAI API key not found!")
        print("Set OPENAI_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = TranscriptionPipeline(api_key=api_key)
    
    # Run transcription
    results = pipeline.transcribe_all(
        force=args.force,
        dry_run=args.dry_run,
        record_ids=args.ids,
        language=args.language
    )
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
