#!/usr/bin/env python3
"""
시스템 리소스 모니터링 스크립트
공격 중 시스템 성능 저하를 실시간으로 모니터링
"""

import psutil
import time
import threading
import json
from datetime import datetime

class SystemMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.monitoring = False
        self.stats = []
        
    def get_system_stats(self):
        """시스템 통계 수집"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
            "network_io": psutil.net_io_counters()._asdict(),
            "processes": len(psutil.pids())
        }
        return stats
    
    def monitor_loop(self):
        """모니터링 루프"""
        while self.monitoring:
            stats = self.get_system_stats()
            self.stats.append(stats)
            
            # 실시간 출력
            print(f"[{stats['timestamp']}] CPU: {stats['cpu_percent']:.1f}% | "
                  f"Memory: {stats['memory_percent']:.1f}% | "
                  f"Processes: {stats['processes']}")
            
            time.sleep(self.interval)
    
    def start_monitoring(self):
        """모니터링 시작"""
        print("시스템 모니터링 시작...")
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        print("모니터링 중지됨")
    
    def analyze_performance(self):
        """성능 분석"""
        if len(self.stats) < 2:
            return
        
        # CPU 사용률 분석
        cpu_values = [s['cpu_percent'] for s in self.stats]
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        
        # 메모리 사용률 분석
        memory_values = [s['memory_percent'] for s in self.stats]
        avg_memory = sum(memory_values) / len(memory_values)
        max_memory = max(memory_values)
        
        print("\n=== 성능 분석 결과 ===")
        print(f"평균 CPU 사용률: {avg_cpu:.1f}%")
        print(f"최대 CPU 사용률: {max_cpu:.1f}%")
        print(f"평균 메모리 사용률: {avg_memory:.1f}%")
        print(f"최대 메모리 사용률: {max_memory:.1f}%")
        
        # 성능 저하 경고
        if max_cpu > 80:
            print("⚠️  CPU 사용률이 높습니다 (80% 초과)")
        if max_memory > 80:
            print("⚠️  메모리 사용률이 높습니다 (80% 초과)")
        
        return {
            "avg_cpu": avg_cpu,
            "max_cpu": max_cpu,
            "avg_memory": avg_memory,
            "max_memory": max_memory
        }
    
    def save_stats(self, filename="system_stats.json"):
        """통계를 JSON 파일로 저장"""
        with open(filename, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"시스템 통계 저장됨: {filename}")

def main():
    monitor = SystemMonitor(interval=5)
    
    try:
        monitor.start_monitoring()
        print("모니터링 중... (Ctrl+C로 중지)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n모니터링 중지")
        monitor.stop_monitoring()
        monitor.analyze_performance()
        monitor.save_stats()

if __name__ == "__main__":
    main()
