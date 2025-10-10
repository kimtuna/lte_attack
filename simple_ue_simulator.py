#!/usr/bin/env python3
"""
간단한 UE 시뮬레이터
실제 RRC 메시지를 보내는 UE 역할을 수행
"""

import zmq
import struct
import time
import random
import threading
from datetime import datetime

class SimpleUESimulator:
    def __init__(self, enb_port=2001):
        self.enb_port = enb_port
        self.context = zmq.Context()
        self.running = False
        self.ue_id = random.randint(1000, 9999)
        
    def create_rrc_connection_request(self):
        """RRC Connection Request 메시지 생성"""
        message = struct.pack('>H', 0x0001)  # Message Type
        message += struct.pack('>I', self.ue_id)  # UE Identity
        message += struct.pack('>H', 0x0001)  # Establishment Cause: Mobile originating call
        message += struct.pack('>H', 0x0000)  # Spare
        
        # 실제 UE가 보내는 추가 정보
        message += struct.pack('>Q', random.randint(1000000000000000, 9999999999999999))  # IMSI
        message += struct.pack('>I', random.randint(1, 1000000))  # TMSI
        message += struct.pack('>H', random.randint(1, 65535))  # LAI
        message += struct.pack('>B', 0x01)  # RRC State: IDLE
        message += struct.pack('>I', random.randint(1, 1000000))  # Cell ID
        message += struct.pack('>H', random.randint(1, 65535))  # Tracking Area Code
        
        return message
    
    def create_rrc_connection_setup_complete(self):
        """RRC Connection Setup Complete 메시지 생성"""
        message = struct.pack('>H', 0x0003)  # Message Type
        message += struct.pack('>I', self.ue_id)  # UE Identity
        message += struct.pack('>H', 0x0000)  # Spare
        
        # NAS 메시지 포함
        message += struct.pack('>H', 0x0041)  # NAS Message Type: Attach Request
        message += struct.pack('>I', random.randint(1, 1000000))  # NAS Transaction ID
        message += struct.pack('>B', 0x01)  # NAS Security Header
        message += struct.pack('>B', 0x00)  # NAS Spare
        
        return message
    
    def create_measurement_report(self):
        """RRC Measurement Report 메시지 생성"""
        message = struct.pack('>H', 0x0005)  # Message Type
        message += struct.pack('>I', self.ue_id)  # UE Identity
        
        # 측정값 포함
        for cell_id in range(5):  # 5개 셀 측정값
            message += struct.pack('>H', cell_id)  # Cell ID
            message += struct.pack('>B', random.randint(50, 120))  # RSRP (양수로 변경)
            message += struct.pack('>B', random.randint(0, 20))  # RSRQ (양수로 변경)
            message += struct.pack('>B', random.randint(0, 100))  # SINR
        
        return message
    
    def send_message(self, message, description):
        """메시지 전송"""
        try:
            socket = self.context.socket(zmq.PUSH)
            socket.connect(f"tcp://localhost:{self.enb_port}")
            socket.send(message, zmq.NOBLOCK)
            socket.close()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {description} 전송 ({len(message)} bytes)")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 전송 실패: {description} - {e}")
            return False
    
    def rrc_connection_cycle(self):
        """RRC 연결 사이클 시뮬레이션"""
        print(f"=== UE {self.ue_id} RRC 연결 사이클 시작 ===")
        
        while self.running:
            try:
                # 1단계: RRC Connection Request
                rrc_request = self.create_rrc_connection_request()
                self.send_message(rrc_request, f"RRC Connection Request (UE {self.ue_id})")
                time.sleep(0.1)
                
                # 2단계: RRC Connection Setup Complete
                rrc_setup_complete = self.create_rrc_connection_setup_complete()
                self.send_message(rrc_setup_complete, f"RRC Connection Setup Complete (UE {self.ue_id})")
                time.sleep(0.1)
                
                # 3단계: Measurement Report
                measurement_report = self.create_measurement_report()
                self.send_message(measurement_report, f"Measurement Report (UE {self.ue_id})")
                time.sleep(0.1)
                
                # 다음 사이클까지 대기
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                print(f"RRC 연결 사이클 오류: {e}")
                time.sleep(1)
    
    def start_ue(self):
        """UE 시작"""
        print(f"=== Simple UE Simulator 시작 ===")
        print(f"UE ID: {self.ue_id}")
        print(f"eNB 포트: {self.enb_port}")
        print("=" * 50)
        
        self.running = True
        
        # RRC 연결 사이클 스레드 시작
        thread = threading.Thread(target=self.rrc_connection_cycle)
        thread.daemon = True
        thread.start()
        
        try:
            # 사용자 입력 대기
            while True:
                command = input("\n명령어 (q: 종료, s: 상태, m: 측정보고): ").strip().lower()
                
                if command == 'q':
                    break
                elif command == 's':
                    print(f"UE ID: {self.ue_id}")
                    print(f"상태: 실행 중")
                elif command == 'm':
                    measurement_report = self.create_measurement_report()
                    self.send_message(measurement_report, f"Manual Measurement Report (UE {self.ue_id})")
                else:
                    print("알 수 없는 명령어")
                    
        except KeyboardInterrupt:
            pass
        
        self.stop_ue()
    
    def stop_ue(self):
        """UE 중지"""
        print("\n=== UE 중지 ===")
        self.running = False
        self.context.term()
        print("UE 시뮬레이터 종료")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple UE Simulator')
    parser.add_argument('--enb-port', type=int, default=2001, help='eNB 포트')
    parser.add_argument('--ue-id', type=int, help='UE ID (지정하지 않으면 랜덤)')
    
    args = parser.parse_args()
    
    ue = SimpleUESimulator(args.enb_port)
    if args.ue_id:
        ue.ue_id = args.ue_id
    
    ue.start_ue()

if __name__ == "__main__":
    main()
