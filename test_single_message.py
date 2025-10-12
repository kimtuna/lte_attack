#!/usr/bin/env python3
"""
단일 RRC 메시지 전송 테스트
eNB 연결 상태 확인 및 메시지 전송/응답 모니터링
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

class SingleMessageTester:
    """단일 메시지 전송 테스트 클래스"""
    
    def __init__(self, enb_ip='127.0.0.1', enb_port=2000):
        self.enb_ip = enb_ip
        self.enb_port = enb_port
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.test_results = []
        self.log_monitoring = False
    
    def check_enb_connection(self):
        """eNB 연결 상태 확인"""
        print("=== eNB 연결 상태 확인 ===")
        
        try:
            # 소켓 연결 테스트
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5.0)
            
            # 연결 테스트 (빈 메시지 전송)
            test_message = b'\x00'
            sock.sendto(test_message, (self.enb_ip, self.enb_port))
            
            print(f"✅ 소켓 연결 성공: {self.enb_ip}:{self.enb_port}")
            sock.close()
            return True
            
        except Exception as e:
            print(f"❌ 소켓 연결 실패: {e}")
            return False
    
    def check_srsran_processes(self):
        """srsRAN 프로세스 확인"""
        print("\n=== srsRAN 프로세스 확인 ===")
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                srsran_processes = []
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['srsenb', 'srsue', 'srsepc']):
                        srsran_processes.append(line.strip())
                
                if srsran_processes:
                    print("✅ 실행 중인 srsRAN 프로세스:")
                    for process in srsran_processes:
                        print(f"  {process}")
                    return True
                else:
                    print("❌ 실행 중인 srsRAN 프로세스가 없습니다.")
                    return False
            else:
                print(f"❌ 프로세스 확인 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 프로세스 확인 오류: {e}")
            return False
    
    def check_ports(self):
        """포트 사용 현황 확인"""
        print("\n=== 포트 사용 현황 확인 ===")
        
        try:
            result = subprocess.run(['netstat', '-tulpn'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                target_ports = []
                for line in lines:
                    if f':{self.enb_port}' in line or ':2001' in line:
                        target_ports.append(line.strip())
                
                if target_ports:
                    print(f"✅ 포트 {self.enb_port} 사용 중:")
                    for port_info in target_ports:
                        print(f"  {port_info}")
                    return True
                else:
                    print(f"❌ 포트 {self.enb_port}가 사용되지 않습니다.")
                    return False
            else:
                print(f"❌ 포트 확인 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 포트 확인 오류: {e}")
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
    
    def send_single_message(self, message_type='reestablishment_request'):
        """단일 메시지 전송"""
        print(f"\n=== 단일 메시지 전송 ({message_type}) ===")
        
        try:
            # 메시지 생성
            message = self.generate_rrc_message(message_type)
            print(f"생성된 메시지: {message.hex()}")
            print(f"메시지 크기: {len(message)} bytes")
            
            # 소켓 생성
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10.0)
            
            # 메시지 전송
            start_time = time.time()
            bytes_sent = sock.sendto(message, (self.enb_ip, self.enb_port))
            send_time = time.time() - start_time
            
            print(f"✅ 메시지 전송 성공: {bytes_sent} bytes")
            print(f"전송 시간: {send_time:.6f}초")
            
            # 응답 대기 (선택적)
            try:
                response, addr = sock.recvfrom(1024)
                response_time = time.time() - start_time
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
    
    def monitor_srsran_logs(self, duration=30):
        """srsRAN 로그 모니터링"""
        print(f"\n=== srsRAN 로그 모니터링 ({duration}초) ===")
        
        log_files = [
            '/tmp/srsenb.log',
            '/tmp/srsue.log',
            '/tmp/srsepc.log'
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
                        recent_lines = lines[-20:] if len(lines) > 20 else lines
                    
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
        print("=== 단일 메시지 전송 종합 테스트 ===")
        print(f"대상: {self.enb_ip}:{self.enb_port}")
        print("=" * 50)
        
        # 1. eNB 연결 상태 확인
        connection_ok = self.check_enb_connection()
        
        # 2. srsRAN 프로세스 확인
        processes_ok = self.check_srsran_processes()
        
        # 3. 포트 사용 현황 확인
        ports_ok = self.check_ports()
        
        # 4. 로그 모니터링 시작
        print("\n=== 로그 모니터링 시작 ===")
        log_data_before = self.monitor_srsran_logs()
        
        # 5. 단일 메시지 전송
        print("\n=== 메시지 전송 테스트 ===")
        
        # Reestablishment Request 테스트
        result1 = self.send_single_message('reestablishment_request')
        self.test_results.append(result1)
        
        time.sleep(2)
        
        # Connection Request 테스트
        result2 = self.send_single_message('connection_request')
        self.test_results.append(result2)
        
        # 6. 로그 모니터링 종료
        print("\n=== 로그 모니터링 종료 ===")
        log_data_after = self.monitor_srsran_logs()
        
        # 7. 결과 저장
        self.save_test_results(log_data_before, log_data_after)
        
        # 8. 결과 요약
        self.print_test_summary()
        
        return self.test_results
    
    def save_test_results(self, log_data_before, log_data_after):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.log_dir}/single_message_test_{timestamp}.json"
        
        test_data = {
            'test_info': {
                'target_ip': self.enb_ip,
                'target_port': self.enb_port,
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
        
        print(f"총 테스트: {total_count}개")
        print(f"성공: {success_count}개")
        print(f"실패: {total_count - success_count}개")
        
        for i, result in enumerate(self.test_results):
            if result['success']:
                print(f"\n테스트 {i+1}: {result['message_type']}")
                print(f"  메시지 크기: {result['message_size']} bytes")
                print(f"  전송 시간: {result['send_time']:.6f}초")
                if result.get('response_hex'):
                    print(f"  응답 크기: {result['response_size']} bytes")
                    print(f"  응답 시간: {result['response_time']:.6f}초")
                else:
                    print("  응답: 없음 (시간 초과)")
            else:
                print(f"\n테스트 {i+1}: 실패")
                print(f"  오류: {result['error']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='단일 RRC 메시지 전송 테스트')
    parser.add_argument('--enb-ip', default='127.0.0.1', help='eNB IP 주소')
    parser.add_argument('--enb-port', type=int, default=2000, help='eNB 포트')
    parser.add_argument('--message-type', choices=['connection_request', 'reestablishment_request'], 
                       default='reestablishment_request', help='메시지 타입')
    
    args = parser.parse_args()
    
    tester = SingleMessageTester(args.enb_ip, args.enb_port)
    
    if args.message_type:
        # 단일 메시지 테스트
        result = tester.send_single_message(args.message_type)
        print(f"\n결과: {result}")
    else:
        # 종합 테스트
        tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
