#!/usr/bin/env python3
"""
srsRAN RRC Connection Request 핸들링 모니터링 도구
srsRAN eNB에서 RRC 메시지가 어떻게 처리되는지 실시간으로 모니터링
"""

import zmq
import json
import time
import threading
import psutil
import subprocess
import os
from datetime import datetime
import argparse

class SRSRANRRCMonitor:
    def __init__(self, zmq_tx_port=2001, zmq_rx_port=2000):
        """
        srsRAN RRC 모니터링 클래스
        
        Args:
            zmq_tx_port: UE에서 eNB로 전송하는 포트
            zmq_rx_port: eNB에서 UE로 수신하는 포트
        """
        self.zmq_tx_port = zmq_tx_port
        self.zmq_rx_port = zmq_rx_port
        self.context = zmq.Context()
        self.running = False
        
        # 모니터링 데이터
        self.message_log = []
        self.processing_times = []
        self.resource_usage = []
        
        # srsRAN 프로세스 찾기
        self.srsran_processes = self.find_srsran_processes()
        
    def find_srsran_processes(self):
        """srsRAN 프로세스 찾기"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and any(name in proc.info['name'].lower() 
                                           for name in ['srsenb', 'srsue', 'srsepc']):
                    processes.append(proc)
                    print(f"srsRAN 프로세스 발견: {proc.info['name']} (PID: {proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes
    
    def monitor_srsran_logs(self):
        """srsRAN 로그 파일 모니터링"""
        log_files = [
            '/tmp/enb.log',
            '/tmp/ue.log',
            '/tmp/epc.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"로그 파일 모니터링: {log_file}")
                try:
                    # tail -f 명령으로 실시간 로그 모니터링
                    process = subprocess.Popen(
                        ['tail', '-f', log_file],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1
                    )
                    
                    while self.running:
                        line = process.stdout.readline()
                        if line:
                            self.parse_log_line(line.strip(), log_file)
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"로그 모니터링 오류 ({log_file}): {e}")
    
    def parse_log_line(self, line, log_file):
        """로그 라인 파싱하여 RRC 메시지 추출"""
        if not line:
            return
            
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # RRC 관련 키워드 검색
        rrc_keywords = [
            'RRCConnectionRequest',
            'RRCConnectionSetup',
            'RRCConnectionSetupComplete',
            'RRCConnectionReject',
            'RRCConnectionRelease',
            'rrc_connection_request',
            'rrc_connection_setup',
            'rrc_connection_setup_complete'
        ]
        
        for keyword in rrc_keywords:
            if keyword.lower() in line.lower():
                log_entry = {
                    'timestamp': timestamp,
                    'log_file': log_file,
                    'message': line,
                    'keyword': keyword
                }
                
                self.message_log.append(log_entry)
                print(f"[{timestamp}] {log_file}: {keyword} - {line}")
                
                # 처리 시간 측정
                if 'request' in keyword.lower():
                    self.processing_times.append({
                        'timestamp': datetime.now(),
                        'message_type': keyword,
                        'start_time': time.time()
                    })
                elif 'setup' in keyword.lower() or 'complete' in keyword.lower():
                    # 가장 최근 request와 매칭
                    if self.processing_times:
                        last_request = self.processing_times[-1]
                        if 'request' in last_request['message_type'].lower():
                            processing_time = (time.time() - last_request['start_time']) * 1000
                            print(f"처리 시간: {processing_time:.2f}ms")
                            last_request['processing_time'] = processing_time
                            last_request['end_time'] = time.time()
    
    def monitor_zeromq_traffic(self):
        """ZeroMQ 트래픽 모니터링"""
        try:
            # ZeroMQ 소켓으로 메시지 수신
            rx_socket = self.context.socket(zmq.PULL)
            rx_socket.connect(f"tcp://localhost:{self.zmq_rx_port}")
            
            while self.running:
                try:
                    # ZeroMQ 메시지 수신
                    message = rx_socket.recv(zmq.NOBLOCK)
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"[{timestamp}] ZeroMQ 메시지 수신: {len(message)} bytes")
                    
                    # 메시지 내용 분석 (바이너리 데이터)
                    if len(message) > 0:
                        hex_data = message.hex()[:100]  # 처음 50바이트만 표시
                        print(f"  데이터: {hex_data}...")
                        
                except zmq.Again:
                    pass
                except Exception as e:
                    print(f"ZeroMQ 모니터링 오류: {e}")
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"ZeroMQ 모니터링 설정 오류: {e}")
    
    def monitor_resource_usage(self):
        """리소스 사용량 모니터링"""
        while self.running:
            try:
                # srsRAN 프로세스 리소스 사용량
                srsran_cpu = 0
                srsran_memory = 0
                
                for proc in self.srsran_processes:
                    try:
                        if proc.is_running():
                            srsran_cpu += proc.cpu_percent()
                            srsran_memory += proc.memory_percent()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                # 시스템 리소스
                system_cpu = psutil.cpu_percent()
                system_memory = psutil.virtual_memory().percent
                
                resource_data = {
                    'timestamp': datetime.now(),
                    'system_cpu': system_cpu,
                    'system_memory': system_memory,
                    'srsran_cpu': srsran_cpu,
                    'srsran_memory': srsran_memory
                }
                
                self.resource_usage.append(resource_data)
                
                # 실시간 출력
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"시스템 CPU: {system_cpu:5.1f}% | "
                      f"시스템 Memory: {system_memory:5.1f}% | "
                      f"srsRAN CPU: {srsran_cpu:5.1f}% | "
                      f"srsRAN Memory: {srsran_memory:5.1f}%")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"리소스 모니터링 오류: {e}")
                time.sleep(2)
    
    def send_test_rrc_request(self):
        """테스트용 RRC Connection Request 전송"""
        try:
            tx_socket = self.context.socket(zmq.PUSH)
            tx_socket.bind(f"tcp://*:{self.zmq_tx_port}")
            
            # 간단한 RRC Connection Request 메시지 생성
            test_message = b'\x00\x01\x00\x00\x00\x00\x00\x01'  # 테스트용 바이너리 데이터
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 테스트 RRC 메시지 전송")
            tx_socket.send(test_message, zmq.NOBLOCK)
            
            tx_socket.close()
            
        except Exception as e:
            print(f"테스트 메시지 전송 오류: {e}")
    
    def start_monitoring(self, duration=300):
        """모니터링 시작"""
        print(f"=== srsRAN RRC 핸들링 모니터링 시작 ===")
        print(f"모니터링 지속 시간: {duration}초")
        print(f"ZeroMQ 포트: TX={self.zmq_tx_port}, RX={self.zmq_rx_port}")
        print(f"시작 시간: {datetime.now()}")
        print("=" * 60)
        
        self.running = True
        
        # 모니터링 스레드들 시작
        threads = []
        
        # 로그 모니터링 스레드
        log_thread = threading.Thread(target=self.monitor_srsran_logs)
        log_thread.daemon = True
        log_thread.start()
        threads.append(log_thread)
        
        # ZeroMQ 트래픽 모니터링 스레드
        zmq_thread = threading.Thread(target=self.monitor_zeromq_traffic)
        zmq_thread.daemon = True
        zmq_thread.start()
        threads.append(zmq_thread)
        
        # 리소스 사용량 모니터링 스레드
        resource_thread = threading.Thread(target=self.monitor_resource_usage)
        resource_thread.daemon = True
        resource_thread.start()
        threads.append(resource_thread)
        
        # 주기적으로 테스트 메시지 전송
        test_thread = threading.Thread(target=self.send_periodic_tests, args=(duration,))
        test_thread.daemon = True
        test_thread.start()
        threads.append(test_thread)
        
        # 모니터링 지속 시간 대기
        time.sleep(duration)
        self.stop_monitoring()
    
    def send_periodic_tests(self, duration):
        """주기적으로 테스트 메시지 전송"""
        start_time = time.time()
        test_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            time.sleep(10)  # 10초마다 테스트 메시지 전송
            test_count += 1
            print(f"\n--- 테스트 메시지 #{test_count} 전송 ---")
            self.send_test_rrc_request()
    
    def stop_monitoring(self):
        """모니터링 중지 및 결과 출력"""
        print("\n=== 모니터링 중지 ===")
        self.running = False
        
        # 결과 리포트
        self.generate_monitoring_report()
        
        # ZeroMQ 정리
        self.context.term()
    
    def generate_monitoring_report(self):
        """모니터링 결과 리포트 생성"""
        print(f"\n=== srsRAN RRC 핸들링 모니터링 결과 ===")
        
        # 메시지 로그 통계
        print(f"\nRRC 메시지 로그:")
        print(f"  총 로그 엔트리: {len(self.message_log)}개")
        
        # 키워드별 통계
        keyword_counts = {}
        for entry in self.message_log:
            keyword = entry['keyword']
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        for keyword, count in keyword_counts.items():
            print(f"  {keyword}: {count}개")
        
        # 처리 시간 통계
        processing_times = [pt['processing_time'] for pt in self.processing_times 
                          if 'processing_time' in pt]
        
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            
            print(f"\nRRC 메시지 처리 시간:")
            print(f"  평균: {avg_time:.2f}ms")
            print(f"  최대: {max_time:.2f}ms")
            print(f"  최소: {min_time:.2f}ms")
            print(f"  샘플 수: {len(processing_times)}")
        
        # 리소스 사용량 통계
        if self.resource_usage:
            srsran_cpu_values = [data['srsran_cpu'] for data in self.resource_usage]
            srsran_memory_values = [data['srsran_memory'] for data in self.resource_usage]
            
            if srsran_cpu_values:
                avg_cpu = sum(srsran_cpu_values) / len(srsran_cpu_values)
                max_cpu = max(srsran_cpu_values)
                print(f"\nsrsRAN 리소스 사용량:")
                print(f"  CPU 평균: {avg_cpu:.1f}%")
                print(f"  CPU 최대: {max_cpu:.1f}%")
            
            if srsran_memory_values:
                avg_memory = sum(srsran_memory_values) / len(srsran_memory_values)
                max_memory = max(srsran_memory_values)
                print(f"  Memory 평균: {avg_memory:.1f}%")
                print(f"  Memory 최대: {max_memory:.1f}%")
        
        print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description='srsRAN RRC Connection Request 핸들링 모니터링')
    parser.add_argument('--duration', type=int, default=300, help='모니터링 지속 시간 (초)')
    parser.add_argument('--zmq-tx-port', type=int, default=2001, help='ZeroMQ TX 포트')
    parser.add_argument('--zmq-rx-port', type=int, default=2000, help='ZeroMQ RX 포트')
    
    args = parser.parse_args()
    
    monitor = SRSRANRRCMonitor(args.zmq_tx_port, args.zmq_rx_port)
    
    try:
        monitor.start_monitoring(args.duration)
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
