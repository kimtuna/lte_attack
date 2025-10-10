#!/usr/bin/env python3
"""
tshark를 사용한 RRC 메시지 핸들링 모니터링 도구
srsRAN 환경에서 RRC 메시지의 실시간 처리 과정을 tshark로 분석
"""

import subprocess
import time
import threading
import json
import re
from datetime import datetime
import argparse
import os

class TsharkRRCMonitor:
    def __init__(self, interface="any", capture_file="rrc_messages.pcap"):
        self.interface = interface
        self.capture_file = capture_file
        self.monitoring = False
        self.stats = {
            "start_time": None,
            "rrc_requests": 0,
            "rrc_setups": 0,
            "rrc_setup_completes": 0,
            "rrc_rejects": 0,
            "total_packets": 0,
            "message_flow": []
        }
        
        # RRC 메시지 타입 매핑
        self.rrc_message_types = {
            0x0001: "RRC Connection Request",
            0x0002: "RRC Connection Setup", 
            0x0003: "RRC Connection Setup Complete",
            0x0004: "RRC Connection Reject",
            0x0005: "RRC Connection Release"
        }
    
    def start_capture(self):
        """tshark 캡처 시작"""
        print(f"tshark RRC 메시지 캡처 시작: {self.capture_file}")
        
        # tshark 캡처 명령어 (포트 2000, 2001)
        cmd = [
            "sudo", "tshark",
            "-i", self.interface,
            "-w", self.capture_file,
            "-f", "port 2000 or port 2001"
        ]
        
        print(f"실행 명령어: {' '.join(cmd)}")
        
        try:
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.monitoring = True
            self.stats["start_time"] = datetime.now()
            print("✅ tshark 캡처 프로세스 시작됨")
            
        except Exception as e:
            print(f"❌ 캡처 시작 오류: {e}")
    
    def stop_capture(self):
        """tshark 캡처 중지"""
        if hasattr(self, 'capture_process'):
            self.capture_process.terminate()
            self.capture_process.wait()
            self.monitoring = False
            print("캡처 중지됨")
    
    def analyze_capture_realtime(self):
        """실시간 캡처 분석"""
        if not self.monitoring:
            return
        
        try:
            # 실시간 패킷 분석 명령어
            cmd = [
                "sudo", "tshark",
                "-i", self.interface,
                "-f", "port 2000 or port 2001",
                "-T", "fields",
                "-e", "frame.time",
                "-e", "ip.src",
                "-e", "ip.dst", 
                "-e", "udp.srcport",
                "-e", "udp.dstport",
                "-e", "data"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            print("실시간 RRC 메시지 분석 시작...")
            
            while self.monitoring:
                line = process.stdout.readline()
                if line:
                    self.parse_packet_line(line.strip())
                time.sleep(0.1)
                
        except Exception as e:
            print(f"실시간 분석 오류: {e}")
    
    def parse_packet_line(self, line):
        """패킷 라인 파싱"""
        if not line:
            return
        
        try:
            # tshark 출력 파싱 (tab으로 구분된 필드)
            fields = line.split('\t')
            if len(fields) >= 6:
                timestamp = fields[0]
                src_ip = fields[1]
                dst_ip = fields[2]
                src_port = fields[3]
                dst_port = fields[4]
                data = fields[5] if len(fields) > 5 else ""
                
                # 데이터에서 RRC 메시지 타입 추출
                if data and len(data) >= 4:
                    # 첫 2바이트에서 메시지 타입 추출
                    try:
                        message_type = int(data[:4], 16)
                        if message_type in self.rrc_message_types:
                            self.process_rrc_message(timestamp, src_ip, dst_ip, 
                                                   src_port, dst_port, message_type, data)
                    except ValueError:
                        pass
                        
        except Exception as e:
            print(f"패킷 파싱 오류: {e}")
    
    def process_rrc_message(self, timestamp, src_ip, dst_ip, src_port, dst_port, msg_type, data):
        """RRC 메시지 처리"""
        message_name = self.rrc_message_types[msg_type]
        
        # 통계 업데이트
        if msg_type == 0x0001:
            self.stats["rrc_requests"] += 1
        elif msg_type == 0x0002:
            self.stats["rrc_setups"] += 1
        elif msg_type == 0x0003:
            self.stats["rrc_setup_completes"] += 1
        elif msg_type == 0x0004:
            self.stats["rrc_rejects"] += 1
        
        self.stats["total_packets"] += 1
        
        # 메시지 플로우 기록
        message_info = {
            "timestamp": timestamp,
            "src": f"{src_ip}:{src_port}",
            "dst": f"{dst_ip}:{dst_port}",
            "message_type": message_name,
            "hex_data": data[:32]  # 처음 16바이트만
        }
        
        self.stats["message_flow"].append(message_info)
        
        # 실시간 출력
        print(f"[{timestamp}] {message_name}")
        print(f"  {src_ip}:{src_port} → {dst_ip}:{dst_port}")
        print(f"  데이터: {data[:32]}...")
        print("-" * 50)
    
    def analyze_capture_file(self):
        """캡처 파일 분석"""
        if not os.path.exists(self.capture_file):
            print(f"⚠️  캡처 파일이 없습니다: {self.capture_file}")
            return
        
        file_size = os.path.getsize(self.capture_file)
        print(f"📁 캡처 파일 크기: {file_size} bytes")
        
        try:
            # RRC 메시지별 분석
            for msg_type, msg_name in self.rrc_message_types.items():
                cmd = [
                    "tshark",
                    "-r", self.capture_file,
                    "-Y", f"udp contains 0x{msg_type:04x}",
                    "-T", "fields",
                    "-e", "frame.number",
                    "-e", "frame.time",
                    "-e", "data"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                
                if count > 0:
                    print(f"{msg_name}: {count}개")
                    
                    # 첫 번째 메시지 예시 출력
                    lines = result.stdout.strip().split('\n')
                    if lines and lines[0]:
                        parts = lines[0].split('\t')
                        if len(parts) >= 3:
                            print(f"  예시: {parts[1]} - {parts[2][:32]}...")
                
        except Exception as e:
            print(f"파일 분석 오류: {e}")
    
    def print_stats(self):
        """통계 정보 출력"""
        print("\n=== RRC 메시지 핸들링 통계 ===")
        print(f"시작 시간: {self.stats['start_time']}")
        print(f"총 패킷 수: {self.stats['total_packets']}")
        print(f"RRC Connection Request: {self.stats['rrc_requests']}")
        print(f"RRC Connection Setup: {self.stats['rrc_setups']}")
        print(f"RRC Connection Setup Complete: {self.stats['rrc_setup_completes']}")
        print(f"RRC Connection Reject: {self.stats['rrc_rejects']}")
        
        # 메시지 플로우 분석
        if self.stats['message_flow']:
            print(f"\n메시지 플로우 ({len(self.stats['message_flow'])}개):")
            for i, msg in enumerate(self.stats['message_flow'][-10:], 1):  # 최근 10개만
                print(f"  {i}. {msg['timestamp']} - {msg['message_type']}")
                print(f"     {msg['src']} → {msg['dst']}")
        
        print("=" * 40)
    
    def save_stats(self, filename="rrc_stats.json"):
        """통계를 JSON 파일로 저장"""
        stats_copy = self.stats.copy()
        if stats_copy["start_time"]:
            stats_copy["start_time"] = stats_copy["start_time"].isoformat()
        
        with open(filename, 'w') as f:
            json.dump(stats_copy, f, indent=2)
        
        print(f"통계 저장됨: {filename}")

def main():
    parser = argparse.ArgumentParser(description='tshark RRC 메시지 핸들링 모니터링')
    parser.add_argument('--interface', default='any', help='네트워크 인터페이스')
    parser.add_argument('--capture-file', default='rrc_messages.pcap', help='캡처 파일명')
    parser.add_argument('--duration', type=int, default=60, help='모니터링 지속 시간 (초)')
    
    args = parser.parse_args()
    
    monitor = TsharkRRCMonitor(args.interface, args.capture_file)
    
    try:
        # 캡처 시작
        monitor.start_capture()
        
        # 실시간 분석 스레드 시작
        analysis_thread = threading.Thread(target=monitor.analyze_capture_realtime)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        # 모니터링 지속
        print(f"RRC 메시지 모니터링 중... ({args.duration}초)")
        time.sleep(args.duration)
        
    except KeyboardInterrupt:
        print("\n모니터링 중지")
    finally:
        monitor.stop_capture()
        monitor.analyze_capture_file()
        monitor.print_stats()
        monitor.save_stats()

if __name__ == "__main__":
    main()
