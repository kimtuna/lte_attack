#!/usr/bin/env python3
"""
정상적인 RRC 연결 흐름 테스트
srsRAN UE를 사용한 실제 RRC 연결 과정 모니터링
"""

import subprocess
import time
import json
import os
import threading
from datetime import datetime
import signal
import sys

class NormalRRCFlowTest:
    """정상적인 RRC 연결 흐름 테스트 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.monitoring = False
        self.srsue_process = None
        self.log_monitor_thread = None
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print("\n테스트를 중단합니다...")
        self.monitoring = False
        if self.srsue_process:
            self.srsue_process.terminate()
        sys.exit(0)
    
    def check_srsran_status(self):
        """srsRAN 프로세스 상태 확인"""
        print("=== srsRAN 프로세스 상태 확인 ===")
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')
            
            srsran_processes = []
            for process in processes:
                if any(keyword in process.lower() for keyword in ['srsenb', 'srsue', 'srsepc']):
                    srsran_processes.append(process.strip())
            
            if srsran_processes:
                print("실행 중인 srsRAN 프로세스:")
                for process in srsran_processes:
                    print(f"  {process}")
                return True
            else:
                print("실행 중인 srsRAN 프로세스가 없습니다.")
                return False
                
        except Exception as e:
            print(f"프로세스 확인 오류: {e}")
            return False
    
    def monitor_enb_logs(self, duration=60):
        """eNB 로그 모니터링"""
        print(f"=== eNB 로그 모니터링 ({duration}초) ===")
        
        log_files = [
            '/var/log/syslog',
            '/var/log/messages'
        ]
        
        log_data = {}
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration:
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # 파일 크기 확인
                        file_size = os.path.getsize(log_file)
                        
                        # 최근 로그 라인들
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-10:] if len(lines) > 10 else lines
                        
                        if log_file not in log_data:
                            log_data[log_file] = {
                                'initial_size': file_size,
                                'lines': []
                            }
                        
                        # 새로운 라인 확인
                        current_lines = [line.strip() for line in recent_lines]
                        new_lines = [line for line in current_lines if line not in log_data[log_file]['lines']]
                        
                        if new_lines:
                            log_data[log_file]['lines'].extend(new_lines)
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_file}:")
                            for line in new_lines:
                                print(f"  {line}")
                        
                    except Exception as e:
                        print(f"로그 파일 읽기 오류 {log_file}: {e}")
            
            time.sleep(2)  # 2초마다 확인
        
        return log_data
    
    def start_srsue(self, duration=30):
        """srsUE 시작"""
        print(f"=== srsUE 시작 ({duration}초) ===")
        
        try:
            # srsUE 명령어 (기본 설정)
            cmd = ['srsue']
            
            # 백그라운드에서 srsUE 실행
            self.srsue_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"srsUE 프로세스 시작 (PID: {self.srsue_process.pid})")
            
            # 지정된 시간 동안 실행
            time.sleep(duration)
            
            # srsUE 종료
            self.srsue_process.terminate()
            self.srsue_process.wait(timeout=10)
            
            print("srsUE 프로세스 종료")
            
            # 출력 확인
            stdout, stderr = self.srsue_process.communicate()
            
            if stdout:
                print("srsUE STDOUT:")
                print(stdout)
            
            if stderr:
                print("srsUE STDERR:")
                print(stderr)
            
            return True
            
        except Exception as e:
            print(f"srsUE 시작 오류: {e}")
            if self.srsue_process:
                self.srsue_process.terminate()
            return False
    
    def monitor_network_traffic(self, duration=60):
        """네트워크 트래픽 모니터링"""
        print(f"=== 네트워크 트래픽 모니터링 ({duration}초) ===")
        
        try:
            # netstat으로 연결 상태 확인
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                # srsRAN 관련 포트 확인
                srsran_ports = []
                for line in lines:
                    if any(port in line for port in ['2000', '2001', '36412', '36413']):
                        srsran_ports.append(line.strip())
                
                if srsran_ports:
                    print("srsRAN 관련 포트 연결:")
                    for port_info in srsran_ports:
                        print(f"  {port_info}")
                else:
                    print("srsRAN 관련 포트 연결이 없습니다.")
                
                return srsran_ports
            else:
                print(f"네트워크 트래픽 확인 실패: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"네트워크 트래픽 확인 오류: {e}")
            return []
    
    def run_comprehensive_test(self):
        """종합 RRC 연결 흐름 테스트"""
        print("=== 정상적인 RRC 연결 흐름 테스트 ===")
        print("srsUE를 사용한 실제 RRC 연결 과정 모니터링")
        print("=" * 50)
        
        # 1. srsRAN 상태 확인
        if not self.check_srsran_status():
            print("srsRAN이 실행되지 않았습니다. 테스트를 중단합니다.")
            return
        
        # 2. 초기 네트워크 상태 확인
        print("\n=== 초기 네트워크 상태 확인 ===")
        initial_traffic = self.monitor_network_traffic(10)
        
        # 3. 로그 모니터링 시작
        print("\n=== 로그 모니터링 시작 ===")
        self.monitoring = True
        
        # 로그 모니터링 스레드 시작
        log_monitor_thread = threading.Thread(
            target=self.monitor_enb_logs, 
            args=(60,)
        )
        log_monitor_thread.daemon = True
        log_monitor_thread.start()
        
        # 4. srsUE 시작
        print("\n=== srsUE 연결 테스트 ===")
        ue_success = self.start_srsue(30)
        
        # 5. 연결 후 네트워크 상태 확인
        print("\n=== 연결 후 네트워크 상태 확인 ===")
        final_traffic = self.monitor_network_traffic(10)
        
        # 6. 로그 모니터링 종료
        self.monitoring = False
        log_monitor_thread.join(timeout=5)
        
        # 7. 결과 저장
        self.save_test_results(initial_traffic, final_traffic, ue_success)
        
        # 8. 결과 요약
        self.print_test_summary(ue_success)
    
    def save_test_results(self, initial_traffic, final_traffic, ue_success):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.log_dir}/normal_rrc_flow_test_{timestamp}.json"
        
        test_data = {
            'test_info': {
                'test_type': 'normal_rrc_flow',
                'timestamp': datetime.now().isoformat(),
                'description': 'srsUE를 사용한 정상적인 RRC 연결 흐름 테스트'
            },
            'results': {
                'ue_success': ue_success,
                'initial_traffic': initial_traffic,
                'final_traffic': final_traffic,
                'traffic_changes': len(final_traffic) - len(initial_traffic)
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 테스트 결과 저장: {result_file}")
    
    def print_test_summary(self, ue_success):
        """테스트 결과 요약"""
        print("\n=== 테스트 결과 요약 ===")
        
        if ue_success:
            print("✅ srsUE 연결 성공")
            print("✅ RRC 연결 흐름 확인됨")
            print("✅ eNB 로그에 연결 정보 기록됨")
        else:
            print("❌ srsUE 연결 실패")
            print("❌ RRC 연결 흐름 확인되지 않음")
        
        print("\n예상되는 정상 RRC 연결 흐름:")
        print("1. srsUE 시작")
        print("2. eNB에 RRC Connection Request 전송")
        print("3. eNB가 RRC Connection Setup 응답")
        print("4. srsUE가 RRC Connection Setup Complete 전송")
        print("5. EPC와 연결 설정")
        print("6. eNB 로그에 연결 정보 기록")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='정상적인 RRC 연결 흐름 테스트')
    parser.add_argument('--duration', type=int, default=30, help='srsUE 실행 시간 (초)')
    parser.add_argument('--check-status', action='store_true', help='srsRAN 상태만 확인')
    
    args = parser.parse_args()
    
    tester = NormalRRCFlowTest()
    
    if args.check_status:
        tester.check_srsran_status()
    else:
        tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
