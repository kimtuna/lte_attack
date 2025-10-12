#!/usr/bin/env python3
"""
공격 전후 영향 비교 분석 도구
시스템 리소스, srsRAN 로그, 네트워크 트래픽의 변화를 비교
"""

import json
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

class AttackImpactComparator:
    """공격 영향 비교 분석 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        self.monitoring_files = []
        self.flooding_files = []
    
    def load_monitoring_data(self):
        """모니터링 데이터 파일들 로드"""
        if not os.path.exists(self.log_dir):
            print("로그 디렉토리가 없습니다.")
            return
        
        # monitoring_data_*.json 파일들 찾기
        pattern = os.path.join(self.log_dir, "monitoring_data_*.json")
        self.monitoring_files = glob.glob(pattern)
        
        # flooding_attack_*.json 파일들 찾기
        pattern = os.path.join(self.log_dir, "flooding_attack_*.json")
        self.flooding_files = glob.glob(pattern)
        
        print(f"모니터링 파일 {len(self.monitoring_files)}개, 공격 파일 {len(self.flooding_files)}개 로드됨")
    
    def analyze_system_resources(self, monitoring_data):
        """시스템 리소스 분석"""
        if not monitoring_data['system_resources']:
            return None
        
        system_data = monitoring_data['system_resources']
        
        # CPU 사용률
        cpu_values = [d['cpu_percent'] for d in system_data]
        
        # 메모리 사용률
        memory_values = [d['memory_percent'] for d in system_data]
        
        # srsRAN 프로세스 리소스
        srsran_resources = {}
        for process_name in ['srsenb', 'srsue', 'srsepc']:
            process_data = []
            for d in system_data:
                if process_name in d['srsran_processes']:
                    process_data.append(d['srsran_processes'][process_name])
            
            if process_data:
                srsran_resources[process_name] = {
                    'cpu_min': min(p['cpu_percent'] for p in process_data),
                    'cpu_max': max(p['cpu_percent'] for p in process_data),
                    'cpu_avg': sum(p['cpu_percent'] for p in process_data) / len(process_data),
                    'memory_min': min(p['memory_percent'] for p in process_data),
                    'memory_max': max(p['memory_percent'] for p in process_data),
                    'memory_avg': sum(p['memory_percent'] for p in process_data) / len(process_data)
                }
        
        return {
            'cpu': {
                'min': min(cpu_values),
                'max': max(cpu_values),
                'avg': sum(cpu_values) / len(cpu_values)
            },
            'memory': {
                'min': min(memory_values),
                'max': max(memory_values),
                'avg': sum(memory_values) / len(memory_values)
            },
            'srsran_processes': srsran_resources
        }
    
    def analyze_network_traffic(self, monitoring_data):
        """네트워크 트래픽 분석"""
        if not monitoring_data['network_traffic']:
            return None
        
        network_data = monitoring_data['network_traffic']
        
        # 첫 번째와 마지막 데이터 비교
        first = network_data[0]
        last = network_data[-1]
        
        return {
            'bytes_sent_diff': last['bytes_sent'] - first['bytes_sent'],
            'bytes_recv_diff': last['bytes_recv'] - first['bytes_recv'],
            'packets_sent_diff': last['packets_sent'] - first['packets_sent'],
            'packets_recv_diff': last['packets_recv'] - first['packets_recv'],
            'port_connections': last.get('port_connections', {})
        }
    
    def analyze_srsran_logs(self, monitoring_data):
        """srsRAN 로그 분석"""
        if not monitoring_data['srsran_logs']:
            return None
        
        log_data = monitoring_data['srsran_logs']
        
        # 로그 파일별 분석
        log_analysis = {}
        for log_entry in log_data:
            for log_path, log_info in log_entry['logs'].items():
                if log_path not in log_analysis:
                    log_analysis[log_path] = {
                        'size_bytes': log_info['size_bytes'],
                        'recent_lines': log_info['recent_lines']
                    }
        
        return log_analysis
    
    def compare_monitoring_files(self):
        """모니터링 파일들 비교"""
        if len(self.monitoring_files) < 2:
            print("비교할 모니터링 파일이 부족합니다.")
            return
        
        print("=== 모니터링 파일 비교 분석 ===")
        
        # 파일들을 시간순으로 정렬
        sorted_files = sorted(self.monitoring_files)
        
        for i, file_path in enumerate(sorted_files):
            print(f"\n파일 {i+1}: {os.path.basename(file_path)}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 시스템 리소스 분석
                system_analysis = self.analyze_system_resources(data)
                if system_analysis:
                    print("  시스템 리소스:")
                    print(f"    CPU: {system_analysis['cpu']['min']:.1f}% ~ {system_analysis['cpu']['max']:.1f}% (평균: {system_analysis['cpu']['avg']:.1f}%)")
                    print(f"    메모리: {system_analysis['memory']['min']:.1f}% ~ {system_analysis['memory']['max']:.1f}% (평균: {system_analysis['memory']['avg']:.1f}%)")
                    
                    # srsRAN 프로세스 리소스
                    for process_name, process_data in system_analysis['srsran_processes'].items():
                        print(f"    {process_name} CPU: {process_data['cpu_min']:.1f}% ~ {process_data['cpu_max']:.1f}% (평균: {process_data['cpu_avg']:.1f}%)")
                        print(f"    {process_name} 메모리: {process_data['memory_min']:.1f}% ~ {process_data['memory_max']:.1f}% (평균: {process_data['memory_avg']:.1f}%)")
                
                # 네트워크 트래픽 분석
                network_analysis = self.analyze_network_traffic(data)
                if network_analysis:
                    print("  네트워크 트래픽:")
                    print(f"    전송 바이트: {network_analysis['bytes_sent_diff']:,}")
                    print(f"    수신 바이트: {network_analysis['bytes_recv_diff']:,}")
                    print(f"    전송 패킷: {network_analysis['packets_sent_diff']:,}")
                    print(f"    수신 패킷: {network_analysis['packets_recv_diff']:,}")
                    
                    # 포트별 연결 수
                    if network_analysis['port_connections']:
                        print("    포트별 연결 수:")
                        for port, connections in network_analysis['port_connections'].items():
                            total_connections = sum(connections.values())
                            print(f"      포트 {port}: {total_connections}개 연결")
                
            except Exception as e:
                print(f"  파일 분석 오류: {e}")
    
    def correlate_attack_with_impact(self):
        """공격과 영향 상관관계 분석"""
        if not self.monitoring_files or not self.flooding_files:
            print("분석할 파일이 부족합니다.")
            return
        
        print("=== 공격과 영향 상관관계 분석 ===")
        
        # 공격 파일들 분석
        attack_summary = []
        for file_path in self.flooding_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                attack_info = data['attack_info']
                results = data['results']
                
                attack_summary.append({
                    'file': os.path.basename(file_path),
                    'timestamp': results['start_time'],
                    'message_type': attack_info['message_type'],
                    'threads': attack_info['num_threads'],
                    'duration': attack_info['duration'],
                    'messages_per_second': results['messages_per_second'],
                    'total_messages': results['total_messages'],
                    'errors': results['errors']
                })
            except Exception as e:
                print(f"공격 파일 분석 오류 {file_path}: {e}")
        
        # 공격 요약 출력
        print("\n공격 요약:")
        print(f"{'순위':<4} {'메시지타입':<20} {'스레드':<6} {'초당메시지':<12} {'총메시지':<12} {'오류':<6}")
        print("-" * 80)
        
        # 성능순 정렬
        sorted_attacks = sorted(attack_summary, key=lambda x: x['messages_per_second'], reverse=True)
        
        for i, attack in enumerate(sorted_attacks):
            print(f"{i+1:<4} {attack['message_type']:<20} {attack['threads']:<6} "
                  f"{attack['messages_per_second']:<12.2f} {attack['total_messages']:<12,} {attack['errors']:<6}")
        
        # 최고 성능 공격 분석
        if sorted_attacks:
            best_attack = sorted_attacks[0]
            print(f"\n최고 성능 공격:")
            print(f"  메시지 타입: {best_attack['message_type']}")
            print(f"  스레드 수: {best_attack['threads']}")
            print(f"  초당 메시지: {best_attack['messages_per_second']:.2f}")
            print(f"  총 메시지: {best_attack['total_messages']:,}")
            print(f"  오류 수: {best_attack['errors']}")
    
    def generate_comparison_report(self):
        """비교 분석 보고서 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"{self.log_dir}/attack_impact_comparison_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("RRC Flooding Attack 영향 비교 분석 보고서\n")
            f.write("=" * 60 + "\n")
            f.write(f"생성 시간: {datetime.now()}\n")
            f.write(f"분석 대상: {len(self.monitoring_files)}개 모니터링 파일, {len(self.flooding_files)}개 공격 파일\n\n")
            
            # 공격 요약
            f.write("공격 요약:\n")
            f.write("-" * 30 + "\n")
            
            attack_summary = []
            for file_path in self.flooding_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    attack_info = data['attack_info']
                    results = data['results']
                    
                    attack_summary.append({
                        'file': os.path.basename(file_path),
                        'message_type': attack_info['message_type'],
                        'threads': attack_info['num_threads'],
                        'messages_per_second': results['messages_per_second'],
                        'total_messages': results['total_messages'],
                        'errors': results['errors']
                    })
                except Exception as e:
                    f.write(f"파일 분석 오류 {file_path}: {e}\n")
            
            # 성능순 정렬
            sorted_attacks = sorted(attack_summary, key=lambda x: x['messages_per_second'], reverse=True)
            
            for i, attack in enumerate(sorted_attacks):
                f.write(f"{i+1}. {attack['file']}\n")
                f.write(f"   메시지 타입: {attack['message_type']}\n")
                f.write(f"   스레드 수: {attack['threads']}\n")
                f.write(f"   초당 메시지: {attack['messages_per_second']:.2f}\n")
                f.write(f"   총 메시지: {attack['total_messages']:,}\n")
                f.write(f"   오류 수: {attack['errors']}\n\n")
            
            # 모니터링 파일 분석
            f.write("모니터링 파일 분석:\n")
            f.write("-" * 30 + "\n")
            
            for i, file_path in enumerate(self.monitoring_files):
                f.write(f"\n파일 {i+1}: {os.path.basename(file_path)}\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                    
                    # 시스템 리소스 분석
                    system_analysis = self.analyze_system_resources(data)
                    if system_analysis:
                        f.write("  시스템 리소스:\n")
                        f.write(f"    CPU: {system_analysis['cpu']['min']:.1f}% ~ {system_analysis['cpu']['max']:.1f}% (평균: {system_analysis['cpu']['avg']:.1f}%)\n")
                        f.write(f"    메모리: {system_analysis['memory']['min']:.1f}% ~ {system_analysis['memory']['max']:.1f}% (평균: {system_analysis['memory']['avg']:.1f}%)\n")
                    
                    # 네트워크 트래픽 분석
                    network_analysis = self.analyze_network_traffic(data)
                    if network_analysis:
                        f.write("  네트워크 트래픽:\n")
                        f.write(f"    전송 바이트: {network_analysis['bytes_sent_diff']:,}\n")
                        f.write(f"    수신 바이트: {network_analysis['bytes_recv_diff']:,}\n")
                        f.write(f"    전송 패킷: {network_analysis['packets_sent_diff']:,}\n")
                        f.write(f"    수신 패킷: {network_analysis['packets_recv_diff']:,}\n")
                
                except Exception as e:
                    f.write(f"  파일 분석 오류: {e}\n")
        
        print(f"비교 분석 보고서 생성: {report_file}")
        return report_file
    
    def run_comparison(self):
        """전체 비교 분석 실행"""
        print("=== RRC Flooding Attack 영향 비교 분석 ===")
        
        # 데이터 로드
        self.load_monitoring_data()
        
        # 모니터링 파일들 비교
        self.compare_monitoring_files()
        
        # 공격과 영향 상관관계 분석
        self.correlate_attack_with_impact()
        
        # 보고서 생성
        self.generate_comparison_report()

def main():
    comparator = AttackImpactComparator()
    comparator.run_comparison()

if __name__ == "__main__":
    main()
