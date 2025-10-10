#!/usr/bin/env python3
"""
캡처된 패킷 내용 분석 스크립트
"""

import subprocess
import time
import sys

def analyze_packet_content():
    """패킷 내용 분석"""
    print("=== 패킷 내용 분석 ===")
    
    # 10초간 패킷 캡처
    cmd = [
        "sudo", "tshark",
        "-i", "any",
        "-f", "port 2000 or port 2001",
        "-Y", "frame.len > 50",
        "-T", "fields",
        "-e", "frame.time",
        "-e", "frame.len",
        "-e", "data"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split('\n')
        
        print(f"캡처된 패킷 수: {len(lines)}")
        print("\n패킷 분석:")
        
        for i, line in enumerate(lines[:10], 1):  # 처음 10개만 분석
            parts = line.split('\t')
            if len(parts) >= 3:
                timestamp = parts[0]
                length = parts[1]
                data = parts[2] if len(parts) > 2 else ""
                
                print(f"\n패킷 {i}:")
                print(f"  시간: {timestamp}")
                print(f"  크기: {length} bytes")
                print(f"  데이터: {data[:32]}...")
                
                # 메시지 타입 분석
                if data:
                    try:
                        first_byte = int(data[:2], 16) if len(data) >= 2 else 0
                        second_byte = int(data[2:4], 16) if len(data) >= 4 else 0
                        
                        print(f"  첫 바이트: 0x{first_byte:02x}")
                        print(f"  둘째 바이트: 0x{second_byte:02x}")
                        
                        # 메시지 타입 추정
                        if first_byte == 0x00 and second_byte == 0x01:
                            print("  → RRC Connection Request")
                        elif first_byte == 0x00 and second_byte == 0x02:
                            print("  → RRC Connection Setup")
                        elif first_byte == 0x00 and second_byte == 0x03:
                            print("  → RRC Connection Setup Complete")
                        elif first_byte == 0x41:
                            print("  → NAS Attach Request")
                        elif first_byte == 0x48:
                            print("  → NAS TAU Request")
                        elif first_byte == 0x45:
                            print("  → NAS Detach Request")
                        else:
                            print("  → 알 수 없는 메시지 타입")
                            
                    except ValueError:
                        print("  → 데이터 파싱 오류")
                        
    except subprocess.TimeoutExpired:
        print("10초 후 자동 종료")
    except Exception as e:
        print(f"분석 오류: {e}")

def check_specific_messages():
    """특정 메시지 타입 확인"""
    print("\n=== 특정 메시지 타입 확인 ===")
    
    message_types = {
        "RRC Connection Request": "udp contains 0x0001",
        "RRC Connection Setup": "udp contains 0x0002", 
        "RRC Connection Setup Complete": "udp contains 0x0003",
        "RRC Connection Reject": "udp contains 0x0004",
        "NAS Attach Request": "udp contains 0x41",
        "NAS TAU Request": "udp contains 0x48",
        "NAS Detach Request": "udp contains 0x45"
    }
    
    for msg_name, filter_expr in message_types.items():
        cmd = [
            "sudo", "tshark",
            "-i", "any",
            "-f", "port 2000 or port 2001",
            "-Y", filter_expr,
            "-T", "fields",
            "-e", "frame.time"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            print(f"{msg_name}: {count}개")
        except:
            print(f"{msg_name}: 확인 실패")

if __name__ == "__main__":
    analyze_packet_content()
    check_specific_messages()
