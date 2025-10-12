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
        capture_file = f"/tmp/ue_rrc_capture_{timestamp}.pcap"
        
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
        
        # 모든 패킷 분석 (필터 제거)
        cmd = [
            "tshark",
            "-r", capture_file,
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
            result = subprocess.run(["sudo"] + cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            if not lines or not lines[0]:
                print("분석된 RRC 메시지가 없습니다.")
                return False
            
            print(f"총 {len(lines)}개 패킷 분석")
            print("\n=== 모든 패킷 분석 결과 ===")
            
            for i, line in enumerate(lines):
                parts = line.split('\t')
                if len(parts) >= 7:
                    timestamp, ip_src, ip_dst, src_port, dst_port, tcp_len, data = parts
                    
                    # 포트 2000 또는 2001과 관련된 패킷만 표시
                    if dst_port in ["2000", "2001"] or src_port in ["2000", "2001"]:
                        direction = "UE→eNB" if dst_port == "2000" else "eNB→UE" if src_port == "2001" else "Unknown"
                        print(f"\n[패킷 {i+1}] {direction}")
                        print(f"  시간: {timestamp}")
                        print(f"  소스: {ip_src}:{src_port}")
                        print(f"  대상: {ip_dst}:{dst_port}")
                        print(f"  크기: {tcp_len} bytes")
                        print(f"  데이터: {data}")
                        
                        # 전체 메시지 저장 (데이터가 있는 경우)
                        if data and len(data) > 0:
                            # 전체 메시지를 그대로 저장
                            self.captured_packets.append({
                                'timestamp': timestamp,
                                'direction': direction,
                                'src_port': src_port,
                                'dst_port': dst_port,
                                'size': tcp_len,
                                'data': data,
                                'message_hex': data
                            })
            
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
        
        # 메시지 크기별 통계
        message_sizes = {}
        for packet in self.captured_packets:
            size = packet['size']
            if size not in message_sizes:
                message_sizes[size] = 0
            message_sizes[size] += 1
        
        print("\n=== 메시지 크기별 통계 ===")
        for size, count in sorted(message_sizes.items()):
            print(f"  {size} bytes: {count}개")
    
    def generate_attack_packets(self):
        """분석된 패킷을 기반으로 공격용 패킷 생성"""
        if not self.captured_packets:
            print("분석된 패킷이 없어서 공격용 패킷을 생성할 수 없습니다.")
            return
        
        print(f"\n=== 공격용 패킷 생성 ===")
        
        # UE→eNB 방향의 메시지만 필터링
        ue_to_enb_packets = [p for p in self.captured_packets if p['direction'] == 'UE→eNB']
        
        if not ue_to_enb_packets:
            print("UE→eNB 방향의 메시지가 없습니다.")
            return
        
        print(f"UE→eNB 메시지 {len(ue_to_enb_packets)}개 발견")
        
        # 실제 메시지 예시 출력
        print(f"\n실제 UE 메시지 예시:")
        for i, packet in enumerate(ue_to_enb_packets[:5]):  # 최대 5개만
            print(f"  예시 {i+1}: {packet['data']}")
        
        # 공격용 패킷 파일 생성
        self.save_attack_packets(ue_to_enb_packets)
    
    def save_attack_packets(self, packets):
        """공격용 패킷을 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        attack_file = f"{self.log_dir}/attack_packets_{timestamp}.txt"
        
        with open(attack_file, 'w') as f:
            f.write("# 실제 UE RRC 메시지 (공격용)\n")
            f.write("# 포맷: hex_data\n\n")
            
            for packet in packets:
                f.write(f"{packet['data']}\n")
        
        print(f"\n공격용 패킷 저장: {attack_file}")
        print(f"총 {len(packets)}개 메시지 저장됨")
    
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
