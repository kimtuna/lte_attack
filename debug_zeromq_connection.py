#!/usr/bin/env python3
"""
ZeroMQ 연결 디버깅 스크립트
eNB와의 연결 상태를 확인
"""

import zmq
import struct
import time

def test_zeromq_connection():
    """ZeroMQ 연결 테스트"""
    context = zmq.Context()
    
    print("=== ZeroMQ 연결 테스트 ===")
    
    # 포트 2000 연결 테스트 (eNB 수신 포트)
    try:
        socket = context.socket(zmq.PUSH)
        print(f"포트 2000 연결 시도...")
        socket.connect("tcp://localhost:2000")
        
        # 간단한 테스트 메시지
        test_message = b"test"
        socket.send(test_message, zmq.NOBLOCK)
        print("포트 2000 연결 성공 및 메시지 전송")
        
        socket.close()
        
    except Exception as e:
        print(f"포트 2000 연결 실패: {e}")
    
    # 포트 2001 연결 테스트 (eNB 전송 포트)
    try:
        socket = context.socket(zmq.PULL)
        print(f"포트 2001 연결 시도...")
        socket.connect("tcp://localhost:2001")
        
        # 타임아웃 설정
        socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1초 타임아웃
        
        try:
            message = socket.recv(zmq.NOBLOCK)
            print(f"포트 2001에서 메시지 수신: {message}")
        except zmq.Again:
            print("포트 2001에서 메시지 없음 (정상)")
        
        socket.close()
        
    except Exception as e:
        print(f"포트 2001 연결 실패: {e}")
    
    context.term()
    print("=== 테스트 완료 ===")

def test_simple_message():
    """간단한 메시지 전송 테스트"""
    context = zmq.Context()
    
    print("\n=== 간단한 메시지 전송 테스트 ===")
    
    try:
        socket = context.socket(zmq.PUSH)
        socket.connect("tcp://localhost:2000")
        
        # RRC Connection Request 메시지
        message = struct.pack('>H', 0x0001)  # Message Type
        message += struct.pack('>I', 12345)  # UE Identity
        message += struct.pack('>H', 0x0001)  # Establishment Cause
        message += struct.pack('>H', 0x0000)  # Spare
        
        print(f"메시지 전송: {message.hex()}")
        socket.send(message, zmq.NOBLOCK)
        print("메시지 전송 완료")
        
        socket.close()
        
    except Exception as e:
        print(f"메시지 전송 실패: {e}")
    
    context.term()

if __name__ == "__main__":
    test_zeromq_connection()
    test_simple_message()
