#!/usr/bin/env python3
"""
RRC 연결 흐름 실시간 모니터링
srsRAN eNB, EPC, UE 간의 RRC 메시지 교환 모니터링
"""

import subprocess
import time
import json
import os
import threading
from datetime import datetime
import signal
import sys

class RRCFlowMonitor:
    """RRC 연결 흐름 모니터링 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.monitoring = False
        self.monitor_data = {
            'enb_logs': [],
            'epc_logs': [],
            'network_traffic': [],
            'timestamps': []
        }
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print("\n모니터링을 중단합니다...")
        self.monitoring = False
        sys.exit(0)
    
    def monitor_enb_logs(self):
        """eNB 로그 모니터링"""
        print("=== eNB 로그 모니터링 시작 ===")
        
        log_files = [
            '/var/log/syslog',
            '/var/log/messages'
        ]
        
        while self.monitoring:
            timestamp = datetime.now()
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # 파일 크기 확인
                        file_size = os.path.getsize(log_file)
                        
                        # 최근 로그 라인들
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-5:] if len(lines) > 5 else lines
                        
                        # RRC 관련 로그 필터링
                        rrc_lines = []
                        for line in recent_lines:
                            if any(keyword in line.lower() for keyword in [
                                'rrc', 'connection', 'request', 'setup', 'complete', 
                                'ue', 'attach', 'detach', 'bearer'
                            ]):
                                rrc_lines.append(line.strip())
                        
                        if rrc_lines:
                            self.monitor_data['enb_logs'].append({
                                'timestamp': timestamp.isoformat(),
                                'file': log_file,
                                'size': file_size,
                                'rrc_lines': rrc_lines
                            })
                            
                            print(f"[{timestamp.strftime('%H:%M:%S')}] eNB RRC 로그:")
                            for line in rrc_lines:
                                print(f"  {line}")
                        
                    except Exception as e:
                        print(f"eNB 로그 읽기 오류 {log_file}: {e}")
            
            time.sleep(3)  # 3초마다 확인
    
    def monitor_epc_logs(self):
        """EPC 로그 모니터링"""
        print("=== EPC 로그 모니터링 시작 ===")
        
        log_files = [
            '/var/log/syslog',
            '/var/log/messages'
        ]
        
        while self.monitoring:
            timestamp = datetime.now()
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        # 파일 크기 확인
                        file_size = os.path.getsize(log_file)
                        
                        # 최근 로그 라인들
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-5:] if len(lines) > 5 else lines
                        
                        # EPC 관련 로그 필터링
                        epc_lines = []
                        for line in recent_lines:
                            if any(keyword in line.lower() for keyword in [
                                'epc', 'mme', 'sgw', 'pgw', 's1ap', 'gtp', 
                                'attach', 'detach', 'bearer', 'session'
                            ]):
                                epc_lines.append(line.strip())
                        
                        if epc_lines:
                            self.monitor_data['epc_logs'].append({
                                'timestamp': timestamp.isoformat(),
                                'file': log_file,
                                'size': file_size,
                                'epc_lines': epc_lines
                            })
                            
                            print(f"[{timestamp.strftime('%H:%M:%S')}] EPC 로그:")
                            for line in epc_lines:
                                print(f"  {line}")
                        
                    except Exception as e:
                        print(f"EPC 로그 읽기 오류 {log_file}: {e}")
            
            time.sleep(3)  # 3초마다 확인
    
    def monitor_network_traffic(self):
        """네트워크 트래픽 모니터링"""
        print("=== 네트워크 트래픽 모니터링 시작 ===")
        
        while self.monitoring:
            timestamp = datetime.now()
            
            try:
                # netstat으로 연결 상태 확인
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    
                    # srsRAN 관련 포트 확인
                    srsran_connections = []
                    for line in lines:
                        if any(port in line for port in ['2000', '2001', '36412', '36413', '8080']):
                            srsran_connections.append(line.strip())
                    
                    if srsran_connections:
                        self.monitor_data['network_traffic'].append({
                            'timestamp': timestamp.isoformat(),
                            'connections': srsran_connections
                        })
                        
                        print(f"[{timestamp.strftime('%H:%M:%S')}] 네트워크 연결:")
                        for conn in srsran_connections:
                            print(f"  {conn}")
                
            except Exception as e:
                print(f"네트워크 트래픽 확인 오류: {e}")
            
            time.sleep(5)  # 5초마다 확인
    
    def start_monitoring(self, duration=300):
        """모니터링 시작"""
        print(f"=== RRC 연결 흐름 모니터링 시작 ===")
        print(f"지속 시간: {duration}초")
        print("Ctrl+C로 중단할 수 있습니다.")
        print("=" * 50)
        
        self.monitoring = True
        start_time = time.time()
        
        # 모니터링 스레드들 시작
        threads = []
        
        # eNB 로그 모니터링 스레드
        enb_thread = threading.Thread(target=self.monitor_enb_logs)
        enb_thread.daemon = True
        enb_thread.start()
        threads.append(enb_thread)
        
        # EPC 로그 모니터링 스레드
        epc_thread = threading.Thread(target=self.monitor_epc_logs)
        epc_thread.daemon = True
        epc_thread.start()
        threads.append(epc_thread)
        
        # 네트워크 트래픽 모니터링 스레드
        traffic_thread = threading.Thread(target=self.monitor_network_traffic)
        traffic_thread.daemon = True
        traffic_thread.start()
        threads.append(traffic_thread)
        
        try:
            while self.monitoring and (time.time() - start_time) < duration:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n모니터링이 중단되었습니다.")
        finally:
            self.monitoring = False
        
        # 모든 스레드 종료 대기
        for thread in threads:
            thread.join(timeout=5)
        
        print("모니터링 완료")
        return self.monitor_data
    
    def save_monitoring_data(self, filename=None):
        """모니터링 데이터 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.log_dir}/rrc_flow_monitor_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.monitor_data, f, indent=2, ensure_ascii=False)
        
        print(f"모니터링 데이터 저장: {filename}")
        return filename
    
    def analyze_monitoring_data(self):
        """모니터링 데이터 분석"""
        print("=== RRC 연결 흐름 분석 ===")
        
        # eNB 로그 분석
        if self.monitor_data['enb_logs']:
            print(f"\neNB RRC 로그: {len(self.monitor_data['enb_logs'])}개 이벤트")
            
            # RRC 메시지 타입별 카운트
            rrc_messages = {}
            for log_entry in self.monitor_data['enb_logs']:
                for line in log_entry['rrc_lines']:
                    if 'connection request' in line.lower():
                        rrc_messages['connection_request'] = rrc_messages.get('connection_request', 0) + 1
                    elif 'connection setup' in line.lower():
                        rrc_messages['connection_setup'] = rrc_messages.get('connection_setup', 0) + 1
                    elif 'connection complete' in line.lower():
                        rrc_messages['connection_complete'] = rrc_messages.get('connection_complete', 0) + 1
            
            if rrc_messages:
                print("RRC 메시지 통계:")
                for msg_type, count in rrc_messages.items():
                    print(f"  {msg_type}: {count}개")
        
        # EPC 로그 분석
        if self.monitor_data['epc_logs']:
            print(f"\nEPC 로그: {len(self.monitor_data['epc_logs'])}개 이벤트")
        
        # 네트워크 트래픽 분석
        if self.monitor_data['network_traffic']:
            print(f"\n네트워크 연결: {len(self.monitor_data['network_traffic'])}개 이벤트")
            
            # 연결 타입별 카운트
            connection_types = {}
            for traffic_entry in self.monitor_data['network_traffic']:
                for conn in traffic_entry['connections']:
                    if '2000' in conn:
                        connection_types['port_2000'] = connection_types.get('port_2000', 0) + 1
                    elif '2001' in conn:
                        connection_types['port_2001'] = connection_types.get('port_2001', 0) + 1
                    elif '36412' in conn:
                        connection_types['s1ap'] = connection_types.get('s1ap', 0) + 1
            
            if connection_types:
                print("연결 타입 통계:")
                for conn_type, count in connection_types.items():
                    print(f"  {conn_type}: {count}개")
    
    def run_comprehensive_monitoring(self, duration=300):
        """종합 모니터링 실행"""
        print("=== RRC 연결 흐름 종합 모니터링 ===")
        print("srsRAN eNB, EPC, UE 간의 RRC 메시지 교환을 모니터링합니다.")
        print()
        
        # 모니터링 시작
        self.start_monitoring(duration)
        
        # 데이터 저장
        filename = self.save_monitoring_data()
        
        # 데이터 분석
        self.analyze_monitoring_data()
        
        return filename

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='RRC 연결 흐름 모니터링')
    parser.add_argument('--duration', type=int, default=300, help='모니터링 지속 시간 (초)')
    
    args = parser.parse_args()
    
    monitor = RRCFlowMonitor()
    monitor.run_comprehensive_monitoring(args.duration)

if __name__ == "__main__":
    main()
