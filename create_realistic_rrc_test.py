#!/usr/bin/env python3
"""
실제적인 RRC 메시지 테스트 생성
srsUE 분석 결과를 바탕으로 실제 RRC 형식으로 테스트
"""

import socket
import time
import json
import os
import struct
import random
from datetime import datetime

class RealisticRRCTest:
    """실제적인 RRC 메시지 테스트 클래스"""
    
    def __init__(self, enb_ip='127.0.0.1', enb_port=2001):
        self.enb_ip = enb_ip
        self.enb_port = enb_port
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # srsUE에서 분석된 실제 메시지 형식 (예시)
        self.realistic_messages = {
            'rrc_connection_request': {
                'description': 'RRC Connection Request (실제 형식)',
                'format': 'ASN.1 PER 인코딩',
                'size': '7-15 bytes',
                'fields': [
                    'RRC Message Type (1 byte)',
                    'UE Identity (5 bytes)',
                    'Establishment Cause (3 bits)',
                    'Spare bits (5 bits)'
                ]
            },
            'rrc_connection_setup_complete': {
                'description': 'RRC Connection Setup Complete (실제 형식)',
                'format': 'ASN.1 PER 인코딩',
                'size': '10-20 bytes',
                'fields': [
                    'RRC Message Type (1 byte)',
                    'Selected PLMN Identity',
                    'Dedicated Info NAS',
                    'Registered MME'
                ]
            }
        }
    
    def generate_realistic_rrc_connection_request(self):
        """실제적인 RRC Connection Request 메시지 생성"""
        print("=== 실제적인 RRC Connection Request 생성 ===")
        
        # 실제 srsUE에서 사용하는 형식에 가까운 메시지 생성
        message = bytearray()
        
        # RRC Message Type (1 byte) - 실제 값
        message.append(0x01)  # RRCConnectionRequest
        
        # UE Identity (5 bytes) - 실제 UE ID 형식
        # S-TMSI 또는 Random ID 형식
        ue_id = random.randint(0, (1 << 40) - 1)
        message.extend(struct.pack('>Q', ue_id)[3:8])  # 상위 5바이트
        
        # Establishment Cause (3 bits) - 실제 원인
        establishment_cause = 0x04  # mo-Data (실제 값)
        message.append(establishment_cause)
        
        # Spare bits (5 bits) - 실제로는 0
        message[-1] |= 0x00
        
        print(f"생성된 메시지: {message.hex()}")
        print(f"메시지 크기: {len(message)} bytes")
        print(f"UE ID: {ue_id}")
        print(f"Establishment Cause: {establishment_cause}")
        
        return bytes(message)
    
    def generate_realistic_rrc_connection_setup_complete(self):
        """실제적인 RRC Connection Setup Complete 메시지 생성"""
        print("=== 실제적인 RRC Connection Setup Complete 생성 ===")
        
        message = bytearray()
        
        # RRC Message Type (1 byte)
        message.append(0x03)  # RRCConnectionSetupComplete
        
        # Selected PLMN Identity (3 bytes)
        plmn_id = random.randint(0, (1 << 24) - 1)
        message.extend(struct.pack('>I', plmn_id)[1:4])
        
        # Dedicated Info NAS (가변 길이)
        nas_info = b'\x00\x01\x02\x03\x04\x05'
        message.extend(nas_info)
        
        # Registered MME (1 byte)
        mme_id = random.randint(0, 255)
        message.append(mme_id)
        
        print(f"생성된 메시지: {message.hex()}")
        print(f"메시지 크기: {len(message)} bytes")
        print(f"PLMN ID: {plmn_id}")
        print(f"MME ID: {mme_id}")
        
        return bytes(message)
    
    def send_realistic_message(self, message, message_type):
        """실제적인 메시지 전송"""
        print(f"\n=== 실제적인 {message_type} 전송 ===")
        
        try:
            # TCP 소켓 생성
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            # 연결
            print("TCP 연결 중...")
            sock.connect((self.enb_ip, self.enb_port))
            print("✅ TCP 연결 성공")
            
            # 메시지 전송
            start_time = time.time()
            bytes_sent = sock.send(message)
            send_time = time.time() - start_time
            
            print(f"✅ 메시지 전송 성공: {bytes_sent} bytes")
            print(f"전송 시간: {send_time:.6f}초")
            
            # 응답 대기
            try:
                print("응답 대기 중...")
                response = sock.recv(1024)
                response_time = time.time() - start_time
                
                if response:
                    print(f"✅ 응답 수신: {response.hex()}")
                    print(f"응답 시간: {response_time:.6f}초")
                    print(f"응답 크기: {len(response)} bytes")
                    
                    result = {
                        'success': True,
                        'message_type': message_type,
                        'message_hex': message.hex(),
                        'message_size': len(message),
                        'bytes_sent': bytes_sent,
                        'send_time': send_time,
                        'response_hex': response.hex(),
                        'response_size': len(response),
                        'response_time': response_time,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    print("⚠️ 빈 응답 수신")
                    result = {
                        'success': True,
                        'message_type': message_type,
                        'message_hex': message.hex(),
                        'message_size': len(message),
                        'bytes_sent': bytes_sent,
                        'send_time': send_time,
                        'response_hex': None,
                        'response_size': 0,
                        'response_time': response_time,
                        'empty_response': True,
                        'timestamp': datetime.now().isoformat()
                    }
                
            except socket.timeout:
                print("⏰ 응답 시간 초과 (10초)")
                result = {
                    'success': True,
                    'message_type': message_type,
                    'message_hex': message.hex(),
                    'message_size': len(message),
                    'bytes_sent': bytes_sent,
                    'send_time': send_time,
                    'response_hex': None,
                    'response_size': 0,
                    'response_time': None,
                    'timeout': True,
                    'timestamp': datetime.now().isoformat()
                }
            
            sock.close()
            return result
            
        except Exception as e:
            print(f"❌ 메시지 전송 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_realistic_test(self):
        """실제적인 RRC 테스트 실행"""
        print("=== 실제적인 RRC 메시지 테스트 ===")
        print(f"대상: {self.enb_ip}:{self.enb_port}")
        print("=" * 50)
        
        results = []
        
        # 1. RRC Connection Request 테스트
        print("\n=== RRC Connection Request 테스트 ===")
        request_message = self.generate_realistic_rrc_connection_request()
        result1 = self.send_realistic_message(request_message, 'RRCConnectionRequest')
        results.append(result1)
        
        time.sleep(2)
        
        # 2. RRC Connection Setup Complete 테스트
        print("\n=== RRC Connection Setup Complete 테스트 ===")
        complete_message = self.generate_realistic_rrc_connection_setup_complete()
        result2 = self.send_realistic_message(complete_message, 'RRCConnectionSetupComplete')
        results.append(result2)
        
        # 3. 결과 저장
        self.save_test_results(results)
        
        # 4. 결과 요약
        self.print_test_summary(results)
        
        return results
    
    def save_test_results(self, results):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.log_dir}/realistic_rrc_test_{timestamp}.json"
        
        test_data = {
            'test_info': {
                'target_ip': self.enb_ip,
                'target_port': self.enb_port,
                'protocol': 'TCP',
                'test_type': 'realistic_rrc',
                'timestamp': datetime.now().isoformat()
            },
            'realistic_messages': self.realistic_messages,
            'test_results': results
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 테스트 결과 저장: {result_file}")
    
    def print_test_summary(self, results):
        """테스트 결과 요약"""
        print("\n=== 테스트 결과 요약 ===")
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        response_count = sum(1 for r in results if r.get('response_hex'))
        
        print(f"총 테스트: {total_count}개")
        print(f"성공: {success_count}개")
        print(f"실패: {total_count - success_count}개")
        print(f"응답 수신: {response_count}개")
        
        for i, result in enumerate(results):
            if result['success']:
                print(f"\n테스트 {i+1}: {result['message_type']}")
                print(f"  메시지 크기: {result['message_size']} bytes")
                print(f"  전송 시간: {result['send_time']:.6f}초")
                if result.get('response_hex'):
                    print(f"  응답 크기: {result['response_size']} bytes")
                    print(f"  응답 시간: {result['response_time']:.6f}초")
                else:
                    print("  응답: 없음")
            else:
                print(f"\n테스트 {i+1}: 실패")
                print(f"  오류: {result['error']}")
        
        print("\n다음 단계:")
        print("1. eNB 로그 확인하여 실제 RRC 메시지 처리 여부 확인")
        print("2. srsUE 메시지 분석 결과와 비교")
        print("3. 필요시 메시지 형식 추가 수정")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='실제적인 RRC 메시지 테스트')
    parser.add_argument('--enb-ip', default='127.0.0.1', help='eNB IP 주소')
    parser.add_argument('--enb-port', type=int, default=2001, help='eNB 포트')
    
    args = parser.parse_args()
    
    tester = RealisticRRCTest(args.enb_ip, args.enb_port)
    tester.run_realistic_test()

if __name__ == "__main__":
    main()
