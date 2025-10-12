#!/usr/bin/env python3
"""
RRC Flooding Attack 영향 모니터링 도구
공격 전후 시스템 리소스, srsRAN 로그, 네트워크 트래픽 비교 분석
"""

import subprocess
import time
import json
import os
import threading
from datetime import datetime
import signal
import sys

# psutil이 없으면 기본 모니터링만 수행
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("경고: psutil이 설치되지 않았습니다. 기본 모니터링만 수행합니다.")
    print("설치: pip3 install psutil")

class AttackImpactMonitor:
    """공격 영향 모니터링 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.monitoring = False
        self.monitor_data = {
            'system_resources': [],
            'srsran_logs': [],
            'network_traffic': [],
            'timestamps': []
        }
        
        # srsRAN 프로세스 이름들
        self.srsran_processes = ['srsenb', 'srsue', 'srsepc']
        
        # 모니터링 중단을 위한 시그널 핸들러
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print("\n모니터링을 중단합니다...")
        self.monitoring = False
        
        # 데이터 저장
        if self.monitor_data['system_resources']:
            print("모니터링 데이터를 저장합니다...")
            filename = self.save_monitoring_data()
            print(f"데이터 저장 완료: {filename}")
        
        sys.exit(0)
    
    def get_system_resources(self):
        """시스템 리소스 정보 수집"""
        if not PSUTIL_AVAILABLE:
            return self.get_system_resources_basic()
        
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            
            # srsRAN 프로세스 리소스
            srsran_resources = {}
            for process_name in self.srsran_processes:
                try:
                    # 프로세스 찾기
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                        if process_name in proc.info['name'].lower():
                            srsran_resources[process_name] = {
                                'pid': proc.info['pid'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'memory_mb': proc.info['memory_info'].rss / 1024 / 1024
                            }
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                'disk_percent': disk.percent,
                'srsran_processes': srsran_resources
            }
        except Exception as e:
            print(f"시스템 리소스 수집 오류: {e}")
            return None
    
    def get_system_resources_basic(self):
        """기본 시스템 리소스 정보 수집 (psutil 없이)"""
        try:
            # top 명령어로 CPU 사용률 확인
            cpu_result = subprocess.run(['top', '-bn1'], capture_output=True, text=True)
            cpu_percent = 0.0
            if cpu_result.returncode == 0:
                lines = cpu_result.stdout.split('\n')
                for line in lines:
                    if 'Cpu(s)' in line:
                        # CPU 사용률 파싱
                        parts = line.split(',')
                        for part in parts:
                            if 'us' in part:
                                cpu_percent = float(part.split('%')[0].split()[-1])
                                break
            
            # free 명령어로 메모리 사용률 확인
            memory_result = subprocess.run(['free', '-m'], capture_output=True, text=True)
            memory_percent = 0.0
            memory_available_gb = 0.0
            if memory_result.returncode == 0:
                lines = memory_result.stdout.split('\n')
                if len(lines) > 1:
                    mem_line = lines[1].split()
                    if len(mem_line) >= 7:
                        total_mem = int(mem_line[1])
                        used_mem = int(mem_line[2])
                        available_mem = int(mem_line[6])
                        memory_percent = (used_mem / total_mem) * 100
                        memory_available_gb = available_mem / 1024
            
            # df 명령어로 디스크 사용률 확인
            disk_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            disk_percent = 0.0
            if disk_result.returncode == 0:
                lines = disk_result.stdout.split('\n')
                if len(lines) > 1:
                    disk_line = lines[1].split()
                    if len(disk_line) >= 5:
                        disk_percent = float(disk_line[4].replace('%', ''))
            
            # srsRAN 프로세스 확인
            srsran_resources = {}
            for process_name in self.srsran_processes:
                try:
                    # ps 명령어로 프로세스 확인
                    ps_result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.split('\n')
                        for line in lines:
                            if process_name in line.lower():
                                parts = line.split()
                                if len(parts) >= 11:
                                    pid = int(parts[1])
                                    cpu_percent_proc = float(parts[2])
                                    memory_percent_proc = float(parts[3])
                                    memory_mb = float(parts[5]) / 1024  # KB to MB
                                    
                                    srsran_resources[process_name] = {
                                        'pid': pid,
                                        'cpu_percent': cpu_percent_proc,
                                        'memory_percent': memory_percent_proc,
                                        'memory_mb': memory_mb
                                    }
                                    break
                except Exception as e:
                    print(f"프로세스 {process_name} 확인 오류: {e}")
                    continue
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_gb': memory_available_gb,
                'disk_percent': disk_percent,
                'srsran_processes': srsran_resources
            }
        except Exception as e:
            print(f"기본 시스템 리소스 수집 오류: {e}")
            return None
    
    def get_srsran_logs(self):
        """srsRAN 로그 정보 수집"""
        try:
            log_info = {}
            
            # 일반적인 srsRAN 로그 파일 위치들
            log_paths = [
                '/tmp/srsenb.log',
                '/tmp/srsue.log',
                '/tmp/srsepc.log',
                '/var/log/srsran/enb.log',
                '/var/log/srsran/ue.log',
                '/var/log/srsran/epc.log'
            ]
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    try:
                        # 파일 크기
                        file_size = os.path.getsize(log_path)
                        
                        # 최근 로그 라인들 (마지막 10줄)
                        with open(log_path, 'r') as f:
                            lines = f.readlines()
                            recent_lines = lines[-10:] if len(lines) > 10 else lines
                        
                        log_info[log_path] = {
                            'size_bytes': file_size,
                            'recent_lines': [line.strip() for line in recent_lines]
                        }
                    except Exception as e:
                        print(f"로그 파일 읽기 오류 {log_path}: {e}")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'logs': log_info
            }
        except Exception as e:
            print(f"srsRAN 로그 수집 오류: {e}")
            return None
    
    def get_network_traffic(self):
        """네트워크 트래픽 정보 수집"""
        try:
            # 네트워크 인터페이스 통계
            net_io = psutil.net_io_counters()
            
            # 특정 포트 트래픽 (2000, 2001)
            port_traffic = {}
            try:
                # netstat으로 포트별 연결 수 확인
                result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ':2000' in line or ':2001' in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                port = parts[1].split(':')[-1]
                                state = parts[-1] if parts[-1] in ['ESTABLISHED', 'LISTEN', 'TIME_WAIT'] else 'UNKNOWN'
                                if port not in port_traffic:
                                    port_traffic[port] = {}
                                if state not in port_traffic[port]:
                                    port_traffic[port][state] = 0
                                port_traffic[port][state] += 1
            except Exception as e:
                print(f"포트 트래픽 확인 오류: {e}")
            
            return {
                'timestamp': datetime.now().isoformat(),
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'port_connections': port_traffic
            }
        except Exception as e:
            print(f"네트워크 트래픽 수집 오류: {e}")
            return None
    
    def collect_monitoring_data(self):
        """모니터링 데이터 수집"""
        timestamp = datetime.now()
        
        # 시스템 리소스
        system_data = self.get_system_resources()
        if system_data:
            self.monitor_data['system_resources'].append(system_data)
        
        # srsRAN 로그
        log_data = self.get_srsran_logs()
        if log_data:
            self.monitor_data['srsran_logs'].append(log_data)
        
        # 네트워크 트래픽
        network_data = self.get_network_traffic()
        if network_data:
            self.monitor_data['network_traffic'].append(network_data)
        
        self.monitor_data['timestamps'].append(timestamp.isoformat())
        
        print(f"[{timestamp.strftime('%H:%M:%S')}] 모니터링 데이터 수집 완료")
    
    def start_monitoring(self, duration=300, interval=5):
        """모니터링 시작"""
        print(f"=== 공격 영향 모니터링 시작 ===")
        print(f"지속 시간: {duration}초")
        print(f"수집 간격: {interval}초")
        print("=" * 50)
        
        self.monitoring = True
        start_time = time.time()
        
        try:
            while self.monitoring and (time.time() - start_time) < duration:
                self.collect_monitoring_data()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n모니터링이 중단되었습니다.")
        finally:
            self.monitoring = False
            
            # 데이터 저장
            if self.monitor_data['system_resources']:
                print("모니터링 데이터를 저장합니다...")
                filename = self.save_monitoring_data()
                print(f"데이터 저장 완료: {filename}")
        
        print("모니터링 완료")
        return self.monitor_data
    
    def save_monitoring_data(self, filename=None):
        """모니터링 데이터 저장"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.log_dir}/monitoring_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.monitor_data, f, indent=2, ensure_ascii=False)
        
        print(f"모니터링 데이터 저장: {filename}")
        return filename
    
    def analyze_monitoring_data(self):
        """모니터링 데이터 분석"""
        if not self.monitor_data['system_resources']:
            print("분석할 데이터가 없습니다.")
            return
        
        print("=== 모니터링 데이터 분석 ===")
        
        # 시스템 리소스 분석
        system_data = self.monitor_data['system_resources']
        if system_data:
            print("\n시스템 리소스 변화:")
            
            # CPU 사용률
            cpu_values = [d['cpu_percent'] for d in system_data]
            print(f"  CPU 사용률: {min(cpu_values):.1f}% ~ {max(cpu_values):.1f}% (평균: {sum(cpu_values)/len(cpu_values):.1f}%)")
            
            # 메모리 사용률
            memory_values = [d['memory_percent'] for d in system_data]
            print(f"  메모리 사용률: {min(memory_values):.1f}% ~ {max(memory_values):.1f}% (평균: {sum(memory_values)/len(memory_values):.1f}%)")
            
            # srsRAN 프로세스 리소스
            for process_name in self.srsran_processes:
                process_data = []
                for d in system_data:
                    if process_name in d['srsran_processes']:
                        process_data.append(d['srsran_processes'][process_name])
                
                if process_data:
                    cpu_values = [p['cpu_percent'] for p in process_data]
                    memory_values = [p['memory_percent'] for p in process_data]
                    print(f"  {process_name} CPU: {min(cpu_values):.1f}% ~ {max(cpu_values):.1f}%")
                    print(f"  {process_name} 메모리: {min(memory_values):.1f}% ~ {max(memory_values):.1f}%")
        
        # 네트워크 트래픽 분석
        network_data = self.monitor_data['network_traffic']
        if network_data:
            print("\n네트워크 트래픽 변화:")
            
            # 첫 번째와 마지막 데이터 비교
            first = network_data[0]
            last = network_data[-1]
            
            bytes_sent_diff = last['bytes_sent'] - first['bytes_sent']
            bytes_recv_diff = last['bytes_recv'] - first['bytes_recv']
            packets_sent_diff = last['packets_sent'] - first['packets_sent']
            packets_recv_diff = last['packets_recv'] - first['packets_recv']
            
            print(f"  전송 바이트: {bytes_sent_diff:,} bytes")
            print(f"  수신 바이트: {bytes_recv_diff:,} bytes")
            print(f"  전송 패킷: {packets_sent_diff:,} packets")
            print(f"  수신 패킷: {packets_recv_diff:,} packets")
            
            # 포트별 연결 수
            if 'port_connections' in last:
                print("  포트별 연결 수:")
                for port, connections in last['port_connections'].items():
                    total_connections = sum(connections.values())
                    print(f"    포트 {port}: {total_connections}개 연결")
    
    def run_comprehensive_monitoring(self, duration=300):
        """종합 모니터링 실행"""
        print("=== 종합 모니터링 시작 ===")
        print("공격 전후 시스템 상태를 모니터링합니다.")
        print("Ctrl+C로 중단할 수 있습니다.")
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
    
    parser = argparse.ArgumentParser(description='RRC Flooding Attack 영향 모니터링')
    parser.add_argument('--duration', type=int, default=300, help='모니터링 지속 시간 (초)')
    parser.add_argument('--interval', type=int, default=5, help='데이터 수집 간격 (초)')
    
    args = parser.parse_args()
    
    monitor = AttackImpactMonitor()
    monitor.run_comprehensive_monitoring(args.duration)

if __name__ == "__main__":
    main()
