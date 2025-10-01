#!/usr/bin/env python3
"""
성능 분석기
공격 전후 성능 비교 및 DoS 효과 분석
"""

import json
import time
import subprocess
import psutil
from datetime import datetime

class PerformanceAnalyzer:
    def __init__(self):
        self.baseline_stats = {}
        self.attack_stats = {}
        
    def get_baseline_performance(self):
        """공격 전 기준 성능 측정"""
        print("기준 성능 측정 중...")
        
        # CPU 및 메모리
        cpu_percent = psutil.cpu_percent(interval=5)
        memory_percent = psutil.virtual_memory().percent
        
        # 네트워크 통계
        network_io = psutil.net_io_counters()
        
        # 프로세스 수
        process_count = len(psutil.pids())
        
        self.baseline_stats = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "network_bytes_sent": network_io.bytes_sent,
            "network_bytes_recv": network_io.bytes_recv,
            "process_count": process_count
        }
        
        print(f"기준 성능: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%")
        return self.baseline_stats
    
    def get_attack_performance(self):
        """공격 중 성능 측정"""
        print("공격 중 성능 측정...")
        
        # CPU 및 메모리
        cpu_percent = psutil.cpu_percent(interval=5)
        memory_percent = psutil.virtual_memory().percent
        
        # 네트워크 통계
        network_io = psutil.net_io_counters()
        
        # 프로세스 수
        process_count = len(psutil.pids())
        
        self.attack_stats = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "network_bytes_sent": network_io.bytes_sent,
            "network_bytes_recv": network_io.bytes_recv,
            "process_count": process_count
        }
        
        print(f"공격 중 성능: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%")
        return self.attack_stats
    
    def analyze_dos_effectiveness(self):
        """DoS 효과 분석"""
        if not self.baseline_stats or not self.attack_stats:
            print("기준 성능 또는 공격 성능 데이터가 없습니다.")
            return
        
        print("\n" + "="*50)
        print("DoS 공격 효과 분석")
        print("="*50)
        
        # CPU 사용률 변화
        cpu_change = self.attack_stats['cpu_percent'] - self.baseline_stats['cpu_percent']
        print(f"CPU 사용률 변화: {cpu_change:+.1f}%")
        
        # 메모리 사용률 변화
        memory_change = self.attack_stats['memory_percent'] - self.baseline_stats['memory_percent']
        print(f"메모리 사용률 변화: {memory_change:+.1f}%")
        
        # 네트워크 트래픽 변화
        network_sent_change = self.attack_stats['network_bytes_sent'] - self.baseline_stats['network_bytes_sent']
        network_recv_change = self.attack_stats['network_bytes_recv'] - self.baseline_stats['network_bytes_recv']
        print(f"네트워크 송신 변화: {network_sent_change:,} bytes")
        print(f"네트워크 수신 변화: {network_recv_change:,} bytes")
        
        # 프로세스 수 변화
        process_change = self.attack_stats['process_count'] - self.baseline_stats['process_count']
        print(f"프로세스 수 변화: {process_change:+d}")
        
        # 효과 평가
        print("\n" + "-"*30)
        print("공격 효과 평가:")
        
        if cpu_change > 20:
            print("🔥 CPU 사용률이 크게 증가했습니다 (DoS 효과 높음)")
        elif cpu_change > 10:
            print("⚠️  CPU 사용률이 증가했습니다 (DoS 효과 중간)")
        else:
            print("✅ CPU 사용률 변화가 적습니다 (DoS 효과 낮음)")
        
        if memory_change > 10:
            print("🔥 메모리 사용률이 크게 증가했습니다 (DoS 효과 높음)")
        elif memory_change > 5:
            print("⚠️  메모리 사용률이 증가했습니다 (DoS 효과 중간)")
        else:
            print("✅ 메모리 사용률 변화가 적습니다 (DoS 효과 낮음)")
        
        if network_sent_change > 1000000:  # 1MB
            print("🔥 네트워크 트래픽이 크게 증가했습니다 (DoS 효과 높음)")
        elif network_sent_change > 100000:  # 100KB
            print("⚠️  네트워크 트래픽이 증가했습니다 (DoS 효과 중간)")
        else:
            print("✅ 네트워크 트래픽 변화가 적습니다 (DoS 효과 낮음)")
        
        return {
            "cpu_change": cpu_change,
            "memory_change": memory_change,
            "network_sent_change": network_sent_change,
            "network_recv_change": network_recv_change,
            "process_change": process_change
        }
    
    def save_analysis(self, filename="performance_analysis.json"):
        """분석 결과 저장"""
        analysis_data = {
            "baseline": self.baseline_stats,
            "attack": self.attack_stats,
            "analysis": self.analyze_dos_effectiveness()
        }
        
        with open(filename, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"\n분석 결과 저장됨: {filename}")

def main():
    analyzer = PerformanceAnalyzer()
    
    print("성능 분석기 시작")
    print("1. 기준 성능 측정")
    analyzer.get_baseline_performance()
    
    input("\n공격을 시작한 후 Enter를 눌러주세요...")
    
    print("2. 공격 중 성능 측정")
    analyzer.get_attack_performance()
    
    print("3. DoS 효과 분석")
    analyzer.analyze_dos_effectiveness()
    analyzer.save_analysis()

if __name__ == "__main__":
    main()
