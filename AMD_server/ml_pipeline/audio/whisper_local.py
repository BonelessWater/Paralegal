"""
Local Whisper Transcriber - AMD ROCm GPU Accelerated

Fast, private, free audio transcription using Whisper on AMD MI300X.
No API costs, all processing on your hardware.

Usage:
    from audio.whisper_local import WhisperLocalTranscriber
    
    # Initialize (downloads model on first run)
    transcriber = WhisperLocalTranscriber(model_size="large-v3")
    
    # Transcribe single file
    result = transcriber.transcribe("audio.m4a")
    print(result['text'])
    
    # Batch transcribe (optimized for GPU)
    results = transcriber.transcribe_batch(["call1.m4a", "call2.m4a"])
"""

import os
import sys
import time
import torch
from pathlib import Path
from typing import Dict, List, Optional, Union
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')


class WhisperLocalTranscriber:
    """
    Local Whisper transcription using HuggingFace Transformers + ROCm.
    
    Optimized for AMD MI300X GPU with batch processing support.
    
    Attributes:
        model_size: Whisper model size (tiny, base, small, medium, large, large-v3)
        device: Computation device (cuda for AMD ROCm)
        model: Loaded Whisper model
        processor: Audio processor
    """
    
    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = None,
        use_flash_attention: bool = False,  # Disabled by default for AMD ROCm
        torch_dtype: str = "float16"
    ):
        """
        Initialize local Whisper transcriber.
        
        Args:
            model_size: Whisper model variant
                - "tiny": Fastest, 39M params, ~1GB VRAM, English-only
                - "base": Fast, 74M params, ~1.5GB VRAM, multilingual
                - "small": Balanced, 244M params, ~2GB VRAM, multilingual
                - "medium": Better, 769M params, ~5GB VRAM, multilingual
                - "large": Best, 1550M params, ~10GB VRAM, multilingual
                - "large-v3": Latest, 1550M params, ~10GB VRAM, best accuracy
            device: Device to run on (auto-detects AMD GPU if None)
            use_flash_attention: Enable flash attention for faster inference
            torch_dtype: Model precision ("float16" for speed, "float32" for accuracy)
        """
        self.model_size = model_size
        
        # Auto-detect device
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
                print(f"✓ AMD GPU detected: {torch.cuda.get_device_name(0)}")
                print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            else:
                device = "cpu"
                print("⚠️  No GPU detected, using CPU (will be slower)")
        
        self.device = device
        
        # Import transformers (lazy import to avoid dependency issues)
        try:
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
        except ImportError:
            raise ImportError(
                "transformers library not installed. Run:\n"
                "pip install transformers accelerate"
            )
        
        print(f"\nLoading Whisper model: {model_size}")
        print(f"Device: {device}")
        print(f"Precision: {torch_dtype}")
        
        # Set dtype
        torch_dtype = torch.float16 if torch_dtype == "float16" else torch.float32
        
        # Model ID
        model_id = f"openai/whisper-{model_size}"
        
        # Load model
        print(f"Downloading/loading model from HuggingFace...")
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
            attn_implementation="flash_attention_2" if use_flash_attention and device == "cuda" else "eager"
        )
        self.model.to(self.device)
        
        # Load processor
        self.processor = AutoProcessor.from_pretrained(model_id)
        
        # Create pipeline
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            torch_dtype=torch_dtype,
            device=self.device,
        )
        
        print(f"✓ Whisper {model_size} loaded successfully!")
        
        # Cache for loaded audio
        self._audio_cache = {}
    
    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = "transcribe",
        return_timestamps: bool = False,
        batch_size: int = 16
    ) -> Dict:
        """
        Transcribe a single audio file.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', None for auto-detect)
            task: "transcribe" or "translate" (to English)
            return_timestamps: Include word-level timestamps
            batch_size: Batch size for processing chunks
        
        Returns:
            Dictionary with:
                - text: Transcribed text
                - language: Detected/specified language
                - chunks: List of text chunks (if return_timestamps=True)
        """
        # Validate file
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load audio using librosa (supports .m4a)
        import librosa
        audio, sr = librosa.load(str(audio_path), sr=16000, mono=True)
        
        # Prepare generation kwargs
        generate_kwargs = {"task": task}
        if language:
            generate_kwargs["language"] = language
        
        # Transcribe
        print(f"Transcribing: {audio_path.name}")
        start_time = time.time()
        
        result = self.pipe(
            {"array": audio, "sampling_rate": sr},
            generate_kwargs=generate_kwargs,
            return_timestamps=return_timestamps,
            batch_size=batch_size
        )
        
        duration = time.time() - start_time
        
        # Format result
        output = {
            'text': result['text'],
            'language': language or 'auto',
            'duration_seconds': duration,
            'file_path': str(audio_path)
        }
        
        if return_timestamps and 'chunks' in result:
            output['chunks'] = result['chunks']
        
        print(f"✓ Transcribed in {duration:.2f}s ({len(result['text'])} chars)")
        
        return output
    
    def transcribe_batch(
        self,
        audio_paths: List[Union[str, Path]],
        language: Optional[str] = None,
        task: str = "transcribe",
        verbose: bool = True
    ) -> List[Dict]:
        """
        Transcribe multiple audio files (optimized for GPU).
        
        Args:
            audio_paths: List of audio file paths
            language: Language code for all files
            task: "transcribe" or "translate"
            verbose: Print progress
        
        Returns:
            List of transcription results
        """
        results = []
        total = len(audio_paths)
        
        for i, audio_path in enumerate(audio_paths, 1):
            if verbose:
                print(f"\n[{i}/{total}] Processing: {Path(audio_path).name}")
            
            try:
                result = self.transcribe(
                    audio_path=audio_path,
                    language=language,
                    task=task
                )
                result['success'] = True
                result['error'] = None
                
            except Exception as e:
                if verbose:
                    print(f"✗ Error: {e}")
                
                result = {
                    'text': None,
                    'success': False,
                    'error': str(e),
                    'file_path': str(audio_path)
                }
            
            results.append(result)
        
        return results
    
    def get_model_info(self) -> Dict:
        """
        Get information about loaded model.
        
        Returns:
            Dictionary with model details
        """
        return {
            'model_size': self.model_size,
            'device': self.device,
            'gpu_name': torch.cuda.get_device_name(0) if self.device == "cuda" else None,
            'vram_allocated_gb': torch.cuda.memory_allocated(0) / 1e9 if self.device == "cuda" else 0,
            'vram_reserved_gb': torch.cuda.memory_reserved(0) / 1e9 if self.device == "cuda" else 0,
            'parameters': sum(p.numel() for p in self.model.parameters()) / 1e6,  # Millions
        }
    
    def benchmark(
        self,
        audio_path: Union[str, Path],
        num_runs: int = 3
    ) -> Dict:
        """
        Benchmark transcription speed.
        
        Args:
            audio_path: Test audio file
            num_runs: Number of runs to average
        
        Returns:
            Benchmark statistics
        """
        print(f"\nBenchmarking on: {Path(audio_path).name}")
        print(f"Runs: {num_runs}")
        
        times = []
        
        for i in range(num_runs):
            print(f"\nRun {i+1}/{num_runs}...")
            start = time.time()
            result = self.transcribe(audio_path)
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Time: {elapsed:.2f}s")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        stats = {
            'average_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'runs': num_runs,
            'model_info': self.get_model_info()
        }
        
        print(f"\n{'='*60}")
        print("BENCHMARK RESULTS")
        print(f"{'='*60}")
        print(f"Average: {avg_time:.2f}s")
        print(f"Min: {min_time:.2f}s")
        print(f"Max: {max_time:.2f}s")
        print(f"Model: {self.model_size}")
        print(f"Device: {self.device}")
        
        return stats


