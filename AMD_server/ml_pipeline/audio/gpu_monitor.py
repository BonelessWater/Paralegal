#!/usr/bin/env python3
"""
Lightweight GPU Memory Monitor for AMD MI300X
Integrates with existing ML pipeline for optimization tracking
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import csv


class GPUMonitor:
    """Monitor AMD GPU for optimization metrics (lightweight)."""
    
    def __init__(self, log_file: str = None):
        if log_file is None:
            log_dir = Path(__file__).parent / "gpu_logs"
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / f"gpu_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            self.log_file = Path(log_file)
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_gpu_stats(self) -> dict:
        """Get current GPU stats using rocm-smi."""
        try:
            # Get basic stats
            result = subprocess.run(['rocm-smi', '--showuse', '--showmeminfo', 'vram'],
                                   capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.split('\n')
            stats = {'timestamp': datetime.now().isoformat()}
            
            for line in lines:
                if 'GPU use' in line:
                    stats['gpu_util_pct'] = float(line.split('%')[0].split()[-1])
                elif 'VRAM%' in line or 'VRAM Total Memory' in line:
                    # Parse VRAM percentage
                    if '%' in line:
                        stats['vram_pct'] = float(line.split('%')[0].split()[-1])
            
            return stats if 'vram_pct' in stats else None
            
        except Exception as e:
            print(f"Warning: Could not get GPU stats: {e}")
            return None
    
    def log_simple(self, event: str):
        """Simple logging - just timestamp, event, and VRAM%."""
        stats = self.get_gpu_stats()
        if stats:
            # Write to CSV (create header if new file)
            write_header = not self.log_file.exists()
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(['timestamp', 'event', 'vram_pct', 'gpu_util_pct'])
                writer.writerow([
                    stats['timestamp'], event,
                    stats.get('vram_pct', 0), stats.get('gpu_util_pct', 0)
                ])
            
            print(f"[GPU] {event}: VRAM {stats.get('vram_pct', 0):.1f}%")
        return stats


# Quick CLI usage
if __name__ == "__main__":
    monitor = GPUMonitor()
    monitor.log_simple("Manual check")

    
    def log_event(self, event: str, process_name: str = ""):
        """Log a GPU event with current metrics."""
        stats = self.get_gpu_stats()
        if stats:
            with open(self.metrics_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    stats['timestamp'],
                    stats['gpu_util_pct'],
                    stats['vram_used_gb'],
                    stats['vram_total_gb'],
                    stats['vram_pct'],
                    stats['power_watts'],
                    stats['temp_c'],
                    process_name,
                    event
                ])
            
            print(f"\n{'='*70}")
            print(f"GPU METRICS - {event}")
            print(f"{'='*70}")
            print(f"VRAM: {stats['vram_used_gb']:.2f} GB / {stats['vram_total_gb']:.2f} GB ({stats['vram_pct']:.1f}%)")
            print(f"GPU Utilization: {stats['gpu_util_pct']:.1f}%")
            print(f"Power: {stats['power_watts']:.1f} W")
            print(f"Temperature: {stats['temp_c']:.1f}°C")
            print(f"{'='*70}\n")
            
            return stats
        return None
    
    def monitor_continuous(self, duration_seconds: int, interval: float = 1.0, process_name: str = ""):
        """Continuously monitor GPU for a duration."""
        start_time = time.time()
        samples = []
        
        print(f"\n📊 Monitoring GPU for {duration_seconds} seconds...")
        
        while time.time() - start_time < duration_seconds:
            stats = self.get_gpu_stats()
            if stats:
                samples.append(stats)
                with open(self.metrics_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        stats['timestamp'],
                        stats['gpu_util_pct'],
                        stats['vram_used_gb'],
                        stats['vram_total_gb'],
                        stats['vram_pct'],
                        stats['power_watts'],
                        stats['temp_c'],
                        process_name,
                        'continuous_monitor'
                    ])
            time.sleep(interval)
        
        # Calculate averages
        if samples:
            avg_vram = sum(s['vram_used_gb'] for s in samples) / len(samples)
            avg_util = sum(s['gpu_util_pct'] for s in samples) / len(samples)
            avg_power = sum(s['power_watts'] for s in samples) / len(samples)
            
            print(f"\n{'='*70}")
            print(f"MONITORING SUMMARY ({len(samples)} samples)")
            print(f"{'='*70}")
            print(f"Average VRAM: {avg_vram:.2f} GB ({avg_vram/samples[0]['vram_total_gb']*100:.1f}%)")
            print(f"Average GPU Util: {avg_util:.1f}%")
            print(f"Average Power: {avg_power:.1f} W")
            print(f"{'='*70}\n")
            
            return {
                'avg_vram_gb': avg_vram,
                'avg_util_pct': avg_util,
                'avg_power_watts': avg_power,
                'samples': len(samples)
            }
        return None
    
    def generate_report(self) -> str:
        """Generate optimization report from logged metrics."""
        report_file = self.log_dir / f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Read all metrics
        metrics = []
        with open(self.metrics_file, 'r') as f:
            reader = csv.DictReader(f)
            metrics = list(reader)
        
        if not metrics:
            return "No metrics collected yet."
        
        # Analyze by event type
        events = {}
        for m in metrics:
            event = m['event']
            if event not in events:
                events[event] = []
            events[event].append(m)
        
        # Generate report
        report = []
        report.append("=" * 80)
        report.append("GPU OPTIMIZATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Samples: {len(metrics)}")
        report.append("")
        
        for event_name, event_metrics in events.items():
            if not event_metrics:
                continue
                
            vram_vals = [float(m['vram_used_gb']) for m in event_metrics]
            util_vals = [float(m['gpu_util_pct']) for m in event_metrics]
            power_vals = [float(m['power_watts']) for m in event_metrics]
            
            report.append("-" * 80)
            report.append(f"EVENT: {event_name}")
            report.append("-" * 80)
            report.append(f"Samples: {len(event_metrics)}")
            report.append(f"VRAM Usage:")
            report.append(f"  Average: {sum(vram_vals)/len(vram_vals):.2f} GB")
            report.append(f"  Min: {min(vram_vals):.2f} GB")
            report.append(f"  Max: {max(vram_vals):.2f} GB")
            report.append(f"GPU Utilization:")
            report.append(f"  Average: {sum(util_vals)/len(util_vals):.1f}%")
            report.append(f"  Min: {min(util_vals):.1f}%")
            report.append(f"  Max: {max(util_vals):.1f}%")
            report.append(f"Power Consumption:")
            report.append(f"  Average: {sum(power_vals)/len(power_vals):.1f} W")
            report.append(f"  Min: {min(power_vals):.1f} W")
            report.append(f"  Max: {max(power_vals):.1f} W")
            report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save to file
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\n📄 Report saved to: {report_file}")
        
        return report_text


if __name__ == "__main__":
    import sys
    
    monitor = GPUMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            monitor.log_event("Manual Status Check")
        elif sys.argv[1] == "monitor":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            monitor.monitor_continuous(duration)
        elif sys.argv[1] == "report":
            monitor.generate_report()
    else:
        monitor.log_event("Manual Status Check")
