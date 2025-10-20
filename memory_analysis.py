#!/usr/bin/env python3
"""
DoS 공격 시 메모리 사용량 분석 및 시각화 도구
시간당 연결 수와 메모리 점유율을 추적하여 크래시까지의 과정을 시각화합니다.
"""

import psutil
import time
import threading
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import deque
import argparse
import os

class MemoryMonitor:
    def __init__(self, monitoring_interval=1.0, max_data_points=3600):
        """
        메모리 모니터링 클래스
        
        Args:
            monitoring_interval: 모니터링 간격 (초)
            max_data_points: 최대 데이터 포인트 수 (1시간 = 3600초)
        """
        self.monitoring_interval = monitoring_interval
        self.max_data_points = max_data_points
        self.running = False
        
        # 데이터 저장소
        self.timestamps = deque(maxlen=max_data_points)
        self.memory_usage = deque(maxlen=max_data_points)
        self.cpu_usage = deque(maxlen=max_data_points)
        self.connections = deque(maxlen=max_data_points)
        self.process_count = deque(maxlen=max_data_points)
        
        # 통계 정보
        self.stats = {
            "start_time": None,
            "end_time": None,
            "peak_memory": 0,
            "peak_connections": 0,
            "crash_time": None,
            "total_data_points": 0
        }
        
    def get_system_info(self):
        """시스템 정보 수집"""
        try:
            # 메모리 사용량 (MB)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 네트워크 연결 수
            connections = len(psutil.net_connections())
            
            # 프로세스 수
            process_count = len(psutil.pids())
            
            return {
                "memory_mb": memory_mb,
                "memory_percent": memory.percent,
                "cpu_percent": cpu_percent,
                "connections": connections,
                "process_count": process_count,
                "available_memory_mb": memory.available / (1024 * 1024)
            }
            
        except Exception as e:
            print(f"시스템 정보 수집 오류: {e}")
            return None
    
    def monitor_loop(self):
        """모니터링 루프"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 메모리 모니터링 시작")
        
        while self.running:
            try:
                system_info = self.get_system_info()
                if system_info:
                    current_time = datetime.now()
                    
                    # 데이터 저장
                    self.timestamps.append(current_time)
                    self.memory_usage.append(system_info["memory_percent"])
                    self.cpu_usage.append(system_info["cpu_percent"])
                    self.connections.append(system_info["connections"])
                    self.process_count.append(system_info["process_count"])
                    
                    # 통계 업데이트
                    self.stats["total_data_points"] += 1
                    self.stats["peak_memory"] = max(self.stats["peak_memory"], system_info["memory_percent"])
                    self.stats["peak_connections"] = max(self.stats["peak_connections"], system_info["connections"])
                    
                    # 크래시 감지 (메모리 사용률 95% 이상)
                    if system_info["memory_percent"] >= 95 and not self.stats["crash_time"]:
                        self.stats["crash_time"] = current_time
                        print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️  크래시 임계점 도달! 메모리 사용률: {system_info['memory_percent']:.1f}%")
                    
                    # 주기적 상태 출력
                    if self.stats["total_data_points"] % 60 == 0:  # 1분마다
                        print(f"[{current_time.strftime('%H:%M:%S')}] 메모리: {system_info['memory_percent']:.1f}%, "
                              f"연결: {system_info['connections']}, CPU: {system_info['cpu_percent']:.1f}%")
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"모니터링 오류: {e}")
                time.sleep(self.monitoring_interval)
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.running = False
        self.stats["end_time"] = datetime.now()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 메모리 모니터링 중지")
    
    def save_data(self, filename=None):
        """모니터링 데이터 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"memory_monitor_data_{timestamp}.json"
        
        data = {
            "stats": {
                "start_time": self.stats["start_time"].isoformat() if self.stats["start_time"] else None,
                "end_time": self.stats["end_time"].isoformat() if self.stats["end_time"] else None,
                "peak_memory": self.stats["peak_memory"],
                "peak_connections": self.stats["peak_connections"],
                "crash_time": self.stats["crash_time"].isoformat() if self.stats["crash_time"] else None,
                "total_data_points": self.stats["total_data_points"],
                "monitoring_interval": self.monitoring_interval
            },
            "data": {
                "timestamps": [t.isoformat() for t in self.timestamps],
                "memory_usage": list(self.memory_usage),
                "cpu_usage": list(self.cpu_usage),
                "connections": list(self.connections),
                "process_count": list(self.process_count)
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"모니터링 데이터 저장: {filename}")
            return filename
            
        except Exception as e:
            print(f"데이터 저장 오류: {e}")
            return None
    
    def create_visualization(self, save_plots=True):
        """시각화 생성"""
        if not self.timestamps:
            print("시각화할 데이터가 없습니다.")
            return None
        
        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        
        # 데이터를 DataFrame으로 변환
        df = pd.DataFrame({
            'timestamp': list(self.timestamps),
            'memory_usage': list(self.memory_usage),
            'cpu_usage': list(self.cpu_usage),
            'connections': list(self.connections),
            'process_count': list(self.process_count)
        })
        
        # 시간을 분 단위로 변환
        start_time = df['timestamp'].iloc[0]
        df['minutes'] = [(t - start_time).total_seconds() / 60 for t in df['timestamp']]
        
        # 그래프 생성
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('DoS 공격 시 시스템 리소스 사용량 분석', fontsize=16, fontweight='bold')
        
        # 1. 메모리 사용률
        axes[0, 0].plot(df['minutes'], df['memory_usage'], 'b-', linewidth=2, label='메모리 사용률')
        axes[0, 0].axhline(y=95, color='r', linestyle='--', alpha=0.7, label='크래시 임계점 (95%)')
        axes[0, 0].axhline(y=80, color='orange', linestyle='--', alpha=0.7, label='경고 임계점 (80%)')
        
        if self.stats["crash_time"]:
            crash_minutes = (self.stats["crash_time"] - start_time).total_seconds() / 60
            axes[0, 0].axvline(x=crash_minutes, color='r', linestyle=':', alpha=0.8, label=f'크래시 시점 ({crash_minutes:.1f}분)')
        
        axes[0, 0].set_title('메모리 사용률 (%)', fontweight='bold')
        axes[0, 0].set_xlabel('시간 (분)')
        axes[0, 0].set_ylabel('메모리 사용률 (%)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 100)
        
        # 2. 네트워크 연결 수
        axes[0, 1].plot(df['minutes'], df['connections'], 'g-', linewidth=2, label='네트워크 연결 수')
        axes[0, 1].set_title('네트워크 연결 수', fontweight='bold')
        axes[0, 1].set_xlabel('시간 (분)')
        axes[0, 1].set_ylabel('연결 수')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. CPU 사용률
        axes[1, 0].plot(df['minutes'], df['cpu_usage'], 'purple', linewidth=2, label='CPU 사용률')
        axes[1, 0].set_title('CPU 사용률 (%)', fontweight='bold')
        axes[1, 0].set_xlabel('시간 (분)')
        axes[1, 0].set_ylabel('CPU 사용률 (%)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 100)
        
        # 4. 프로세스 수
        axes[1, 1].plot(df['minutes'], df['process_count'], 'orange', linewidth=2, label='프로세스 수')
        axes[1, 1].set_title('프로세스 수', fontweight='bold')
        axes[1, 1].set_xlabel('시간 (분)')
        axes[1, 1].set_ylabel('프로세스 수')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_filename = f"dos_memory_analysis_{timestamp}.png"
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"시각화 그래프 저장: {plot_filename}")
        
        plt.show()
        return fig
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        if not self.timestamps:
            return "데이터가 없습니다."
        
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds() / 60 if self.stats["end_time"] else 0
        
        report = f"""
=== DoS 공격 메모리 분석 보고서 ===

📊 모니터링 정보:
- 시작 시간: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S') if self.stats['start_time'] else 'N/A'}
- 종료 시간: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S') if self.stats['end_time'] else 'N/A'}
- 모니터링 지속 시간: {duration:.1f}분
- 데이터 포인트 수: {self.stats['total_data_points']}개

📈 피크 값:
- 최대 메모리 사용률: {self.stats['peak_memory']:.1f}%
- 최대 네트워크 연결 수: {self.stats['peak_connections']}개

⚠️  크래시 정보:
- 크래시 발생 시간: {self.stats['crash_time'].strftime('%Y-%m-%d %H:%M:%S') if self.stats['crash_time'] else '크래시 미발생'}
- 크래시까지 소요 시간: {f"{((self.stats['crash_time'] - self.stats['start_time']).total_seconds() / 60):.1f}분" if self.stats['crash_time'] and self.stats['start_time'] else 'N/A'}

💾 메모리 분석:
- 평균 메모리 사용률: {np.mean(list(self.memory_usage)):.1f}%
- 메모리 사용률 표준편차: {np.std(list(self.memory_usage)):.1f}%
- 메모리 사용률 증가율: {((list(self.memory_usage)[-1] - list(self.memory_usage)[0]) / len(self.memory_usage) * 60):.2f}% per minute

🔗 연결 분석:
- 평균 연결 수: {np.mean(list(self.connections)):.0f}개
- 연결 수 증가율: {((list(self.connections)[-1] - list(self.connections)[0]) / len(self.connections) * 60):.1f} connections per minute

========================================
        """
        
        return report

def simulate_dos_attack_with_monitoring(duration_minutes=10, attack_intensity="medium"):
    """
    DoS 공격 시뮬레이션과 함께 메모리 모니터링 실행
    
    Args:
        duration_minutes: 시뮬레이션 지속 시간 (분)
        attack_intensity: 공격 강도 ("low", "medium", "high")
    """
    print("=== DoS 공격 시뮬레이션 시작 ===")
    
    # 메모리 모니터 생성
    monitor = MemoryMonitor(monitoring_interval=1.0)
    
    # 모니터링 시작
    monitor_thread = monitor.start_monitoring()
    
    try:
        # 시뮬레이션 실행
        duration_seconds = duration_minutes * 60
        
        if attack_intensity == "low":
            # 낮은 강도: CPU 집약적 작업
            simulate_cpu_intensive_work(duration_seconds, intensity=0.3)
        elif attack_intensity == "medium":
            # 중간 강도: 메모리 + CPU 집약적 작업
            simulate_memory_intensive_work(duration_seconds, intensity=0.6)
        elif attack_intensity == "high":
            # 높은 강도: 메모리 누수 시뮬레이션
            simulate_memory_leak(duration_seconds, intensity=0.9)
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    finally:
        # 모니터링 중지
        monitor.stop_monitoring()
        monitor_thread.join(timeout=5)
        
        # 결과 저장 및 시각화
        data_file = monitor.save_data()
        monitor.create_visualization()
        
        # 요약 보고서 출력
        report = monitor.generate_summary_report()
        print(report)
        
        # 보고서 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"dos_analysis_report_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"분석 보고서 저장: {report_filename}")

def simulate_cpu_intensive_work(duration, intensity=0.5):
    """CPU 집약적 작업 시뮬레이션"""
    print(f"CPU 집약적 작업 시뮬레이션 시작 (강도: {intensity})")
    
    start_time = time.time()
    while time.time() - start_time < duration:
        # CPU 집약적 계산
        for _ in range(int(1000000 * intensity)):
            _ = sum(range(100))
        time.sleep(0.1)

def simulate_memory_intensive_work(duration, intensity=0.5):
    """메모리 집약적 작업 시뮬레이션"""
    print(f"메모리 집약적 작업 시뮬레이션 시작 (강도: {intensity})")
    
    memory_blocks = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # 메모리 블록 할당 (1MB씩)
        block_size = int(1024 * 1024 * intensity)  # MB
        memory_blocks.append(bytearray(block_size))
        
        # 일부 메모리 해제 (메모리 압박 효과)
        if len(memory_blocks) > 100:
            memory_blocks = memory_blocks[50:]  # 절반 해제
        
        time.sleep(0.1)

def simulate_memory_leak(duration, intensity=0.8):
    """메모리 누수 시뮬레이션"""
    print(f"메모리 누수 시뮬레이션 시작 (강도: {intensity})")
    
    memory_blocks = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # 메모리 블록 할당 (누적)
        block_size = int(1024 * 1024 * intensity)  # MB
        memory_blocks.append(bytearray(block_size))
        
        # 메모리 해제하지 않음 (누수)
        time.sleep(0.05)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="DoS 공격 메모리 분석 도구")
    parser.add_argument("--duration", type=int, default=10, help="시뮬레이션 지속 시간 (분)")
    parser.add_argument("--intensity", choices=["low", "medium", "high"], default="medium", 
                       help="공격 강도")
    parser.add_argument("--monitor-only", action="store_true", help="모니터링만 실행 (시뮬레이션 없음)")
    
    args = parser.parse_args()
    
    if args.monitor_only:
        # 모니터링만 실행
        monitor = MemoryMonitor()
        monitor_thread = monitor.start_monitoring()
        
        try:
            print("모니터링 중... (Ctrl+C로 중지)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n모니터링 중지")
        finally:
            monitor.stop_monitoring()
            monitor_thread.join(timeout=5)
            monitor.save_data()
            monitor.create_visualization()
            print(monitor.generate_summary_report())
    else:
        # 시뮬레이션과 함께 실행
        simulate_dos_attack_with_monitoring(args.duration, args.intensity)

if __name__ == "__main__":
    main()
