#!/usr/bin/env python3
"""
srsUE 실행 및 패킷 캡처 통합 스크립트
srsUE를 실행하면서 동시에 패킷을 캡처합니다.
"""

import subprocess
import time
import signal
import sys
import os
import threading
from datetime import datetime

class SrsUERunner:
    def __init__(self):
        self.srsue_process = None
        self.capture_process = None
        self.running = False
        
    def start_srsue(self):
        """srsUE 시작"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] srsUE 시작...")
        
        # srsUE 실행 경로 확인
        srsue_paths = [
            "/home/tuna/libzmq/czmq/srsRAN_4G/build/srsue/src/srsue",
            "./srsue/src/srsue",
            "srsue"
        ]
        
        srsue_cmd = None
        for path in srsue_paths:
            if os.path.exists(path):
                srsue_cmd = path
                break
        
        if not srsue_cmd:
            print("srsUE 실행 파일을 찾을 수 없습니다.")
            return False
        
        try:
            # srsUE 실행
            self.srsue_process = subprocess.Popen(
                [srsue_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] srsUE 시작됨 (PID: {self.srsue_process.pid})")
            
            # srsUE 출력 모니터링
            def monitor_srsue():
                for line in iter(self.srsue_process.stdout.readline, ''):
                    if line:
                        print(f"[srsUE] {line.strip()}")
            
            monitor_thread = threading.Thread(target=monitor_srsue, daemon=True)
            monitor_thread.start()
            
            # srsUE 시작 대기
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"srsUE 시작 오류: {e}")
            return False
    
    def start_capture(self, duration=60):
        """패킷 캡처 시작"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        capture_file = f"/tmp/srsue_capture_{timestamp}.pcap"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 패킷 캡처 시작...")
        print(f"캡처 파일: {capture_file}")
        
        # tcpdump 명령어
        cmd = [
            "sudo", "tcpdump",
            "-i", "tun_srsue",
            "-w", capture_file,
            "-n",
            "-v"
        ]
        
        try:
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 캡처 프로세스 시작됨 (PID: {self.capture_process.pid})")
            
            # 지정된 시간 동안 대기
            time.sleep(duration)
            
            return capture_file
            
        except Exception as e:
            print(f"캡처 시작 오류: {e}")
            return None
    
    def stop_all(self):
        """모든 프로세스 중지"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 모든 프로세스 중지 중...")
        
        if self.capture_process:
            self.capture_process.terminate()
            try:
                self.capture_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.capture_process.kill()
        
        if self.srsue_process:
            self.srsue_process.terminate()
            try:
                self.srsue_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.srsue_process.kill()
        
        self.running = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 모든 프로세스 중지 완료")

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 시그널 {signum} 수신, 중지...")
    sys.exit(0)

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="srsUE 실행 및 패킷 캡처")
    parser.add_argument("--duration", type=int, default=60, help="캡처 지속 시간 (초)")
    parser.add_argument("--srsue-only", action="store_true", help="srsUE만 실행 (캡처 없음)")
    
    args = parser.parse_args()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=== srsUE 실행 및 패킷 캡처 ===")
    print(f"캡처 지속 시간: {args.duration}초")
    print("=" * 40)
    
    runner = SrsUERunner()
    
    try:
        # srsUE 시작
        if runner.start_srsue():
            if not args.srsue_only:
                # 패킷 캡처
                capture_file = runner.start_capture(args.duration)
                
                if capture_file:
                    print(f"\n=== 캡처 완료 ===")
                    print(f"캡처 파일: {capture_file}")
                    print("패킷 분석을 위해 다음 명령어를 실행하세요:")
                    print(f"python3 capture_srsue_packets.py --analyze {capture_file}")
            else:
                print("srsUE만 실행 중... (Ctrl+C로 중지)")
                # 무한 대기
                while True:
                    time.sleep(1)
        else:
            print("srsUE 시작 실패")
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 사용자에 의해 중단됨")
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        runner.stop_all()

if __name__ == "__main__":
    main()
