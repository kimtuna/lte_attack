#!/usr/bin/env python3
"""
실제 UE RRC 메시지 캡처 및 분석
tshark로 실제 UE가 보내는 RRC 메시지를 캡처하고 형식을 분석
"""

import subprocess
import struct
import json
import os
from datetime import datetime

class RealUERRCCapture:
    def __init__(self, interface="any", duration=60):
        self.interface = interface
        self.duration = duration
        self.captured_packets = []
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def capture_ue_packets(self):
        """실제 UE 패킷 캡처"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        capture_file = f"{self.log_dir}/ue_rrc_capture_{timestamp}.pcap"
        
        print(f"=== 실제 UE RRC 메시지 캡처 시작 ===")
        print(f"캡처 시간: {self.duration}초")
        print(f"캡처 파일: {capture_file}")
        print("실제 UE를 사용해서 RRC 메시지를 보내주세요...")
        print("=" * 50)
        
        # tshark로 패킷 캡처
        cmd = [
            "sudo", "tshark",
            "-i", self.interface,
            "-a", f"duration:{self.duration}",
            "-f", "port 2000 or port 2001",
            "-w", capture_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.duration + 10)
            if result.returncode == 0:
                print(f"패킷 캡처 완료: {capture_file}")
                return capture_file
            else:
                print(f"패킷 캡처 실패: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            print("캡처 시간 초과")
            return None
        except Exception as e:
            print(f"캡처 오류: {e}")
            return None
    
    def analyze_captured_packets(self, capture_file):
        """캡처된 패킷 분석"""
        if not os.path.exists(capture_file):
            print(f"캡처 파일이 없습니다: {capture_file}")
            return False
        
        print(f"\n=== 캡처된 패킷 분석 ===")
        
        # RRC 메시지 필터링
        cmd = [
            "tshark",
            "-r", capture_file,
            "-Y", "tcp.len > 0 and (port 2000 or port 2001)",
            "-T", "fields",
            "-e", "frame.time",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "tcp.srcport",
            "-e", "tcp.dstport",
            "-e", "tcp.len",
            "-e", "data"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            if not lines or not lines[0]:
                print("분석된 RRC 메시지가 없습니다.")
                return False
            
            print(f"총 {len(lines)}개 패킷 분석")
            print("\n=== RRC 메시지 분석 결과 ===")
            
            for i, line in enumerate(lines):
                parts = line.split('\t')
                if len(parts) >= 7:
                    timestamp, ip_src, ip_dst, src_port, dst_port, tcp_len, data = parts
                    
                    # 포트 2000으로 가는 패킷 (UE → eNB)
                    if dst_port == "2000":
                        print(f"\n[패킷 {i+1}] UE → eNB (포트 2000)")
                        print(f"  시간: {timestamp}")
                        print(f"  소스: {ip_src}:{src_port}")
                        print(f"  대상: {ip_dst}:{dst_port}")
                        print(f"  크기: {tcp_len} bytes")
                        print(f"  데이터: {data}")
                        
                        # RRC 메시지 타입 추출
                        if data and len(data) >= 4:
                            try:
                                # 첫 2바이트에서 메시지 타입 추출
                                msg_type = int(data[:4], 16)
                                print(f"  RRC 메시지 타입: 0x{msg_type:04X}")
                                
                                # 메시지 저장
                                self.captured_packets.append({
                                    'timestamp': timestamp,
                                    'direction': 'UE→eNB',
                                    'port': dst_port,
                                    'size': tcp_len,
                                    'data': data,
                                    'message_type': f"0x{msg_type:04X}"
                                })
                            except ValueError:
                                print(f"  메시지 타입 파싱 실패")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"tshark 분석 오류: {e.stderr}")
            return False
    
    def save_analysis_results(self):
        """분석 결과 저장"""
        if not self.captured_packets:
            print("저장할 분석 결과가 없습니다.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{self.log_dir}/ue_rrc_analysis_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.captured_packets, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== 분석 결과 저장 ===")
        print(f"파일: {output_file}")
        print(f"총 {len(self.captured_packets)}개 RRC 메시지 분석됨")
        
        # 메시지 타입별 통계
        message_types = {}
        for packet in self.captured_packets:
            msg_type = packet['message_type']
            if msg_type not in message_types:
                message_types[msg_type] = 0
            message_types[msg_type] += 1
        
        print("\n=== 메시지 타입별 통계 ===")
        for msg_type, count in message_types.items():
            print(f"  {msg_type}: {count}개")
    
    def generate_attack_packets(self):
        """분석된 패킷을 기반으로 공격용 패킷 생성"""
        if not self.captured_packets:
            print("분석된 패킷이 없어서 공격용 패킷을 생성할 수 없습니다.")
            return
        
        print(f"\n=== 공격용 패킷 생성 ===")
        
        # 가장 많이 사용된 메시지 타입 찾기
        message_types = {}
        for packet in self.captured_packets:
            msg_type = packet['message_type']
            if msg_type not in message_types:
                message_types[msg_type] = []
            message_types[msg_type].append(packet)
        
        # 가장 많이 사용된 메시지 타입
        most_common_type = max(message_types.keys(), key=lambda k: len(message_types[k]))
        print(f"가장 많이 사용된 메시지 타입: {most_common_type}")
        
        # 해당 메시지 타입의 패킷들 출력
        print(f"\n{most_common_type} 메시지 예시:")
        for i, packet in enumerate(message_types[most_common_type][:3]):  # 최대 3개만
            print(f"  예시 {i+1}: {packet['data']}")
    
    def run(self):
        """전체 프로세스 실행"""
        capture_file = self.capture_ue_packets()
        if capture_file:
            if self.analyze_captured_packets(capture_file):
                self.save_analysis_results()
                self.generate_attack_packets()
        else:
            print("패킷 캡처에 실패했습니다.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='실제 UE RRC 메시지 캡처 및 분석')
    parser.add_argument('--duration', type=int, default=60, help='캡처 시간 (초)')
    parser.add_argument('--interface', default='any', help='네트워크 인터페이스')
    
    args = parser.parse_args()
    
    capturer = RealUERRCCapture(args.interface, args.duration)
    capturer.run()
