#!/usr/bin/env python3
"""
TCP 소켓을 사용한 RRC 메시지 전송 테스트
srsRAN eNB와의 실제 연결 및 메시지 교환 테스트
"""

import socket
import time
import json
import os
import subprocess
import threading
from datetime import datetime
import struct
import random

class TCPMessageTester:
    """TCP 소켓을 사용한 메시지 전송 테스트 클래스"""
    
    def __init__(self, enb_ip='127.0.0.1', enb_port=2001):
        self.enb_ip = enb_ip
        self.enb_port = enb_port
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.test_results = []
    
    def check_tcp_connection(self):
        """TCP 연결 상태 확인"""
        print("=== TCP 연결 상태 확인 ===")
        
        try:
            # TCP 소켓 연결 테스트
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            # 연결 시도
            result = sock.connect_ex((self.enb_ip, self.enb_port))
            
            if result == 0:
                print(f"✅ TCP 연결 성공: {self.enb_ip}:{self.enb_port}")
                sock.close()
                return True
            else:
                print(f"❌ TCP 연결 실패: {result}")
                sock.close()
                return False
                
        except Exception as e:
            print(f"❌ TCP 연결 오류: {e}")
            return False
    
    def generate_rrc_message(self, message_type='reestablishment_request'):
        """RRC 메시지 생성"""
        if message_type == 'reestablishment_request':
            # RRC Connection Reestablishment Request 메시지
            message = bytearray()
            
            # RRC Message Type (1 byte)
            message.append(0x02)  # RRCConnectionReestablishmentRequest
            
            # C-RNTI (2 bytes)
            c_rnti = random.randint(1, 65535)
            message.extend(struct.pack('>H', c_rnti))
            
            # PCI (2 bytes)
            pci = random.randint(0, 503)
            message.extend(struct.pack('>H', pci))
            
            # ShortMAC-I (2 bytes)
            short_mac_i = random.randint(0, 65535)
            message.extend(struct.pack('>H', short_mac_i))
            
            return bytes(message)
        
        elif message_type == 'connection_request':
            # RRC Connection Request 메시지
            message = bytearray()
            
            # RRC Message Type (1 byte)
            message.append(0x01)  # RRCConnectionRequest
            
            # UE Identity (5 bytes - 40 bits)
            ue_id = random.randint(0, (1 << 40) - 1)
            message.extend(struct.pack('>Q', ue_id)[3:8])
            
            # Establishment Cause (3 bits)
            message.append(0x04)  # mo-Data
            
            return bytes(message)
        
        else:
            # 기본 메시지
            return b'\x00\x01\x02\x03\x04\x05\x06\x07'
    
    def send_tcp_message(self, message_type='reestablishment_request'):
        """TCP 소켓을 사용한 메시지 전송"""
        print(f"\n=== TCP 메시지 전송 ({message_type}) ===")
        
        try:
            # 메시지 생성
            message = self.generate_rrc_message(message_type)
            print(f"생성된 메시지: {message.hex()}")
            print(f"메시지 크기: {len(message)} bytes")
            
            # TCP 소켓 생성
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15.0)
            
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
                print("⏰ 응답 시간 초과 (15초)")
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
            print(f"❌ TCP 메시지 전송 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_multiple_messages(self, count=5):
        """여러 메시지 연속 전송 테스트"""
        print(f"\n=== 연속 메시지 전송 테스트 ({count}개) ===")
        
        results = []
        
        for i in range(count):
            print(f"\n--- 메시지 {i+1}/{count} ---")
            
            # 메시지 타입 번갈아가며 전송
            message_type = 'reestablishment_request' if i % 2 == 0 else 'connection_request'
            
            result = self.send_tcp_message(message_type)
            results.append(result)
            
            # 메시지 간 대기
            if i < count - 1:
                time.sleep(1)
        
        return results
    
    def monitor_srsran_logs(self):
        """srsRAN 로그 모니터링"""
        print("\n=== srsRAN 로그 모니터링 ===")
        
        log_files = [
            '/tmp/srsenb.log',
            '/tmp/srsue.log',
            '/tmp/srsepc.log',
            '/var/log/syslog'
        ]
        
        log_data = {}
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    # 파일 크기 확인
                    file_size = os.path.getsize(log_file)
                    
                    # 최근 로그 라인들
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        recent_lines = lines[-10:] if len(lines) > 10 else lines
                    
                    log_data[log_file] = {
                        'size_bytes': file_size,
                        'recent_lines': [line.strip() for line in recent_lines]
                    }
                    
                    print(f"✅ {log_file}: {file_size} bytes")
                    
                except Exception as e:
                    print(f"❌ {log_file} 읽기 오류: {e}")
            else:
                print(f"⚠️ {log_file} 파일이 없습니다.")
        
        return log_data
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("=== TCP 메시지 전송 종합 테스트 ===")
        print(f"대상: {self.enb_ip}:{self.enb_port}")
        print("=" * 50)
        
        # 1. TCP 연결 상태 확인
        connection_ok = self.check_tcp_connection()
        
        if not connection_ok:
            print("❌ TCP 연결 실패. 테스트를 중단합니다.")
            return []
        
        # 2. 로그 모니터링 시작
        print("\n=== 로그 모니터링 시작 ===")
        log_data_before = self.monitor_srsran_logs()
        
        # 3. 단일 메시지 전송
        print("\n=== 단일 메시지 전송 테스트 ===")
        
        # Reestablishment Request 테스트
        result1 = self.send_tcp_message('reestablishment_request')
        self.test_results.append(result1)
        
        time.sleep(2)
        
        # Connection Request 테스트
        result2 = self.send_tcp_message('connection_request')
        self.test_results.append(result2)
        
        # 4. 연속 메시지 전송 테스트
        print("\n=== 연속 메시지 전송 테스트 ===")
        continuous_results = self.test_multiple_messages(3)
        self.test_results.extend(continuous_results)
        
        # 5. 로그 모니터링 종료
        print("\n=== 로그 모니터링 종료 ===")
        log_data_after = self.monitor_srsran_logs()
        
        # 6. 결과 저장
        self.save_test_results(log_data_before, log_data_after)
        
        # 7. 결과 요약
        self.print_test_summary()
        
        return self.test_results
    
    def save_test_results(self, log_data_before, log_data_after):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.log_dir}/tcp_message_test_{timestamp}.json"
        
        test_data = {
            'test_info': {
                'target_ip': self.enb_ip,
                'target_port': self.enb_port,
                'protocol': 'TCP',
                'timestamp': datetime.now().isoformat()
            },
            'test_results': self.test_results,
            'log_data': {
                'before': log_data_before,
                'after': log_data_after
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 테스트 결과 저장: {result_file}")
    
    def print_test_summary(self):
        """테스트 결과 요약"""
        print("\n=== 테스트 결과 요약 ===")
        
        success_count = sum(1 for r in self.test_results if r['success'])
        total_count = len(self.test_results)
        response_count = sum(1 for r in self.test_results if r.get('response_hex'))
        
        print(f"총 테스트: {total_count}개")
        print(f"성공: {success_count}개")
        print(f"실패: {total_count - success_count}개")
        print(f"응답 수신: {response_count}개")
        
        for i, result in enumerate(self.test_results):
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

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='TCP RRC 메시지 전송 테스트')
    parser.add_argument('--enb-ip', default='127.0.0.1', help='eNB IP 주소')
    parser.add_argument('--enb-port', type=int, default=2001, help='eNB 포트')
    parser.add_argument('--message-type', choices=['connection_request', 'reestablishment_request'], 
                       default='reestablishment_request', help='메시지 타입')
    parser.add_argument('--comprehensive', action='store_true', help='종합 테스트 실행')
    parser.add_argument('--count', type=int, default=5, help='연속 메시지 수')
    
    args = parser.parse_args()
    
    tester = TCPMessageTester(args.enb_ip, args.enb_port)
    
    if args.comprehensive:
        # 종합 테스트
        tester.run_comprehensive_test()
    else:
        # 단일 메시지 테스트
        result = tester.send_tcp_message(args.message_type)
        print(f"\n결과: {result}")
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{tester.log_dir}/tcp_message_test_{timestamp}.json"
        
        test_data = {
            'test_info': {
                'target_ip': args.enb_ip,
                'target_port': args.enb_port,
                'protocol': 'TCP',
                'timestamp': datetime.now().isoformat()
            },
            'test_results': [result]
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 테스트 결과 저장: {result_file}")

if __name__ == "__main__":
    main()
