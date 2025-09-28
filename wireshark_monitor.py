#!/usr/bin/env python3
"""
Wireshark 모니터링 스크립트
Resource Depletion Attack 중에 네트워크 트래픽을 모니터링하고 분석
"""

import subprocess
import time
import threading
import json
from datetime import datetime

class WiresharkMonitor:
    def __init__(self, interface="any", capture_file="lte_attack_capture.pcap"):
        self.interface = interface
        self.capture_file = capture_file
        self.monitoring = False
        self.stats = {
            "start_time": None,
            "packet_count": 0,
            "rrc_requests": 0,
            "paging_messages": 0,
            "nas_messages": 0,
            "bearer_requests": 0
        }
    
    def start_capture(self):
        """Wireshark 캡처 시작"""
        print(f"Wireshark 캡처 시작: {self.capture_file}")
        
        # tshark를 사용한 백그라운드 캡처
        cmd = [
            "tshark",
            "-i", self.interface,
            "-w", self.capture_file,
            "-f", "udp port 36412 or udp port 36422 or udp port 36432"
        ]
        
        try:
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.monitoring = True
            self.stats["start_time"] = datetime.now()
            print("캡처 프로세스 시작됨")
        except Exception as e:
            print(f"캡처 시작 오류: {e}")
    
    def stop_capture(self):
        """Wireshark 캡처 중지"""
        if hasattr(self, 'capture_process'):
            self.capture_process.terminate()
            self.capture_process.wait()
            self.monitoring = False
            print("캡처 중지됨")
    
    def analyze_capture(self):
        """캡처된 파일 분석"""
        if not self.monitoring:
            return
        
        try:
            # RRC Connection Request 분석
            rrc_cmd = [
                "tshark",
                "-r", self.capture_file,
                "-Y", "udp.port == 36412",
                "-T", "fields",
                "-e", "frame.number"
            ]
            
            result = subprocess.run(rrc_cmd, capture_output=True, text=True)
            self.stats["rrc_requests"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Paging 메시지 분석
            paging_cmd = [
                "tshark",
                "-r", self.capture_file,
                "-Y", "udp.port == 36422",
                "-T", "fields",
                "-e", "frame.number"
            ]
            
            result = subprocess.run(paging_cmd, capture_output=True, text=True)
            self.stats["paging_messages"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # NAS 메시지 분석
            nas_cmd = [
                "tshark",
                "-r", self.capture_file,
                "-Y", "udp.port == 36432",
                "-T", "fields",
                "-e", "frame.number"
            ]
            
            result = subprocess.run(nas_cmd, capture_output=True, text=True)
            self.stats["nas_messages"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # 전체 패킷 수
            total_cmd = [
                "tshark",
                "-r", self.capture_file,
                "-T", "fields",
                "-e", "frame.number"
            ]
            
            result = subprocess.run(total_cmd, capture_output=True, text=True)
            self.stats["packet_count"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
        except Exception as e:
            print(f"분석 오류: {e}")
    
    def print_stats(self):
        """통계 정보 출력"""
        print("\n=== 공격 모니터링 통계 ===")
        print(f"시작 시간: {self.stats['start_time']}")
        print(f"총 패킷 수: {self.stats['packet_count']}")
        print(f"RRC 요청: {self.stats['rrc_requests']}")
        print(f"Paging 메시지: {self.stats['paging_messages']}")
        print(f"NAS 메시지: {self.stats['nas_messages']}")
        print(f"Bearer 요청: {self.stats['bearer_requests']}")
        print("=" * 30)
    
    def save_stats(self, filename="attack_stats.json"):
        """통계를 JSON 파일로 저장"""
        stats_copy = self.stats.copy()
        if stats_copy["start_time"]:
            stats_copy["start_time"] = stats_copy["start_time"].isoformat()
        
        with open(filename, 'w') as f:
            json.dump(stats_copy, f, indent=2)
        
        print(f"통계 저장됨: {filename}")

def main():
    monitor = WiresharkMonitor()
    
    try:
        # 캡처 시작
        monitor.start_capture()
        
        # 모니터링 지속
        print("모니터링 중... (Ctrl+C로 중지)")
        while True:
            time.sleep(10)
            monitor.analyze_capture()
            monitor.print_stats()
            
    except KeyboardInterrupt:
        print("\n모니터링 중지")
        monitor.stop_capture()
        monitor.analyze_capture()
        monitor.print_stats()
        monitor.save_stats()

if __name__ == "__main__":
    main()
