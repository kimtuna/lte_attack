#!/usr/bin/env python3
"""
통합 DoS 공격 분석 도구
실제 flooding 공격과 메모리 모니터링을 동시에 실행하여 크래시까지의 과정을 분석합니다.
"""

import subprocess
import threading
import time
import json
import os
import signal
import sys
from datetime import datetime
from memory_analysis import MemoryMonitor
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class IntegratedDoSAnalyzer:
    def __init__(self):
        self.monitor = MemoryMonitor(monitoring_interval=0.5)  # 더 자주 모니터링
        self.flooding_process = None
        self.running = False
        self.attack_stats = {
            "start_time": None,
            "end_time": None,
            "messages_sent": 0,
            "connections_created": 0,
            "crash_detected": False,
            "crash_time": None
        }
        
    def start_flooding_attack(self, messages_file, target_ip="127.0.0.1", target_port=2001, 
                            threads=20, duration=300, interval=0.001, batch_size=5):
        """
        Flooding 공격 시작
        
        Args:
            messages_file: RRC 메시지 파일 경로
            target_ip: 대상 IP
            target_port: 대상 포트
            threads: 스레드 수
            duration: 지속 시간 (초)
            interval: 메시지 간격
            batch_size: 배치 크기
        """
        if not os.path.exists(messages_file):
            print(f"메시지 파일을 찾을 수 없습니다: {messages_file}")
            return False
        
        # Flooding 공격 명령어 구성
        cmd = [
            "python3", "flooding_attack.py",
            "--target-ip", target_ip,
            "--target-port", str(target_port),
            "--messages", messages_file,
            "--threads", str(threads),
            "--duration", str(duration),
            "--interval", str(interval),
            "--batch-size", str(batch_size)
        ]
        
        print(f"=== Flooding 공격 시작 ===")
        print(f"대상: {target_ip}:{target_port}")
        print(f"스레드: {threads}, 지속시간: {duration}초")
        print(f"간격: {interval}초, 배치크기: {batch_size}")
        print("=" * 50)
        
        try:
            # 공격 프로세스 시작
            self.flooding_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.attack_stats["start_time"] = datetime.now()
            return True
            
        except Exception as e:
            print(f"공격 시작 오류: {e}")
            return False
    
    def monitor_attack_progress(self):
        """공격 진행 상황 모니터링"""
        if not self.flooding_process:
            return
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 공격 진행 상황 모니터링 시작")
        
        # 연결 수 추적을 위한 변수들
        max_connections = 0
        connection_drop_threshold = 0.1  # 10% 이하로 떨어지면 크래시로 판단
        stable_connections = 0
        connection_drop_count = 0
        
        while self.running and self.flooding_process.poll() is None:
            try:
                # 공격 프로세스 상태 확인
                if self.flooding_process.poll() is not None:
                    break
                
                # 시스템 리소스 확인
                system_info = self.monitor.get_system_info()
                if system_info:
                    current_connections = system_info["connections"]
                    
                    # 최대 연결 수 업데이트
                    if current_connections > max_connections:
                        max_connections = current_connections
                        stable_connections = current_connections
                    
                    # 연결 수 급격한 감소 감지 (크래시 감지)
                    if max_connections > 1000:  # 충분한 연결이 있었을 때만 체크
                        connection_ratio = current_connections / max_connections
                        
                        if connection_ratio < connection_drop_threshold:
                            connection_drop_count += 1
                            if connection_drop_count >= 3:  # 3회 연속 감소 확인
                                self.attack_stats["crash_detected"] = True
                                self.attack_stats["crash_time"] = datetime.now()
                                crash_duration = (self.attack_stats["crash_time"] - self.attack_stats["start_time"]).total_seconds() / 60
                                
                                print(f"\n🚨 SERVER CRASH DETECTED! 🚨")
                                print(f"시간: {self.attack_stats['crash_time'].strftime('%H:%M:%S')}")
                                print(f"크래시까지 소요 시간: {crash_duration:.1f}분")
                                print(f"최대 연결 수: {max_connections}개")
                                print(f"현재 연결 수: {current_connections}개")
                                print(f"연결 수 감소율: {(1 - connection_ratio) * 100:.1f}%")
                                print(f"메모리 사용률: {system_info['memory_percent']:.1f}%")
                                print("=" * 50)
                                
                                # 공격 중지
                                self.stop_attack()
                                break
                        else:
                            connection_drop_count = 0  # 리셋
                    
                    # 기존 메모리 크래시 감지
                    if system_info["memory_percent"] >= 95 and not self.attack_stats["crash_detected"]:
                        self.attack_stats["crash_detected"] = True
                        self.attack_stats["crash_time"] = datetime.now()
                        crash_duration = (self.attack_stats["crash_time"] - self.attack_stats["start_time"]).total_seconds() / 60
                        
                        print(f"\n🚨 MEMORY CRASH DETECTED! 🚨")
                        print(f"시간: {self.attack_stats['crash_time'].strftime('%H:%M:%S')}")
                        print(f"크래시까지 소요 시간: {crash_duration:.1f}분")
                        print(f"메모리 사용률: {system_info['memory_percent']:.1f}%")
                        print(f"연결 수: {system_info['connections']}")
                        print("=" * 50)
                        
                        # 공격 중지
                        self.stop_attack()
                        break
                    
                    # 주기적 상태 출력
                    elapsed = (datetime.now() - self.attack_stats["start_time"]).total_seconds()
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"경과: {elapsed:.0f}초 | "
                          f"메모리: {system_info['memory_percent']:.1f}% | "
                          f"연결: {system_info['connections']} | "
                          f"CPU: {system_info['cpu_percent']:.1f}%")
                
                time.sleep(5)  # 5초마다 체크
                
            except Exception as e:
                print(f"모니터링 오류: {e}")
                time.sleep(5)
    
    def stop_attack(self):
        """공격 중지"""
        if self.flooding_process and self.flooding_process.poll() is None:
            print("공격 프로세스 중지 중...")
            self.flooding_process.terminate()
            
            # 강제 종료 대기
            try:
                self.flooding_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("강제 종료...")
                self.flooding_process.kill()
                self.flooding_process.wait()
        
        self.attack_stats["end_time"] = datetime.now()
        self.running = False
    
    def run_analysis(self, messages_file, **attack_params):
        """통합 분석 실행"""
        print("=== 통합 DoS 공격 분석 시작 ===")
        
        # 기본 공격 파라미터
        default_params = {
            "target_ip": "127.0.0.1",
            "target_port": 2001,
            "threads": 20,
            "duration": 300,  # 5분
            "interval": 0.001,
            "batch_size": 5
        }
        default_params.update(attack_params)
        
        try:
            # 메모리 모니터링 시작
            monitor_thread = self.monitor.start_monitoring()
            self.running = True
            
            # Flooding 공격 시작
            if not self.start_flooding_attack(messages_file, **default_params):
                return False
            
            # 공격 모니터링 시작
            attack_monitor_thread = threading.Thread(target=self.monitor_attack_progress)
            attack_monitor_thread.start()
            
            # 공격 완료 대기
            if self.flooding_process:
                self.flooding_process.wait()
            
            # 모든 스레드 종료 대기
            self.running = False
            attack_monitor_thread.join(timeout=10)
            
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단됨")
            self.stop_attack()
        except Exception as e:
            print(f"분석 실행 오류: {e}")
            self.stop_attack()
        finally:
            # 모니터링 중지
            self.monitor.stop_monitoring()
            monitor_thread.join(timeout=5)
            
            # 결과 분석 및 저장
            self.generate_comprehensive_report()
    
    def generate_comprehensive_report(self):
        """종합 분석 보고서 생성"""
        print("\n=== 종합 분석 보고서 생성 ===")
        
        # 데이터 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = self.monitor.save_data(f"integrated_dos_analysis_{timestamp}.json")
        
        # 시각화 생성
        self.create_comprehensive_visualization()
        
        # 상세 보고서 생성
        report = self.create_detailed_report()
        
        # 보고서 파일 저장
        report_filename = f"comprehensive_dos_report_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"종합 분석 보고서 저장: {report_filename}")
        print("\n" + "="*60)
        print(report)
        print("="*60)
    
    def create_comprehensive_visualization(self):
        """종합 시각화 생성"""
        if not self.monitor.timestamps:
            print("시각화할 데이터가 없습니다.")
            return
        
        # 한글 폰트 설정 (Ubuntu 환경)
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        
        # 데이터 준비
        df = pd.DataFrame({
            'timestamp': list(self.monitor.timestamps),
            'memory_usage': list(self.monitor.memory_usage),
            'cpu_usage': list(self.monitor.cpu_usage),
            'connections': list(self.monitor.connections),
            'process_count': list(self.monitor.process_count)
        })
        
        # 시간을 분 단위로 변환
        start_time = df['timestamp'].iloc[0]
        df['minutes'] = [(t - start_time).total_seconds() / 60 for t in df['timestamp']]
        
        # 크래시 시점 계산
        crash_minutes = None
        if self.attack_stats["crash_time"]:
            crash_minutes = (self.attack_stats["crash_time"] - start_time).total_seconds() / 60
        
        # 그래프 생성
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('DoS Attack Analysis: Memory Usage to Crash', fontsize=18, fontweight='bold')
        
        # 1. 메모리 사용률 (메인 차트)
        axes[0, 0].plot(df['minutes'], df['memory_usage'], 'b-', linewidth=3, label='Memory Usage')
        axes[0, 0].axhline(y=95, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Crash Threshold (95%)')
        axes[0, 0].axhline(y=80, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Warning Threshold (80%)')
        axes[0, 0].axhline(y=60, color='yellow', linestyle='--', linewidth=1, alpha=0.6, label='Caution Threshold (60%)')
        
        if crash_minutes:
            axes[0, 0].axvline(x=crash_minutes, color='red', linestyle=':', linewidth=3, alpha=0.9, 
                              label=f'Crash Detected ({crash_minutes:.1f}min)')
        
        axes[0, 0].set_title('Memory Usage Change', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('Time (minutes)', fontsize=12)
        axes[0, 0].set_ylabel('Memory Usage (%)', fontsize=12)
        axes[0, 0].legend(fontsize=10)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 100)
        
        # 2. 네트워크 연결 수
        axes[0, 1].plot(df['minutes'], df['connections'], 'g-', linewidth=2, label='Network Connections')
        if crash_minutes:
            axes[0, 1].axvline(x=crash_minutes, color='red', linestyle=':', linewidth=2, alpha=0.8)
        axes[0, 1].set_title('Network Connections Change', fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('Time (minutes)', fontsize=12)
        axes[0, 1].set_ylabel('Connections', fontsize=12)
        axes[0, 1].legend(fontsize=10)
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. CPU 사용률
        axes[1, 0].plot(df['minutes'], df['cpu_usage'], 'purple', linewidth=2, label='CPU Usage')
        if crash_minutes:
            axes[1, 0].axvline(x=crash_minutes, color='red', linestyle=':', linewidth=2, alpha=0.8)
        axes[1, 0].set_title('CPU Usage Change', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('Time (minutes)', fontsize=12)
        axes[1, 0].set_ylabel('CPU Usage (%)', fontsize=12)
        axes[1, 0].legend(fontsize=10)
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 100)
        
        # 4. 프로세스 수
        axes[1, 1].plot(df['minutes'], df['process_count'], 'orange', linewidth=2, label='Process Count')
        if crash_minutes:
            axes[1, 1].axvline(x=crash_minutes, color='red', linestyle=':', linewidth=2, alpha=0.8)
        axes[1, 1].set_title('Process Count Change', fontsize=14, fontweight='bold')
        axes[1, 1].set_xlabel('Time (minutes)', fontsize=12)
        axes[1, 1].set_ylabel('Process Count', fontsize=12)
        axes[1, 1].legend(fontsize=10)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 그래프 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_filename = f"comprehensive_dos_analysis_{timestamp}.png"
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"종합 분석 그래프 저장: {plot_filename}")
        
        plt.show()
        return fig
    
    def create_detailed_report(self):
        """상세 보고서 생성"""
        if not self.monitor.timestamps:
            return "분석할 데이터가 없습니다."
        
        # 크래시 시점까지의 데이터만 분석
        crash_time = self.attack_stats.get("crash_time")
        if crash_time:
            # 크래시 시점까지의 데이터만 필터링
            crash_data = []
            for i, timestamp in enumerate(self.monitor.timestamps):
                if timestamp <= crash_time:
                    crash_data.append({
                        'timestamp': timestamp,
                        'memory': self.monitor.memory_usage[i],
                        'cpu': self.monitor.cpu_usage[i],
                        'connections': self.monitor.connections[i],
                        'processes': self.monitor.process_count[i]
                    })
            
            if not crash_data:
                return "크래시 시점까지의 데이터가 없습니다."
            
            # 크래시까지의 데이터로 분석
            memory_data = [d['memory'] for d in crash_data]
            cpu_data = [d['cpu'] for d in crash_data]
            connections_data = [d['connections'] for d in crash_data]
            process_data = [d['processes'] for d in crash_data]
            
            crash_duration = (crash_time - self.attack_stats["start_time"]).total_seconds() / 60
        else:
            # 크래시가 없었다면 전체 데이터 사용
            memory_data = list(self.monitor.memory_usage)
            cpu_data = list(self.monitor.cpu_usage)
            connections_data = list(self.monitor.connections)
            process_data = list(self.monitor.process_count)
            crash_duration = (self.attack_stats["end_time"] - self.attack_stats["start_time"]).total_seconds() / 60 if self.attack_stats["end_time"] else 0
        
        # 기본 통계 계산
        duration = crash_duration
        
        # 메모리 통계
        memory_start = memory_data[0] if memory_data else 0
        memory_end = memory_data[-1] if memory_data else 0
        memory_peak = max(memory_data) if memory_data else 0
        
        # 연결 통계
        connections_start = connections_data[0] if connections_data else 0
        connections_end = connections_data[-1] if connections_data else 0
        connections_peak = max(connections_data) if connections_data else 0
        
        # 크래시 감지 정보 생성
        crash_detection_info = ""
        if self.attack_stats["crash_detected"] and self.attack_stats["crash_time"]:
            crash_detection_info = f"""
🚨 크래시 감지 정보:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 크래시 발생: 예{'':<50} │
│ 크래시 시간: {self.attack_stats['crash_time'].strftime('%Y-%m-%d %H:%M:%S'):<50} │
│ 크래시까지 소요: {crash_duration:.1f}분{'':<45} │
│ 최대 연결 수: {connections_peak}개{'':<45} │
│ 연결 수 감소율: {((connections_peak - connections_end) / connections_peak * 100):.1f}%{'':<40} │
└─────────────────────────────────────────────────────────────────────────────┘
"""
        else:
            crash_detection_info = f"""
✅ 크래시 미발생:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 공격 완료: 정상 종료{'':<45} │
│ 최대 연결 수: {connections_peak}개{'':<45} │
│ 최종 연결 수: {connections_end}개{'':<45} │
└─────────────────────────────────────────────────────────────────────────────┘
"""
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DoS 공격 통합 분석 보고서                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{crash_detection_info}

📊 공격 개요:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 시작 시간: {self.attack_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S') if self.attack_stats['start_time'] else 'N/A':<50} │
│ 종료 시간: {self.attack_stats['end_time'].strftime('%Y-%m-%d %H:%M:%S') if self.attack_stats['end_time'] else 'N/A':<50} │
│ 총 지속 시간: {duration:.1f}분{'':<45} │
│ 데이터 포인트: {len(memory_data)}개{'':<45} │
└─────────────────────────────────────────────────────────────────────────────┘

🚨 크래시 분석:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 크래시 발생: {'예' if self.attack_stats['crash_detected'] else '아니오':<50} │
│ 크래시 시간: {self.attack_stats['crash_time'].strftime('%Y-%m-%d %H:%M:%S') if self.attack_stats['crash_time'] else 'N/A':<50} │
│ 크래시까지 소요: {f"{crash_duration:.1f}분" if crash_duration > 0 else 'N/A'}{'':<45} │
└─────────────────────────────────────────────────────────────────────────────┘

💾 메모리 분석 (크래시까지):
┌─────────────────────────────────────────────────────────────────────────────┐
│ 초기 메모리 사용률: {memory_start:.1f}%{'':<40} │
│ 최종 메모리 사용률: {memory_end:.1f}%{'':<40} │
│ 최대 메모리 사용률: {memory_peak:.1f}%{'':<40} │
│ 메모리 증가량: {memory_end - memory_start:.1f}%{'':<40} │
│ 평균 메모리 사용률: {np.mean(memory_data):.1f}%{'':<40} │
│ 메모리 증가율: {f"{((memory_end - memory_start) / duration):.2f}% per minute" if duration > 0 else 'N/A'}{'':<25} │
└─────────────────────────────────────────────────────────────────────────────┘

🔗 네트워크 연결 분석 (크래시까지):
┌─────────────────────────────────────────────────────────────────────────────┐
│ 초기 연결 수: {connections_start}개{'':<40} │
│ 최종 연결 수: {connections_end}개{'':<40} │
│ 최대 연결 수: {connections_peak}개{'':<40} │
│ 연결 증가량: {connections_end - connections_start}개{'':<40} │
│ 평균 연결 수: {np.mean(connections_data):.0f}개{'':<40} │
│ 연결 증가율: {f"{((connections_end - connections_start) / duration):.1f} connections per minute" if duration > 0 else 'N/A'}{'':<15} │
└─────────────────────────────────────────────────────────────────────────────┘

📈 시간별 분석 (크래시까지):
┌─────────────────────────────────────────────────────────────────────────────┐
│ CPU 평균 사용률: {np.mean(cpu_data):.1f}%{'':<40} │
│ CPU 최대 사용률: {max(cpu_data):.1f}%{'':<40} │
│ 프로세스 평균 수: {np.mean(process_data):.0f}개{'':<40} │
│ 프로세스 최대 수: {max(process_data)}개{'':<40} │
└─────────────────────────────────────────────────────────────────────────────┘

⚠️  크래시 임계점 분석:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 메모리 60% 도달: {self.get_threshold_time(memory_data, 60):<50} │
│ 메모리 80% 도달: {self.get_threshold_time(memory_data, 80):<50} │
│ 메모리 95% 도달: {self.get_threshold_time(memory_data, 95):<50} │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 결론 및 권장사항:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 크래시 발생 여부: {'크래시 발생' if self.attack_stats['crash_detected'] else '크래시 미발생'}{'':<35} │
│ 2. 주요 원인: {'메모리 부족' if memory_peak >= 95 else '연결 수 급감' if self.attack_stats['crash_detected'] else '리소스 과부하'}{'':<40} │
│ 3. 권장 대응: {'즉시 공격 중지 및 메모리 정리' if self.attack_stats['crash_detected'] else '모니터링 지속'}{'':<25} │
│ 4. 예방 조치: {'메모리 제한 설정 및 연결 수 제한' if self.attack_stats['crash_detected'] else '정상 범위 내 운영'}{'':<25} │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
        """
        
        return report
    
    def get_threshold_time(self, data, threshold):
        """임계점 도달 시간 계산"""
        for i, value in enumerate(data):
            if value >= threshold:
                minutes = i * self.monitor.monitoring_interval / 60
                return f"{minutes:.1f}분"
        return "도달하지 않음"

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="통합 DoS 공격 분석 도구")
    parser.add_argument("--messages", required=True, help="RRC 메시지 분석 파일")
    parser.add_argument("--target-ip", default="127.0.0.1", help="대상 IP 주소")
    parser.add_argument("--target-port", type=int, default=2001, help="대상 포트")
    parser.add_argument("--threads", type=int, default=20, help="스레드 수")
    parser.add_argument("--duration", type=int, default=300, help="지속 시간 (초)")
    parser.add_argument("--interval", type=float, default=0.001, help="메시지 간격 (초)")
    parser.add_argument("--batch-size", type=int, default=5, help="배치 크기")
    
    args = parser.parse_args()
    
    # 분석기 생성 및 실행
    analyzer = IntegratedDoSAnalyzer()
    
    attack_params = {
        "target_ip": args.target_ip,
        "target_port": args.target_port,
        "threads": args.threads,
        "duration": args.duration,
        "interval": args.interval,
        "batch_size": args.batch_size
    }
    
    analyzer.run_analysis(args.messages, **attack_params)

if __name__ == "__main__":
    main()
