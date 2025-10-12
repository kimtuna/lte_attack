#!/usr/bin/env python3
"""
srsRAN 프로세스 및 포트 관리 도구
포트 확인, 프로세스 종료, 상태 모니터링
"""

import subprocess
import json
import time
import os
from datetime import datetime

class SrsRANManager:
    """srsRAN 프로세스 및 포트 관리 클래스"""
    
    def __init__(self):
        self.srsran_ports = [2000, 2001, 2002, 2003, 2004, 2005]
        self.srsran_processes = ['srsenb', 'srsue', 'srsepc', 'srsran']
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def check_ports(self):
        """포트 사용 현황 확인"""
        print("=== 포트 사용 현황 확인 ===")
        
        try:
            # lsof 명령어로 포트 확인
            result = subprocess.run(['sudo', 'lsof', '-i'], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                # srsRAN 관련 포트만 필터링
                srsran_ports_info = []
                for line in lines:
                    if any(str(port) in line for port in self.srsran_ports):
                        srsran_ports_info.append(line.strip())
                
                if srsran_ports_info:
                    print("srsRAN 관련 포트 사용 현황:")
                    for info in srsran_ports_info:
                        print(f"  {info}")
                else:
                    print("srsRAN 관련 포트가 사용되지 않습니다.")
                
                return srsran_ports_info
            else:
                print(f"포트 확인 오류: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"포트 확인 오류: {e}")
            return []
    
    def check_processes(self):
        """srsRAN 프로세스 확인"""
        print("\n=== srsRAN 프로세스 확인 ===")
        
        try:
            # ps 명령어로 프로세스 확인
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                
                # srsRAN 관련 프로세스만 필터링
                srsran_processes = []
                for line in lines:
                    if any(process in line.lower() for process in self.srsran_processes):
                        srsran_processes.append(line.strip())
                
                if srsran_processes:
                    print("실행 중인 srsRAN 프로세스:")
                    for process in srsran_processes:
                        print(f"  {process}")
                else:
                    print("실행 중인 srsRAN 프로세스가 없습니다.")
                
                return srsran_processes
            else:
                print(f"프로세스 확인 오류: {result.stderr}")
                return []
                
        except Exception as e:
            print(f"프로세스 확인 오류: {e}")
            return []
    
    def kill_processes(self, force=False):
        """srsRAN 프로세스 종료"""
        print("\n=== srsRAN 프로세스 종료 ===")
        
        try:
            if force:
                # 강제 종료
                print("강제 종료 모드")
                for process in self.srsran_processes:
                    try:
                        result = subprocess.run(['sudo', 'killall', '-9', process], 
                                               capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"  {process} 강제 종료 완료")
                        else:
                            print(f"  {process} 종료 실패: {result.stderr}")
                    except Exception as e:
                        print(f"  {process} 종료 오류: {e}")
            else:
                # 일반 종료
                print("일반 종료 모드")
                for process in self.srsran_processes:
                    try:
                        result = subprocess.run(['sudo', 'pkill', '-f', process], 
                                               capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"  {process} 종료 완료")
                        else:
                            print(f"  {process} 종료 실패: {result.stderr}")
                    except Exception as e:
                        print(f"  {process} 종료 오류: {e}")
            
            # 종료 확인
            time.sleep(2)
            remaining_processes = self.check_processes()
            
            if not remaining_processes:
                print("모든 srsRAN 프로세스가 종료되었습니다.")
            else:
                print("일부 프로세스가 여전히 실행 중입니다.")
                
        except Exception as e:
            print(f"프로세스 종료 오류: {e}")
    
    def kill_by_port(self, port):
        """특정 포트를 사용하는 프로세스 종료"""
        print(f"\n=== 포트 {port} 사용 프로세스 종료 ===")
        
        try:
            # 포트를 사용하는 프로세스 PID 확인
            result = subprocess.run(['sudo', 'lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                
                for pid in pids:
                    if pid.strip():
                        try:
                            # 프로세스 종료
                            kill_result = subprocess.run(['sudo', 'kill', '-9', pid], 
                                                       capture_output=True, text=True)
                            if kill_result.returncode == 0:
                                print(f"  PID {pid} 종료 완료")
                            else:
                                print(f"  PID {pid} 종료 실패: {kill_result.stderr}")
                        except Exception as e:
                            print(f"  PID {pid} 종료 오류: {e}")
            else:
                print(f"포트 {port}를 사용하는 프로세스가 없습니다.")
                
        except Exception as e:
            print(f"포트 {port} 프로세스 종료 오류: {e}")
    
    def monitor_status(self, duration=60):
        """srsRAN 상태 모니터링"""
        print(f"=== srsRAN 상태 모니터링 ({duration}초) ===")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        monitor_file = f"{self.log_dir}/srsran_monitor_{timestamp}.log"
        
        start_time = time.time()
        
        with open(monitor_file, 'w') as f:
            f.write(f"srsRAN 상태 모니터링 시작: {datetime.now()}\n")
            f.write("=" * 50 + "\n")
            
            while time.time() - start_time < duration:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 프로세스 상태 확인
                processes = self.check_processes()
                f.write(f"\n[{current_time}] 프로세스 상태:\n")
                for process in processes:
                    f.write(f"  {process}\n")
                
                # 포트 상태 확인
                ports = self.check_ports()
                f.write(f"\n[{current_time}] 포트 상태:\n")
                for port in ports:
                    f.write(f"  {port}\n")
                
                f.write("-" * 30 + "\n")
                f.flush()
                
                time.sleep(5)  # 5초마다 확인
        
        print(f"모니터링 완료: {monitor_file}")
    
    def cleanup_all(self):
        """모든 srsRAN 관련 프로세스 및 포트 정리"""
        print("=== srsRAN 전체 정리 ===")
        
        # 프로세스 종료
        self.kill_processes(force=True)
        
        # 포트 정리
        for port in self.srsran_ports:
            self.kill_by_port(port)
        
        # 정리 확인
        time.sleep(3)
        remaining_processes = self.check_processes()
        remaining_ports = self.check_ports()
        
        if not remaining_processes and not remaining_ports:
            print("모든 srsRAN 관련 프로세스와 포트가 정리되었습니다.")
        else:
            print("일부 프로세스나 포트가 여전히 사용 중입니다.")
    
    def get_status_summary(self):
        """상태 요약 정보"""
        print("=== srsRAN 상태 요약 ===")
        
        processes = self.check_processes()
        ports = self.check_ports()
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'processes': len(processes),
            'ports': len(ports),
            'status': 'running' if processes else 'stopped'
        }
        
        print(f"상태: {summary['status']}")
        print(f"실행 중인 프로세스: {summary['processes']}개")
        print(f"사용 중인 포트: {summary['ports']}개")
        
        return summary

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='srsRAN 프로세스 및 포트 관리')
    parser.add_argument('--check-ports', action='store_true', help='포트 사용 현황 확인')
    parser.add_argument('--check-processes', action='store_true', help='프로세스 확인')
    parser.add_argument('--kill-processes', action='store_true', help='프로세스 종료')
    parser.add_argument('--kill-port', type=int, help='특정 포트 사용 프로세스 종료')
    parser.add_argument('--monitor', type=int, help='상태 모니터링 (초)')
    parser.add_argument('--cleanup', action='store_true', help='전체 정리')
    parser.add_argument('--status', action='store_true', help='상태 요약')
    
    args = parser.parse_args()
    
    manager = SrsRANManager()
    
    if args.check_ports:
        manager.check_ports()
    elif args.check_processes:
        manager.check_processes()
    elif args.kill_processes:
        manager.kill_processes(force=True)
    elif args.kill_port:
        manager.kill_by_port(args.kill_port)
    elif args.monitor:
        manager.monitor_status(args.monitor)
    elif args.cleanup:
        manager.cleanup_all()
    elif args.status:
        manager.get_status_summary()
    else:
        # 기본: 모든 상태 확인
        manager.check_ports()
        manager.check_processes()
        manager.get_status_summary()

if __name__ == "__main__":
    main()
