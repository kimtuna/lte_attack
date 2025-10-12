#!/usr/bin/env python3
"""
Measurement Report 전송 스크립트
eNB에게 Measurement Report를 보내서 처리 부담을 증가시킴
"""

import zmq
import struct
import random
import time
import argparse

def create_measurement_report(ue_id=1001):
    """RRC Measurement Report 메시지 생성"""
    message = struct.pack('>H', 0x0005)  # Message Type: RRC Measurement Report
    message += struct.pack('>I', ue_id)  # UE Identity
    
    # srsRAN이 기대하는 실제 RRC 필드들
    message += struct.pack('>I', 0x12345678)  # RRC Transaction ID
    message += struct.pack('>H', 0x0000)       # Criticality
    message += struct.pack('>H', 0x0000)       # Spare
    
    # 다수의 측정값 포함 (스케줄링 알고리즘 부담 증가)
    for i in range(100):  # 100개 셀 측정값
        message += struct.pack('>H', random.randint(1, 65535))  # Cell ID
        message += struct.pack('>B', random.randint(50, 120))   # RSRP (양수로 변경)
        message += struct.pack('>B', random.randint(0, 20))     # RSRQ (양수로 변경)
        message += struct.pack('>B', random.randint(0, 100))    # SINR
    
    # 더 큰 페이로드 추가 (메모리 사용량 증가)
    large_payload = b'Y' * 3000  # 3KB 페이로드
    message += large_payload
    
    return message

def send_measurement_report(target_port=2001, count=1, interval=1.0):
    """Measurement Report 전송"""
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    
    try:
        socket.connect(f"tcp://localhost:{target_port}")
        print(f"eNB 포트 {target_port}에 연결됨")
        
        for i in range(count):
            message = create_measurement_report()
            socket.send(message, zmq.NOBLOCK)
            print(f"[{i+1}/{count}] Measurement Report 전송 완료 ({len(message)} bytes)")
            
            if i < count - 1:  # 마지막이 아니면 대기
                time.sleep(interval)
                
    except Exception as e:
        print(f"전송 오류: {e}")
    finally:
        socket.close()
        context.term()

def main():
    parser = argparse.ArgumentParser(description='Measurement Report 전송')
    parser.add_argument('--target-port', type=int, default=2001, help='eNB 포트 (기본값: 2001)')
    parser.add_argument('--count', type=int, default=1, help='전송 횟수 (기본값: 1)')
    parser.add_argument('--interval', type=float, default=1.0, help='전송 간격 초 (기본값: 1.0)')
    
    args = parser.parse_args()
    
    print("=== Measurement Report 전송 ===")
    print(f"대상 포트: {args.target_port}")
    print(f"전송 횟수: {args.count}")
    print(f"전송 간격: {args.interval}초")
    print("=" * 40)
    
    send_measurement_report(args.target_port, args.count, args.interval)

if __name__ == "__main__":
    main()
