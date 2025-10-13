#!/usr/bin/env python3
"""
srsUE 실제 패킷 캡처 및 분석 스크립트
tun_srsue 인터페이스에서 실제 RRC 메시지를 캡처합니다.
"""

import subprocess
import json
import time
import signal
import sys
import os
from datetime import datetime
import threading

class SrsUEPacketCapture:
    def __init__(self):
        self.capture_process = None
        self.captured_packets = []
        self.capture_file = None
        self.running = False
        
    def start_capture(self, duration=60):
        """패킷 캡처 시작"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.capture_file = f"/tmp/srsue_packets_{timestamp}.pcap"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 패킷 캡처 시작...")
        print(f"캡처 파일: {self.capture_file}")
        print(f"지속 시간: {duration}초")
        
        # tcpdump 명령어 구성
        cmd = [
            "sudo", "tcpdump",
            "-i", "tun_srsue",  # srsUE 터널 인터페이스
            "-w", self.capture_file,
            "-n",  # DNS 조회 비활성화
            "-v",  # 상세 출력
            "port", "2000", "or", "port", "2001"  # srsRAN 포트들
        ]
        
        try:
            self.capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.running = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 캡처 프로세스 시작됨 (PID: {self.capture_process.pid})")
            
            # 지정된 시간 동안 캡처
            time.sleep(duration)
            
        except Exception as e:
            print(f"캡처 시작 오류: {e}")
            return False
            
        return True
    
    def stop_capture(self):
        """패킷 캡처 중지"""
        if self.capture_process and self.running:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 캡처 중지 중...")
            
            # 프로세스 종료
            self.capture_process.terminate()
            
            # 5초 대기 후 강제 종료
            try:
                self.capture_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.capture_process.kill()
                self.capture_process.wait()
            
            self.running = False
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 캡처 완료")
            
            return True
        return False
    
    def analyze_packets(self):
        """캡처된 패킷 분석"""
        if not self.capture_file or not os.path.exists(self.capture_file):
            print("캡처 파일이 없습니다.")
            return None
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 패킷 분석 시작...")
        
        # tshark로 패킷 분석
        cmd = [
            "tshark",
            "-r", self.capture_file,
            "-T", "json",
            "-e", "frame.time",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "tcp.srcport",
            "-e", "tcp.dstport",
            "-e", "tcp.payload",
            "-e", "udp.payload"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packets_data = json.loads(result.stdout)
                
                analysis_result = {
                    "analysis_info": {
                        "timestamp": datetime.now().isoformat(),
                        "capture_file": self.capture_file,
                        "total_packets": len(packets_data),
                        "description": "srsUE 패킷 분석 결과"
                    },
                    "packets": []
                }
                
                for packet in packets_data:
                    packet_info = {
                        "timestamp": packet.get("_source", {}).get("layers", {}).get("frame.time", [""])[0],
                        "src_ip": packet.get("_source", {}).get("layers", {}).get("ip.src", [""])[0],
                        "dst_ip": packet.get("_source", {}).get("layers", {}).get("ip.dst", [""])[0],
                        "src_port": packet.get("_source", {}).get("layers", {}).get("tcp.srcport", [""])[0],
                        "dst_port": packet.get("_source", {}).get("layers", {}).get("tcp.dstport", [""])[0],
                        "payload": packet.get("_source", {}).get("layers", {}).get("tcp.payload", [""])[0]
                    }
                    
                    # UDP 페이로드도 확인
                    if not packet_info["payload"]:
                        packet_info["payload"] = packet.get("_source", {}).get("layers", {}).get("udp.payload", [""])[0]
                    
                    analysis_result["packets"].append(packet_info)
                
                return analysis_result
            else:
                print(f"tshark 오류: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"패킷 분석 오류: {e}")
            return None
    
    def save_analysis(self, analysis_result):
        """분석 결과 저장"""
        if not analysis_result:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"logs/srsue_packet_analysis_{timestamp}.json"
        
        # logs 디렉토리 생성
        os.makedirs("logs", exist_ok=True)
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 분석 결과 저장: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"파일 저장 오류: {e}")
            return None

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 시그널 {signum} 수신, 캡처 중지...")
    sys.exit(0)

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="srsUE 패킷 캡처 및 분석")
    parser.add_argument("--duration", type=int, default=60, help="캡처 지속 시간 (초)")
    parser.add_argument("--interface", default="tun_srsue", help="캡처할 인터페이스")
    
    args = parser.parse_args()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=== srsUE 패킷 캡처 및 분석 ===")
    print(f"인터페이스: {args.interface}")
    print(f"지속 시간: {args.duration}초")
    print("=" * 40)
    
    # 캡처 시작
    capture = SrsUEPacketCapture()
    
    try:
        # 패킷 캡처
        if capture.start_capture(args.duration):
            capture.stop_capture()
            
            # 패킷 분석
            analysis_result = capture.analyze_packets()
            
            if analysis_result:
                # 결과 저장
                output_file = capture.save_analysis(analysis_result)
                
                if output_file:
                    print(f"\n=== 캡처 완료 ===")
                    print(f"총 패킷 수: {analysis_result['analysis_info']['total_packets']}")
                    print(f"분석 파일: {output_file}")
                    print(f"원본 캡처: {capture.capture_file}")
                    
                    # 패킷 요약 출력
                    if analysis_result["packets"]:
                        print(f"\n=== 패킷 요약 ===")
                        for i, packet in enumerate(analysis_result["packets"][:5]):  # 처음 5개만
                            print(f"패킷 {i+1}:")
                            print(f"  시간: {packet['timestamp']}")
                            print(f"  소스: {packet['src_ip']}:{packet['src_port']}")
                            print(f"  대상: {packet['dst_ip']}:{packet['dst_port']}")
                            print(f"  페이로드: {packet['payload'][:50]}..." if len(packet['payload']) > 50 else f"  페이로드: {packet['payload']}")
                            print()
                    else:
                        print("캡처된 패킷이 없습니다.")
                else:
                    print("분석 결과 저장 실패")
            else:
                print("패킷 분석 실패")
        else:
            print("패킷 캡처 실패")
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 사용자에 의해 중단됨")
        capture.stop_capture()
    except Exception as e:
        print(f"오류 발생: {e}")
        capture.stop_capture()

if __name__ == "__main__":
    main()
