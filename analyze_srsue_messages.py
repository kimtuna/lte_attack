#!/usr/bin/env python3
"""
srsUE 메시지 분석 도구
srsUE가 실제로 보내는 RRC 메시지를 캡처하고 분석
"""

import subprocess
import time
import json
import os
import threading
from datetime import datetime
import signal
import sys

class SrsUEMessageAnalyzer:
    """srsUE 메시지 분석 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.monitoring = False
        self.captured_messages = []
        self.srsue_process = None
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print("\n분석을 중단합니다...")
        self.monitoring = False
        if self.srsue_process:
            self.srsue_process.terminate()
        sys.exit(0)
    
    def start_packet_capture(self, duration=60):
        """패킷 캡처 시작"""
        print(f"=== 패킷 캡처 시작 ({duration}초) ===")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        capture_file = f"/tmp/srsue_capture_{timestamp}.pcap"
        
        try:
            # tcpdump로 패킷 캡처
            cmd = [
                'sudo', 'tcpdump',
                '-i', 'lo',  # localhost 인터페이스
                '-w', capture_file,
                'port', '2000', 'or', 'port', '2001'  # srsRAN 포트들
            ]
            
            print(f"캡처 파일: {capture_file}")
            print("패킷 캡처 중...")
            
            # 백그라운드에서 tcpdump 실행
            capture_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 지정된 시간 동안 캡처
            time.sleep(duration)
            
            # tcpdump 종료
            capture_process.terminate()
            capture_process.wait(timeout=10)
            
            print(f"패킷 캡처 완료: {capture_file}")
            return capture_file
            
        except Exception as e:
            print(f"패킷 캡처 오류: {e}")
            return None
    
    def analyze_captured_packets(self, capture_file):
        """캡처된 패킷 분석"""
        if not os.path.exists(capture_file):
            print(f"캡처 파일이 없습니다: {capture_file}")
            return False
        
        print(f"\n=== 캡처된 패킷 분석 ===")
        
        try:
            # tshark로 패킷 분석
            cmd = [
                'tshark',
                '-r', capture_file,
                '-T', 'fields',
                '-e', 'frame.time',
                '-e', 'ip.src',
                '-e', 'ip.dst',
                '-e', 'tcp.srcport',
                '-e', 'tcp.dstport',
                '-e', 'tcp.len',
                '-e', 'data'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            
            if not lines or not lines[0]:
                print("분석된 패킷이 없습니다.")
                return False
            
            print(f"총 {len(lines)}개 패킷 분석")
            
            # srsUE → eNB 방향 패킷만 필터링
            ue_to_enb_packets = []
            for line in lines:
                parts = line.split('\t')
                if len(parts) >= 7:
                    timestamp, ip_src, ip_dst, src_port, dst_port, tcp_len, data = parts
                    
                    # 포트 2000 또는 2001과 관련된 패킷
                    if dst_port in ["2000", "2001"]:
                        direction = "UE→eNB"
                        ue_to_enb_packets.append({
                            'timestamp': timestamp,
                            'direction': direction,
                            'src_port': src_port,
                            'dst_port': dst_port,
                            'size': tcp_len,
                            'data': data,
                            'message_hex': data
                        })
            
            if ue_to_enb_packets:
                print(f"srsUE → eNB 패킷 {len(ue_to_enb_packets)}개 발견")
                
                # 패킷 정보 출력
                for i, packet in enumerate(ue_to_enb_packets[:10]):  # 최대 10개만
                    print(f"\n패킷 {i+1}:")
                    print(f"  시간: {packet['timestamp']}")
                    print(f"  방향: {packet['direction']}")
                    print(f"  포트: {packet['src_port']} → {packet['dst_port']}")
                    print(f"  크기: {packet['size']} bytes")
                    print(f"  데이터: {packet['data']}")
                
                self.captured_messages = ue_to_enb_packets
                return True
            else:
                print("srsUE → eNB 패킷이 없습니다.")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"tshark 분석 오류: {e.stderr}")
            return False
        except Exception as e:
            print(f"패킷 분석 오류: {e}")
            return False
    
    def start_srsue(self, duration=30):
        """srsUE 시작"""
        print(f"=== srsUE 시작 ({duration}초) ===")
        
        try:
            # srsUE 명령어
            cmd = ['srsue']
            
            # 백그라운드에서 srsUE 실행
            self.srsue_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"srsUE 프로세스 시작 (PID: {self.srsue_process.pid})")
            
            # 지정된 시간 동안 실행
            time.sleep(duration)
            
            # srsUE 종료
            self.srsue_process.terminate()
            self.srsue_process.wait(timeout=10)
            
            print("srsUE 프로세스 종료")
            
            # 출력 확인
            stdout, stderr = self.srsue_process.communicate()
            
            if stdout:
                print("srsUE STDOUT:")
                print(stdout)
            
            if stderr:
                print("srsUE STDERR:")
                print(stderr)
            
            return True
            
        except Exception as e:
            print(f"srsUE 시작 오류: {e}")
            if self.srsue_process:
                self.srsue_process.terminate()
            return False
    
    def monitor_enb_logs(self, duration=60):
        """eNB 로그 모니터링"""
        print(f"=== eNB 로그 모니터링 ({duration}초) ===")
        
        log_files = [
            '/tmp/srsenb.log',
            '/var/log/syslog'
        ]
        
        log_data = {}
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration:
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # 파일 크기 확인
                        file_size = os.path.getsize(log_file)
                        
                        # 최근 로그 라인들
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-10:] if len(lines) > 10 else lines
                        
                        # RRC 관련 로그 필터링
                        rrc_lines = []
                        for line in recent_lines:
                            if any(keyword in line.lower() for keyword in [
                                'rrc', 'connection', 'request', 'setup', 'complete', 
                                'ue', 'attach', 'detach', 'bearer'
                            ]):
                                rrc_lines.append(line.strip())
                        
                        if rrc_lines:
                            if log_file not in log_data:
                                log_data[log_file] = []
                            
                            log_data[log_file].extend(rrc_lines)
                            
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] eNB RRC 로그:")
                            for line in rrc_lines:
                                print(f"  {line}")
                        
                    except Exception as e:
                        print(f"eNB 로그 읽기 오류 {log_file}: {e}")
            
            time.sleep(2)  # 2초마다 확인
        
        return log_data
    
    def run_comprehensive_analysis(self):
        """종합 srsUE 메시지 분석"""
        print("=== srsUE 메시지 종합 분석 ===")
        print("srsUE가 실제로 보내는 RRC 메시지를 캡처하고 분석")
        print("=" * 50)
        
        # 1. 패킷 캡처 시작
        print("\n=== 패킷 캡처 시작 ===")
        capture_file = self.start_packet_capture(60)
        
        if not capture_file:
            print("패킷 캡처 실패")
            return
        
        # 2. 로그 모니터링 시작
        print("\n=== 로그 모니터링 시작 ===")
        self.monitoring = True
        
        # 로그 모니터링 스레드 시작
        log_monitor_thread = threading.Thread(
            target=self.monitor_enb_logs, 
            args=(60,)
        )
        log_monitor_thread.daemon = True
        log_monitor_thread.start()
        
        # 3. srsUE 시작
        print("\n=== srsUE 연결 테스트 ===")
        ue_success = self.start_srsue(30)
        
        # 4. 로그 모니터링 종료
        self.monitoring = False
        log_monitor_thread.join(timeout=5)
        
        # 5. 패킷 분석
        print("\n=== 패킷 분석 ===")
        packet_analysis_success = self.analyze_captured_packets(capture_file)
        
        # 6. 결과 저장
        self.save_analysis_results(capture_file, ue_success, packet_analysis_success)
        
        # 7. 결과 요약
        self.print_analysis_summary(ue_success, packet_analysis_success)
    
    def save_analysis_results(self, capture_file, ue_success, packet_analysis_success):
        """분석 결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"{self.log_dir}/srsue_message_analysis_{timestamp}.json"
        
        analysis_data = {
            'analysis_info': {
                'timestamp': datetime.now().isoformat(),
                'capture_file': capture_file,
                'description': 'srsUE 메시지 분석 결과'
            },
            'results': {
                'ue_success': ue_success,
                'packet_analysis_success': packet_analysis_success,
                'captured_messages': self.captured_messages
            }
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 분석 결과 저장: {result_file}")
    
    def print_analysis_summary(self, ue_success, packet_analysis_success):
        """분석 결과 요약"""
        print("\n=== 분석 결과 요약 ===")
        
        if ue_success:
            print("✅ srsUE 연결 성공")
        else:
            print("❌ srsUE 연결 실패")
        
        if packet_analysis_success:
            print("✅ 패킷 분석 성공")
            print(f"✅ 캡처된 메시지: {len(self.captured_messages)}개")
            
            if self.captured_messages:
                print("\n캡처된 메시지 예시:")
                for i, message in enumerate(self.captured_messages[:3]):
                    print(f"  메시지 {i+1}: {message['data']}")
        else:
            print("❌ 패킷 분석 실패")
        
        print("\n다음 단계:")
        print("1. 캡처된 메시지를 분석하여 실제 RRC 형식 파악")
        print("2. 분석된 형식으로 직접 TCP 테스트 수정")
        print("3. 수정된 테스트로 eNB 로그 확인")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='srsUE 메시지 분석')
    parser.add_argument('--duration', type=int, default=30, help='srsUE 실행 시간 (초)')
    parser.add_argument('--capture-duration', type=int, default=60, help='패킷 캡처 시간 (초)')
    
    args = parser.parse_args()
    
    analyzer = SrsUEMessageAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()