# Quick test script
if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("LOCAL WHISPER TRANSCRIBER - AMD ROCm")
    print("=" * 70)
    
    # Check PyTorch + ROCm
    print(f"\nPyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Initialize transcriber
    print("\n" + "=" * 70)
    print("INITIALIZING WHISPER")
    print("=" * 70)
    
    # Use large-v3 for best accuracy (you have plenty of VRAM)
    transcriber = WhisperLocalTranscriber(
        model_size="large-v3",
        use_flash_attention=True,
        torch_dtype="float16"
    )
    
    # Show model info
    print("\n" + "=" * 70)
    print("MODEL INFO")
    print("=" * 70)
    info = transcriber.get_model_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    # Test transcription if audio file provided
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        
        print("\n" + "=" * 70)
        print("TEST TRANSCRIPTION")
        print("=" * 70)
        
        result = transcriber.transcribe(audio_file, language="en")
        
        print(f"\nTranscript:")
        print("-" * 70)
        print(result['text'])
        print("-" * 70)
        print(f"Duration: {result['duration_seconds']:.2f}s")
        print(f"Text length: {len(result['text'])} characters")
    else:
        print("\n" + "=" * 70)
        print("READY FOR TRANSCRIPTION")
        print("=" * 70)
        print("\nUsage:")
        print("  python whisper_local.py <audio_file.m4a>")
        print("\nOr in your code:")
        print("  from whisper_local import WhisperLocalTranscriber")
        print("  transcriber = WhisperLocalTranscriber()")
        print("  result = transcriber.transcribe('audio.m4a')")
