#!/usr/bin/env python3
"""
GPU Resource Manager for AMD MI300X
Intelligently manages vLLM and Whisper to share GPU resources
"""

import subprocess
import time
import signal
import sys
from pathlib import Path
from typing import Optional, Dict
from gpu_monitor import GPUMonitor


class GPUResourceManager:
    """Manage GPU resources between vLLM and Whisper."""
    
    def __init__(self):
        self.monitor = GPUMonitor()
        self.vllm_process = None
        self.vllm_config = {
            'model': 'Equall/Saul-7B-Instruct-v1',
            'dtype': 'bfloat16',
            'gpu_memory_utilization': 0.60,  # Reduced from 0.95
            'kv_cache_dtype': 'fp8',  # AMD MI300X FP8 optimization
            'max_model_len': 4096,
            'port': 8000
        }
    
    def get_vllm_pid(self) -> Optional[int]:
        """Get PID of running vLLM process."""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'vllm serve'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split('\n')[0])
        except:
            pass
        return None
    
    def is_vllm_running(self) -> bool:
        """Check if vLLM is currently running."""
        return self.get_vllm_pid() is not None
    
    def stop_vllm(self, graceful: bool = True) -> bool:
        """Stop vLLM server."""
        print("\n🛑 Stopping vLLM server...")
        self.monitor.log_event("vLLM Stop Requested", "vllm")
        
        pid = self.get_vllm_pid()
        if not pid:
            print("   vLLM is not running")
            return True
        
        try:
            if graceful:
                # Try graceful shutdown first
                subprocess.run(['sudo', 'kill', '-TERM', str(pid)], check=False)
                time.sleep(3)
                
                # Check if still running
                if self.get_vllm_pid():
                    print("   Graceful shutdown failed, forcing...")
                    subprocess.run(['sudo', 'kill', '-9', str(pid)], check=False)
                    time.sleep(2)
            else:
                subprocess.run(['sudo', 'kill', '-9', str(pid)], check=False)
                time.sleep(2)
            
            # Verify stopped
            if not self.get_vllm_pid():
                print("   ✓ vLLM stopped successfully")
                self.monitor.log_event("vLLM Stopped", "vllm")
                
                # Clear GPU cache
                time.sleep(2)
                return True
            else:
                print("   ✗ Failed to stop vLLM")
                return False
                
        except Exception as e:
            print(f"   ✗ Error stopping vLLM: {e}")
            return False
    
    def start_vllm_optimized(self) -> bool:
        """Start vLLM with optimized settings for GPU sharing."""
        print("\n🚀 Starting vLLM with optimized settings...")
        print(f"   Memory allocation: {self.vllm_config['gpu_memory_utilization']*100:.0f}%")
        print(f"   KV cache: {self.vllm_config['kv_cache_dtype']}")
        
        self.monitor.log_event("vLLM Start Requested (Optimized)", "vllm")
        
        # Build command
        cmd = [
            'vllm', 'serve', self.vllm_config['model'],
            '--dtype', self.vllm_config['dtype'],
            '--gpu-memory-utilization', str(self.vllm_config['gpu_memory_utilization']),
            '--kv-cache-dtype', self.vllm_config['kv_cache_dtype'],
            '--max-model-len', str(self.vllm_config['max_model_len']),
            '--port', str(self.vllm_config['port'])
        ]
        
        # Set environment variables for AMD ROCm optimization
        env = {
            'VLLM_USE_ROCM_FLASH_ATTN': '1',
            'PYTORCH_HIP_ALLOC_CONF': 'expandable_segments:True',
            **subprocess.os.environ
        }
        
        try:
            # Start vLLM as background process
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait for startup
            print("   Waiting for vLLM to initialize...")
            time.sleep(10)
            
            # Verify it started
            if self.is_vllm_running():
                print("   ✓ vLLM started successfully")
                self.monitor.log_event("vLLM Started (Optimized)", "vllm")
                
                # Log GPU stats after startup
                time.sleep(5)
                stats = self.monitor.log_event("vLLM Running", "vllm")
                
                if stats:
                    memory_saved_gb = 192 * (0.95 - self.vllm_config['gpu_memory_utilization'])
                    print(f"\n💾 Memory Optimization:")
                    print(f"   Before: ~182 GB (95%)")
                    print(f"   After: ~{stats['vram_used_gb']:.1f} GB ({stats['vram_pct']:.1f}%)")
                    print(f"   Freed: ~{memory_saved_gb:.1f} GB for Whisper!")
                
                return True
            else:
                print("   ✗ vLLM failed to start")
                return False
                
        except Exception as e:
            print(f"   ✗ Error starting vLLM: {e}")
            return False
    
    def run_whisper_transcription(self, script_path: str = "bash run_transcription.sh") -> Dict:
        """Run Whisper transcription with monitoring."""
        print("\n🎤 Running Whisper Transcription...")
        self.monitor.log_event("Whisper Start", "whisper")
        
        start_time = time.time()
        
        try:
            # Run transcription
            result = subprocess.run(
                script_path,
                shell=True,
                cwd='/home/amd-knights/Paralegal',
                capture_output=False
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"\n   ✓ Transcription completed in {duration:.1f}s")
                self.monitor.log_event("Whisper Complete", "whisper")
                return {'success': True, 'duration': duration}
            else:
                print(f"\n   ✗ Transcription failed (exit code {result.returncode})")
                self.monitor.log_event("Whisper Failed", "whisper")
                return {'success': False, 'duration': duration}
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"\n   ✗ Error: {e}")
            self.monitor.log_event("Whisper Error", "whisper")
            return {'success': False, 'duration': duration, 'error': str(e)}
    
    def optimize_and_transcribe(self) -> Dict:
        """Main workflow: Optimize vLLM, run Whisper, restore vLLM."""
        print("\n" + "="*80)
        print("GPU RESOURCE OPTIMIZATION & TRANSCRIPTION")
        print("="*80)
        
        # Record initial state
        initial_stats = self.monitor.log_event("Initial State (Before Optimization)")
        
        results = {
            'initial_vram_pct': initial_stats['vram_pct'] if initial_stats else None,
            'optimization_steps': []
        }
        
        # Step 1: Stop vLLM
        if self.stop_vllm():
            results['optimization_steps'].append('vllm_stopped')
            time.sleep(3)
            
            # Log GPU after stopping vLLM
            self.monitor.log_event("After vLLM Stop (GPU Free)")
            
            # Step 2: Run Whisper
            whisper_result = self.run_whisper_transcription()
            results['whisper_result'] = whisper_result
            results['optimization_steps'].append('whisper_complete')
            
            time.sleep(2)
            
            # Step 3: Restart vLLM with optimizations
            if self.start_vllm_optimized():
                results['optimization_steps'].append('vllm_restarted_optimized')
                
                # Record final state
                time.sleep(5)
                final_stats = self.monitor.log_event("Final State (After Optimization)")
                results['final_vram_pct'] = final_stats['vram_pct'] if final_stats else None
                
                # Calculate improvements
                if initial_stats and final_stats:
                    memory_freed = initial_stats['vram_used_gb'] - final_stats['vram_used_gb']
                    pct_reduction = ((initial_stats['vram_pct'] - final_stats['vram_pct']) / 
                                    initial_stats['vram_pct'] * 100)
                    
                    print(f"\n{'='*80}")
                    print("OPTIMIZATION RESULTS")
                    print(f"{'='*80}")
                    print(f"Initial VRAM: {initial_stats['vram_used_gb']:.1f} GB ({initial_stats['vram_pct']:.1f}%)")
                    print(f"Final VRAM: {final_stats['vram_used_gb']:.1f} GB ({final_stats['vram_pct']:.1f}%)")
                    print(f"Memory Freed: {memory_freed:.1f} GB ({pct_reduction:.1f}% reduction)")
                    print(f"Whisper Success: {'✓' if whisper_result.get('success') else '✗'}")
                    print(f"{'='*80}\n")
                    
                    results['memory_freed_gb'] = memory_freed
                    results['pct_reduction'] = pct_reduction
        
        # Generate final report
        print("\n📊 Generating optimization report...")
        self.monitor.generate_report()
        
        return results


def main():
    """Main entry point."""
    manager = GPUResourceManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stop-vllm":
            manager.stop_vllm()
        elif command == "start-vllm":
            manager.start_vllm_optimized()
        elif command == "transcribe":
            manager.optimize_and_transcribe()
        elif command == "status":
            manager.monitor.log_event("Status Check")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python gpu_resource_manager.py [stop-vllm|start-vllm|transcribe|status]")
    else:
        # Default: Run full optimization workflow
        manager.optimize_and_transcribe()


if __name__ == "__main__":
    main()
