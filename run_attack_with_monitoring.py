#!/usr/bin/env python3
"""
RRC Flooding Attack과 모니터링을 함께 실행하는 스크립트
공격 전후 시스템 상태를 자동으로 모니터링
"""

import subprocess
import time
import threading
import os
from datetime import datetime

class AttackWithMonitoring:
    """공격과 모니터링을 함께 실행하는 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.monitoring_process = None
        self.attack_process = None
    
    def start_monitoring(self, duration=300):
        """모니터링 시작"""
        print("=== 모니터링 시작 ===")
        
        # 모니터링 스크립트 실행
        cmd = ['python3', 'monitor_attack_impact.py', '--duration', str(duration)]
        
        try:
            self.monitoring_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"모니터링 프로세스 시작 (PID: {self.monitoring_process.pid})")
            return True
        except Exception as e:
            print(f"모니터링 시작 오류: {e}")
            return False
    
    def start_attack(self, attack_config):
        """공격 시작"""
        print("=== 공격 시작 ===")
        
        # 공격 스크립트 실행
        cmd = [
            'python3', 'rrc_flooding_attack.py',
            '--enb-ip', attack_config['enb_ip'],
            '--enb-port', str(attack_config['enb_port']),
            '--threads', str(attack_config['threads']),
            '--duration', str(attack_config['duration']),
            '--message-type', attack_config['message_type']
        ]
        
        try:
            self.attack_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"공격 프로세스 시작 (PID: {self.attack_process.pid})")
            return True
        except Exception as e:
            print(f"공격 시작 오류: {e}")
            return False
    
    def wait_for_attack_completion(self):
        """공격 완료 대기"""
        if not self.attack_process:
            return False
        
        try:
            stdout, stderr = self.attack_process.communicate()
            
            print("=== 공격 결과 ===")
            print("STDOUT:")
            print(stdout)
            
            if stderr:
                print("STDERR:")
                print(stderr)
            
            return self.attack_process.returncode == 0
        except Exception as e:
            print(f"공격 완료 대기 오류: {e}")
            return False
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if not self.monitoring_process:
            return
        
        try:
            self.monitoring_process.terminate()
            self.monitoring_process.wait(timeout=10)
            print("모니터링 프로세스 종료")
        except subprocess.TimeoutExpired:
            self.monitoring_process.kill()
            print("모니터링 프로세스 강제 종료")
        except Exception as e:
            print(f"모니터링 중지 오류: {e}")
    
    def run_attack_with_monitoring(self, attack_config, monitoring_duration=300):
        """공격과 모니터링을 함께 실행"""
        print("=== RRC Flooding Attack with Monitoring ===")
        print(f"공격 설정: {attack_config}")
        print(f"모니터링 지속 시간: {monitoring_duration}초")
        print("=" * 60)
        
        # 모니터링 시작
        if not self.start_monitoring(monitoring_duration):
            print("모니터링 시작 실패")
            return False
        
        # 모니터링 안정화 대기
        print("모니터링 안정화 대기 (10초)...")
        time.sleep(10)
        
        # 공격 시작
        if not self.start_attack(attack_config):
            print("공격 시작 실패")
            self.stop_monitoring()
            return False
        
        # 공격 완료 대기
        print("공격 완료 대기...")
        attack_success = self.wait_for_attack_completion()
        
        # 모니터링 추가 대기 (공격 후 상태 확인)
        print("공격 후 상태 확인 (30초)...")
        time.sleep(30)
        
        # 모니터링 중지
        self.stop_monitoring()
        
        # 결과 요약
        print("\n=== 실행 결과 요약 ===")
        print(f"공격 성공: {'예' if attack_success else '아니오'}")
        print(f"모니터링 완료: 예")
        
        return attack_success
    
    def run_multiple_attacks(self, attack_configs, monitoring_duration=300):
        """여러 공격을 순차적으로 실행"""
        print("=== 다중 공격 실행 ===")
        print(f"총 {len(attack_configs)}개 공격 실행 예정")
        print("=" * 40)
        
        results = []
        
        for i, attack_config in enumerate(attack_configs):
            print(f"\n공격 {i+1}/{len(attack_configs)}: {attack_config['message_type']} ({attack_config['threads']}스레드)")
            
            # 공격 실행
            success = self.run_attack_with_monitoring(attack_config, monitoring_duration)
            
            results.append({
                'attack_config': attack_config,
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
            
            # 공격 간 대기
            if i < len(attack_configs) - 1:
                print(f"\n다음 공격까지 30초 대기...")
                time.sleep(30)
        
        # 전체 결과 요약
        print("\n=== 전체 결과 요약 ===")
        success_count = sum(1 for r in results if r['success'])
        print(f"총 {len(results)}개 공격 중 {success_count}개 성공")
        
        for i, result in enumerate(results):
            status = "성공" if result['success'] else "실패"
            config = result['attack_config']
            print(f"  공격 {i+1}: {config['message_type']} ({config['threads']}스레드) - {status}")
        
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RRC Flooding Attack with Monitoring')
    parser.add_argument('--enb-ip', default='127.0.0.1', help='eNB IP 주소')
    parser.add_argument('--enb-port', type=int, default=2000, help='eNB 포트')
    parser.add_argument('--threads', type=int, default=10, help='동시 스레드 수')
    parser.add_argument('--duration', type=int, default=60, help='공격 지속 시간 (초)')
    parser.add_argument('--message-type', choices=['connection_request', 'reestablishment_request'], 
                       default='reestablishment_request', help='메시지 타입')
    parser.add_argument('--monitoring-duration', type=int, default=300, help='모니터링 지속 시간 (초)')
    parser.add_argument('--multiple', action='store_true', help='다중 공격 실행')
    
    args = parser.parse_args()
    
    # 공격 설정
    attack_config = {
        'enb_ip': args.enb_ip,
        'enb_port': args.enb_port,
        'threads': args.threads,
        'duration': args.duration,
        'message_type': args.message_type
    }
    
    runner = AttackWithMonitoring()
    
    if args.multiple:
        # 다중 공격 설정
        attack_configs = [
            {
                'enb_ip': args.enb_ip,
                'enb_port': args.enb_port,
                'threads': 10,
                'duration': 60,
                'message_type': 'reestablishment_request'
            },
            {
                'enb_ip': args.enb_ip,
                'enb_port': args.enb_port,
                'threads': 20,
                'duration': 60,
                'message_type': 'reestablishment_request'
            },
            {
                'enb_ip': args.enb_ip,
                'enb_port': args.enb_port,
                'threads': 50,
                'duration': 60,
                'message_type': 'reestablishment_request'
            }
        ]
        
        runner.run_multiple_attacks(attack_configs, args.monitoring_duration)
    else:
        # 단일 공격 실행
        runner.run_attack_with_monitoring(attack_config, args.monitoring_duration)

if __name__ == "__main__":
    main()
