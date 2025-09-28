#!/usr/bin/env python3
"""
Resource Depletion Attack 실행기
다양한 DoS 공격을 순차적으로 실행하고 결과를 분석
"""

import subprocess
import time
import threading
import sys
import os
from datetime import datetime

class AttackRunner:
    def __init__(self, target_ip="127.0.0.1"):
        self.target_ip = target_ip
        self.attacks = [
            {
                "name": "RRC Connection Flood",
                "script": "rrc_connection_flood.py",
                "duration": 60,
                "description": "대량의 RRC 연결 요청으로 eNB 리소스 고갈"
            },
            {
                "name": "Paging Storm",
                "script": "paging_storm_attack.py",
                "duration": 60,
                "description": "대량의 Paging 메시지로 UE 리소스 고갈"
            },
            {
                "name": "NAS Signaling Flood",
                "script": "nas_signaling_flood.py",
                "duration": 60,
                "description": "NAS 시그널링 메시지로 MME 리소스 고갈"
            },
            {
                "name": "Bearer Setup Flood",
                "script": "bearer_setup_flood.py",
                "duration": 60,
                "description": "Bearer 설정 요청으로 네트워크 리소스 고갈"
            }
        ]
        self.results = []
    
    def run_attack(self, attack_info):
        """개별 공격 실행"""
        print(f"\n{'='*50}")
        print(f"공격 시작: {attack_info['name']}")
        print(f"설명: {attack_info['description']}")
        print(f"지속 시간: {attack_info['duration']}초")
        print(f"{'='*50}")
        
        start_time = datetime.now()
        
        try:
            # 공격 스크립트 실행
            result = subprocess.run([
                "python3", attack_info["script"]
            ], capture_output=True, text=True, timeout=attack_info["duration"] + 30)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            attack_result = {
                "name": attack_info["name"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
            self.results.append(attack_result)
            
            print(f"공격 완료: {attack_info['name']}")
            print(f"실행 시간: {duration:.2f}초")
            print(f"성공 여부: {'성공' if attack_result['success'] else '실패'}")
            
            if result.stderr:
                print(f"오류 메시지: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            print(f"공격 시간 초과: {attack_info['name']}")
        except Exception as e:
            print(f"공격 실행 오류: {e}")
    
    def run_all_attacks(self):
        """모든 공격 순차 실행"""
        print("Resource Depletion Attack 테스트 시작")
        print(f"대상 IP: {self.target_ip}")
        print(f"총 공격 수: {len(self.attacks)}")
        
        for i, attack in enumerate(self.attacks, 1):
            print(f"\n진행률: {i}/{len(self.attacks)}")
            self.run_attack(attack)
            
            # 공격 간 대기 시간
            if i < len(self.attacks):
                print("다음 공격까지 30초 대기...")
                time.sleep(30)
        
        self.print_summary()
    
    def print_summary(self):
        """결과 요약 출력"""
        print(f"\n{'='*60}")
        print("공격 테스트 결과 요약")
        print(f"{'='*60}")
        
        for result in self.results:
            status = "성공" if result["success"] else "실패"
            print(f"{result['name']}: {status} ({result['duration']:.2f}초)")
        
        print(f"\n총 실행 시간: {sum(r['duration'] for r in self.results):.2f}초")
        print(f"성공한 공격: {sum(1 for r in self.results if r['success'])}/{len(self.results)}")
    
    def save_results(self, filename="attack_results.json"):
        """결과를 JSON 파일로 저장"""
        import json
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"결과 저장됨: {filename}")

def main():
    if len(sys.argv) > 1:
        target_ip = sys.argv[1]
    else:
        target_ip = "127.0.0.1"
    
    runner = AttackRunner(target_ip)
    
    try:
        runner.run_all_attacks()
        runner.save_results()
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
        runner.print_summary()

if __name__ == "__main__":
    main()
