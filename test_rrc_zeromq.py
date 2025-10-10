#!/usr/bin/env python3
"""
ZeroMQ를 통한 RRC Connection Request 테스트 스크립트
srsRAN eNB에 RRC 메시지를 전송하고 응답을 확인
"""

import zmq
import struct
import time
import threading
from datetime import datetime

class RRCZeroMQTester:
    def __init__(self, tx_port=2001, rx_port=2000):
        self.tx_port = tx_port
        self.rx_port = rx_port
        self.context = zmq.Context()
        self.running = False
        
    def create_rrc_connection_request(self, ue_id=12345):
        """RRC Connection Request 메시지 생성"""
        # 간단한 RRC Connection Request 구조
        message = struct.pack('>H', 0x0001)  # Message Type: RRC Connection Request
        message += struct.pack('>I', ue_id)  # UE Identity
        message += struct.pack('>H', 0x0000)  # Establishment Cause: Emergency
        message += struct.pack('>H', 0x0000)  # Spare
        return message
    
    def create_rrc_connection_setup_complete(self, ue_id=12345):
        """RRC Connection Setup Complete 메시지 생성"""
        message = struct.pack('>H', 0x0003)  # Message Type: RRC Connection Setup Complete
        message += struct.pack('>I', ue_id)  # UE Identity
        message += struct.pack('>H', 0x0000)  # Spare
        return message
    
    def send_rrc_message(self, message, message_type="Unknown"):
        """RRC 메시지 전송"""
        try:
            # PUSH 소켓으로 메시지 전송 (포트 2000으로 CONNECT)
            tx_socket = self.context.socket(zmq.PUSH)
            tx_socket.connect(f"tcp://localhost:{self.tx_port}")  # 포트 2000으로 연결
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message_type} 전송")
            print(f"  메시지 크기: {len(message)} bytes")
            print(f"  데이터: {message.hex()}")
            
            tx_socket.send(message, zmq.NOBLOCK)
            tx_socket.close()
            
            return True
            
        except Exception as e:
            print(f"메시지 전송 오류: {e}")
            return False
    
    def monitor_responses(self):
        """응답 메시지 모니터링"""
        try:
            # PULL 소켓으로 응답 수신 (다른 포트 사용)
            rx_socket = self.context.socket(zmq.PULL)
            rx_socket.bind(f"tcp://*:{self.rx_port + 100}")  # 포트 충돌 방지
            
            print(f"응답 모니터링 시작 (포트 {self.rx_port})")
            
            while self.running:
                try:
                    # 응답 메시지 수신
                    response = rx_socket.recv(zmq.NOBLOCK)
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"[{timestamp}] 응답 수신: {len(response)} bytes")
                    print(f"  데이터: {response.hex()}")
                    
                    # 메시지 타입 분석
                    if len(response) >= 2:
                        msg_type = struct.unpack('>H', response[:2])[0]
                        if msg_type == 0x0002:
                            print("  → RRC Connection Setup")
                        elif msg_type == 0x0004:
                            print("  → RRC Connection Reject")
                        elif msg_type == 0x0005:
                            print("  → RRC Connection Release")
                        else:
                            print(f"  → 알 수 없는 메시지 타입: 0x{msg_type:04x}")
                    
                    print("-" * 50)
                    
                except zmq.Again:
                    pass
                except Exception as e:
                    print(f"응답 수신 오류: {e}")
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"응답 모니터링 설정 오류: {e}")
    
    def run_test_sequence(self, duration=60):
        """테스트 시퀀스 실행"""
        print(f"=== RRC ZeroMQ 테스트 시작 ===")
        print(f"TX 포트: {self.tx_port}, RX 포트: {self.rx_port}")
        print(f"테스트 지속 시간: {duration}초")
        print("=" * 50)
        
        self.running = True
        
        # 응답 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self.monitor_responses)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 테스트 메시지 전송
        test_count = 0
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            test_count += 1
            
            # RRC Connection Request 전송
            rrc_request = self.create_rrc_connection_request(ue_id=1000 + test_count)
            self.send_rrc_message(rrc_request, f"RRC Connection Request #{test_count}")
            
            time.sleep(2)  # 2초 대기
            
            # RRC Connection Setup Complete 전송 (선택적)
            if test_count % 3 == 0:  # 3번마다 한 번씩
                rrc_complete = self.create_rrc_connection_setup_complete(ue_id=1000 + test_count)
                self.send_rrc_message(rrc_complete, f"RRC Connection Setup Complete #{test_count}")
            
            time.sleep(3)  # 3초 대기
        
        self.running = False
        print(f"\n테스트 완료: 총 {test_count}개 메시지 전송")
        
        # ZeroMQ 정리
        self.context.term()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RRC ZeroMQ 테스트')
    parser.add_argument('--tx-port', type=int, default=2001, help='TX 포트')
    parser.add_argument('--rx-port', type=int, default=2000, help='RX 포트')
    parser.add_argument('--duration', type=int, default=60, help='테스트 지속 시간 (초)')
    
    args = parser.parse_args()
    
    tester = RRCZeroMQTester(args.tx_port, args.rx_port)
    
    try:
        tester.run_test_sequence(args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        tester.running = False

if __name__ == "__main__":
    main()
