"""
OpenAI Whisper API Transcriber

Fast transcription using OpenAI's Whisper API.
Handles audio files up to 25MB, supports multiple formats.

Usage:
    from audio.whisper_api import WhisperAPITranscriber
    
    transcriber = WhisperAPITranscriber(api_key="sk-...")
    transcript = transcriber.transcribe("path/to/audio.m4a")
    print(transcript['text'])
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional, Union
from openai import OpenAI
from openai import OpenAIError, RateLimitError, APIError


class WhisperAPITranscriber:
    """
    Transcribes audio files using OpenAI's Whisper API.
    
    Attributes:
        client: OpenAI client instance
        model: Whisper model to use (default: whisper-1)
        max_retries: Maximum retry attempts for failed requests
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        max_retries: int = 3
    ):
        """
        Initialize WhisperAPI transcriber.
        
        Args:
            api_key: OpenAI API key (reads from env if not provided)
            model: Whisper model to use (default: whisper-1)
            max_retries: Maximum retry attempts for API failures
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. "
                    "Set OPENAI_API_KEY environment variable or pass api_key parameter."
                )
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "text",
        temperature: float = 0.0
    ) -> Dict[str, any]:
        """
        Transcribe an audio file using OpenAI Whisper API.
        
        Args:
            audio_path: Path to audio file (.m4a, .mp3, .wav, etc.)
            language: ISO-639-1 language code (e.g., 'en' for English)
            prompt: Optional text to guide the model's style
            response_format: Response format ('text', 'json', 'verbose_json')
            temperature: Sampling temperature (0-1, default 0 for deterministic)
        
        Returns:
            Dictionary containing:
                - text: Transcribed text
                - language: Detected language (if not specified)
                - duration: Audio duration in seconds (if available)
                - segments: Word-level timestamps (if verbose_json)
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If file is too large (>25MB)
            OpenAIError: If API request fails after retries
        """
        # Validate file
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Check file size (Whisper API limit is 25MB)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(
                f"File too large: {file_size_mb:.2f}MB. "
                f"OpenAI Whisper API limit is 25MB. "
                f"Consider compressing or splitting the file."
            )
        
        # Retry loop for API resilience
        for attempt in range(self.max_retries):
            try:
                # Open and transcribe audio file
                with open(audio_path, 'rb') as audio_file:
                    # Build API request parameters
                    kwargs = {
                        'model': self.model,
                        'file': audio_file,
                        'response_format': response_format,
                        'temperature': temperature
                    }
                    
                    if language:
                        kwargs['language'] = language
                    
                    if prompt:
                        kwargs['prompt'] = prompt
                    
                    # Call Whisper API
                    transcript = self.client.audio.transcriptions.create(**kwargs)
                
                # Format response based on response_format
                if response_format == 'text':
                    result = {
                        'text': transcript,
                        'language': language or 'en',
                        'file_size_mb': file_size_mb
                    }
                elif response_format == 'json':
                    result = {
                        'text': transcript.text,
                        'language': language or 'en',
                        'file_size_mb': file_size_mb
                    }
                elif response_format == 'verbose_json':
                    result = {
                        'text': transcript.text,
                        'language': transcript.language,
                        'duration': transcript.duration,
                        'segments': transcript.segments,
                        'file_size_mb': file_size_mb
                    }
                else:
                    result = {'text': str(transcript), 'file_size_mb': file_size_mb}
                
                return result
            
            except RateLimitError as e:
                # Rate limit hit - wait and retry
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Rate limit hit. Retrying in {wait_time}s... (Attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise OpenAIError(f"Rate limit exceeded after {self.max_retries} attempts: {e}")
            
            except APIError as e:
                # API error - retry with backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"API error. Retrying in {wait_time}s... (Attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                else:
                    raise OpenAIError(f"API error after {self.max_retries} attempts: {e}")
            
            except OpenAIError as e:
                # Other OpenAI errors
                raise OpenAIError(f"OpenAI API error: {e}")
    
    def transcribe_batch(
        self,
        audio_paths: list,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        verbose: bool = True
    ) -> list:
        """
        Transcribe multiple audio files in batch.
        
        Args:
            audio_paths: List of audio file paths
            language: ISO-639-1 language code (applied to all files)
            prompt: Optional text to guide transcription style
            verbose: Print progress messages
        
        Returns:
            List of dictionaries with transcription results:
                - file_path: Original file path
                - text: Transcribed text
                - success: Boolean indicating success
                - error: Error message (if failed)
                - duration_seconds: Time taken for transcription
        """
        results = []
        total = len(audio_paths)
        
        for i, audio_path in enumerate(audio_paths, 1):
            if verbose:
                print(f"\n[{i}/{total}] Transcribing: {Path(audio_path).name}")
            
            start_time = time.time()
            
            try:
                # Transcribe single file
                transcript = self.transcribe(
                    audio_path=audio_path,
                    language=language,
                    prompt=prompt,
                    response_format='text'
                )
                
                duration = time.time() - start_time
                
                result = {
                    'file_path': str(audio_path),
                    'text': transcript['text'],
                    'success': True,
                    'error': None,
                    'duration_seconds': duration,
                    'file_size_mb': transcript.get('file_size_mb', 0)
                }
                
                if verbose:
                    print(f"  ✓ Success ({duration:.2f}s, {len(transcript['text'])} chars)")
                
            except Exception as e:
                duration = time.time() - start_time
                
                result = {
                    'file_path': str(audio_path),
                    'text': None,
                    'success': False,
                    'error': str(e),
                    'duration_seconds': duration,
                    'file_size_mb': 0
                }
                
                if verbose:
                    print(f"  ✗ Failed: {e}")
            
            results.append(result)
        
        return results
    
    def estimate_cost(self, audio_duration_minutes: float) -> float:
        """
        Estimate transcription cost for given audio duration.
        
        OpenAI Whisper API pricing: $0.006 per minute
        
        Args:
            audio_duration_minutes: Total audio duration in minutes
        
        Returns:
            Estimated cost in USD
        """
        cost_per_minute = 0.006
        return audio_duration_minutes * cost_per_minute
    
    def get_supported_formats(self) -> list:
        """
        Get list of audio formats supported by Whisper API.
        
        Returns:
            List of supported file extensions
        """
        return [
            'flac', 'mp3', 'mp4', 'm4a', 'mpeg', 'mpga',
            'oga', 'ogg', 'wav', 'webm'
        ]


# Quick usage example
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("OPENAI WHISPER API TRANSCRIBER")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in .env file")
        sys.exit(1)
    
    print(f"\n✓ API key found: {api_key[:20]}...")
    
    # Initialize transcriber
    transcriber = WhisperAPITranscriber()
    
    print(f"\nSupported formats: {', '.join(transcriber.get_supported_formats())}")
    
    # Example: Estimate cost for 16 calls at 15 minutes each
    print(f"\n" + "=" * 60)
    print("COST ESTIMATION")
    print("=" * 60)
    
    total_minutes = 16 * 15  # 16 calls, 15 min each
    estimated_cost = transcriber.estimate_cost(total_minutes)
    
    print(f"\nAssuming 16 calls × 15 minutes = {total_minutes} minutes")
    print(f"Estimated cost: ${estimated_cost:.2f}")
    print(f"Cost per call: ${estimated_cost/16:.2f}")
    
    print("\n" + "=" * 60)
    print("Ready to transcribe audio files!")
    print("=" * 60)
