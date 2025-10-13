#!/usr/bin/env python3
"""
UE가 eNB에게 보내는 패킷 캡처 및 분석
실제 srsUE의 RRC 메시지를 캡처하여 형식을 분석합니다.
"""

import subprocess
import json
import time
import signal
import sys
import os
from datetime import datetime

class UEPacketCapture:
    def __init__(self):
        self.capture_process = None
        self.capture_file = None
        
    def start_capture(self, duration=60):
        """패킷 캡처 시작"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.capture_file = f"/tmp/ue_packets_{timestamp}.pcap"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] UE 패킷 캡처 시작...")
        print(f"캡처 파일: {self.capture_file}")
        print(f"지속 시간: {duration}초")
        print("=" * 50)
        
        # tcpdump 명령어 - 루프백 인터페이스에서 srsRAN 포트 캡처
        cmd = [
            "sudo", "tcpdump",
            "-i", "lo",  # 루프백 인터페이스
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
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 캡처 프로세스 시작됨 (PID: {self.capture_process.pid})")
            print("srsUE를 실행하여 RRC 메시지를 생성하세요...")
            
            # 지정된 시간 동안 캡처
            time.sleep(duration)
            
            return True
            
        except Exception as e:
            print(f"캡처 시작 오류: {e}")
            return False
    
    def stop_capture(self):
        """패킷 캡처 중지"""
        if self.capture_process:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 캡처 중지 중...")
            
            # 프로세스 종료
            self.capture_process.terminate()
            
            # 5초 대기 후 강제 종료
            try:
                self.capture_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.capture_process.kill()
                self.capture_process.wait()
            
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
                        "description": "UE RRC 메시지 분석 결과"
                    },
                    "rrc_messages": [],
                    "all_packets": []
                }
                
                for packet in packets_data:
                    packet_info = packet.get("_source", {}).get("layers", {})
                    
                    packet_data = {
                        "timestamp": packet_info.get("frame.time", [""])[0],
                        "src_ip": packet_info.get("ip.src", [""])[0],
                        "dst_ip": packet_info.get("ip.dst", [""])[0],
                        "src_port": packet_info.get("tcp.srcport", [""])[0],
                        "dst_port": packet_info.get("tcp.dstport", [""])[0],
                        "payload": packet_info.get("tcp.payload", [""])[0]
                    }
                    
                    # UDP 페이로드도 확인
                    if not packet_data["payload"]:
                        packet_data["payload"] = packet_info.get("udp.payload", [""])[0]
                    
                    analysis_result["all_packets"].append(packet_data)
                    
                    # RRC 메시지 필터링 (페이로드가 있는 패킷)
                    if packet_data["payload"] and len(packet_data["payload"]) > 0:
                        analysis_result["rrc_messages"].append(packet_data)
                
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
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S in")
        output_file = f"ue_packet_analysis_{timestamp}.json"
        
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
import (
	"disCall/services"
    import argparse
    
    parser = argparse.ArgumentParser(description="UE RRC 메시지 캡처 및 분석")
    parser.add_argument("--duration", type=int, default=60, help="캡처 지속 시간 (초)")
    parser.add_argument("--analyze", help="기존 캡처 파일 분석")
    
    args = parser.parse_args()
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=== UE RRC 메시지 캡처 및 분석 ===")
    
    # 기존 파일 분석 모드
    if args.analyze:
        print(f"분석할 파일: {args.analyze}")
        print("=" * 50)
        
        capture = UEPacketCapture()
        capture.capture_file = args.analyze
        
        try:
            # 패킷 분석
            analysis_result = capture.analyze_packets()
            
            if analysis_result:
                # 결과 저장
                output_file = capture.save_analysis(analysis_result)
                
                if output_file:
                    print(f"\n=== 분석 완료 ===")
                    print(f"총 패킷 수: {analysis_result['analysis_info']['total_packets']}")
                    print(f"RRC 메시지 수: {len(analysis_result['rrc_messages'])}")
                    print(f"분석 파일: {output_file}")
                    
                    # RRC 메시지 요약 출력
                    if analysis_result["rrc_messages"]:
                        print(f"\n=== RRC 메시지 요약 ===")
                        for i, msg in enumerate(analysis_result["rrc_messages"][:10]):  # 처음 10개
                            print(f"메시지 {i+1}:")
                            print(f"  시간: {msg['timestamp']}")
                            print(f"  소스: {msg['src_ip']}:{msg['src_port']}")
                            print(f"  대상: {msg['dst_ip']}:{msg['dst_port']}")
                            print(f"  페이로드: {msg['payload'][:100]}..." if len(msg['payload']) > 100 else f"  페이로드: {msg['payload']}")
                            print()
                    else:
                        print("RRC 메시지가 캡처되지 않았습니다.")
                else:
                    print("분석 결과 저장 실패")
            else:
                print("패킷 분석 실패")
        except Exception as e:
            print(f"분석 오류: {e}")
        
        return
    
    print(f"지속 시간: {args.duration}초")
    print("=" * 50)
    
    # 캡처 시작
    capture = UEPacketCapture()
    
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
                    print(f"RRC 메시지 수: {len(analysis_result['rrc_messages'])}")
                    print(f"분석 파일: {output_file}")
                    print(f"원본 캡처: {capture.capture_file}")
                    
                    # RRC 메시지 요약 출력
                    if analysis_result["rrc_messages"]:
                        print(f"\n=== RRC 메시지 요약 ===")
                        for i, msg in enumerate(analysis_result["rrc_messages"][:5]):  # 처음 5개만
                            print(f"메시지 {i+1}:")
                            print(f"  시간: {msg['timestamp']}")
                            print(f"  소스: {msg['src_ip']}:{msg['src_port']}")
                            print(f"  대상: {msg['dst_ip']}:{msg['dst_port']}")
                            print(f"  페이로드: {msg['payload'][:100]}..." if len(msg['payload']) > 100 else f"  페이로드: {msg['payload']}")
                            print()
                    else:
                        print("RRC 메시지가 캡처되지 않았습니다.")
                        print("srsUE가 실행되지 않았거나 연결에 실패했을 수 있습니다.")
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
