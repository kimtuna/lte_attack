#!/usr/bin/env python3
"""
RRC Flooding Attack 테스트 스크립트
srsRAN 환경에서 flooding 공격 효과 테스트
"""

import subprocess
import time
import json
import os
from datetime import datetime

class RRCFloodingTest:
    """RRC Flooding Attack 테스트 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def check_srsran_status(self):
        """srsRAN 프로세스 상태 확인"""
        print("=== srsRAN 프로세스 상태 확인 ===")
        
        try:
            # srsRAN 관련 프로세스 확인
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
    
    def monitor_system_resources(self, duration=60):
        """시스템 리소스 모니터링"""
        print(f"=== 시스템 리소스 모니터링 ({duration}초) ===")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        monitor_file = f"{self.log_dir}/system_monitor_{timestamp}.log"
        
        try:
            # top 명령어로 CPU/메모리 사용률 모니터링
            cmd = ['top', '-l', str(duration), '-n', '10', '-s', '1']
            
            with open(monitor_file, 'w') as f:
                process = subprocess.Popen(cmd, stdout=f, stderr=subprocess.PIPE)
                process.wait()
            
            print(f"시스템 모니터링 로그 저장: {monitor_file}")
            return monitor_file
            
        except Exception as e:
            print(f"시스템 모니터링 오류: {e}")
            return None
    
    def run_flooding_test(self, test_config):
        """Flooding 테스트 실행"""
        print("=== RRC Flooding Attack 테스트 실행 ===")
        
        # 테스트 설정 출력
        print(f"테스트 설정:")
        for key, value in test_config.items():
            print(f"  {key}: {value}")
        print()
        
        # 시스템 모니터링 시작 (백그라운드)
        monitor_file = self.monitor_system_resources(test_config['duration'] + 10)
        
        # Flooding 공격 실행
        cmd = [
            'python3', 'rrc_flooding_attack.py',
            '--enb-ip', test_config['enb_ip'],
            '--enb-port', str(test_config['enb_port']),
            '--threads', str(test_config['threads']),
            '--duration', str(test_config['duration']),
            '--message-type', test_config['message_type']
        ]
        
        print(f"실행 명령: {' '.join(cmd)}")
        print("Flooding 공격 시작...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=test_config['duration'] + 30)
            
            print("=== Flooding 공격 결과 ===")
            print("STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("테스트 시간 초과")
            return False
        except Exception as e:
            print(f"테스트 실행 오류: {e}")
            return False
    
    def analyze_test_results(self, test_config):
        """테스트 결과 분석"""
        print("=== 테스트 결과 분석 ===")
        
        # 최근 로그 파일 찾기
        log_files = [f for f in os.listdir(self.log_dir) if f.startswith('flooding_attack_')]
        if not log_files:
            print("분석할 로그 파일이 없습니다.")
            return
        
        latest_log = sorted(log_files)[-1]
        log_path = os.path.join(self.log_dir, latest_log)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            print(f"분석 파일: {log_path}")
            print(f"총 전송 메시지: {log_data['results']['total_messages']}")
            print(f"초당 메시지 수: {log_data['results']['messages_per_second']:.2f}")
            print(f"오류 수: {log_data['results']['errors']}")
            
            # 성공률 계산
            success_rate = (log_data['results']['total_messages'] - log_data['results']['errors']) / log_data['results']['total_messages'] * 100
            print(f"성공률: {success_rate:.2f}%")
            
        except Exception as e:
            print(f"로그 분석 오류: {e}")
    
    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("=== 종합 RRC Flooding 테스트 ===")
        
        # srsRAN 상태 확인
        if not self.check_srsran_status():
            print("srsRAN이 실행되지 않았습니다. 테스트를 중단합니다.")
            return
        
        # 테스트 시나리오들
        test_scenarios = [
            {
                'name': '기본 Connection Request Flooding',
                'enb_ip': '127.0.0.1',
                'enb_port': 2000,
                'threads': 5,
                'duration': 30,
                'message_type': 'connection_request'
            },
            {
                'name': '고강도 Connection Request Flooding',
                'enb_ip': '127.0.0.1',
                'enb_port': 2000,
                'threads': 20,
                'duration': 60,
                'message_type': 'connection_request'
            },
            {
                'name': 'Reestablishment Request Flooding',
                'enb_ip': '127.0.0.1',
                'enb_port': 2000,
                'threads': 10,
                'duration': 30,
                'message_type': 'reestablishment_request'
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(test_scenarios):
            print(f"\n{'='*60}")
            print(f"테스트 시나리오 {i+1}: {scenario['name']}")
            print(f"{'='*60}")
            
            # 테스트 실행
            success = self.run_flooding_test(scenario)
            results.append({
                'scenario': scenario['name'],
                'success': success
            })
            
            # 결과 분석
            self.analyze_test_results(scenario)
            
            # 테스트 간 대기
            if i < len(test_scenarios) - 1:
                print(f"\n다음 테스트까지 10초 대기...")
                time.sleep(10)
        
        # 전체 결과 요약
        print(f"\n{'='*60}")
        print("전체 테스트 결과 요약")
        print(f"{'='*60}")
        
        for result in results:
            status = "성공" if result['success'] else "실패"
            print(f"  {result['scenario']}: {status}")
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n총 {len(results)}개 테스트 중 {success_count}개 성공")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RRC Flooding Attack 테스트')
    parser.add_argument('--comprehensive', action='store_true', help='종합 테스트 실행')
    parser.add_argument('--check-status', action='store_true', help='srsRAN 상태만 확인')
    
    args = parser.parse_args()
    
    tester = RRCFloodingTest()
    
    if args.check_status:
        tester.check_srsran_status()
    elif args.comprehensive:
        tester.run_comprehensive_test()
    else:
        print("사용법:")
        print("  --check-status: srsRAN 상태 확인")
        print("  --comprehensive: 종합 테스트 실행")

if __name__ == "__main__":
    main()
