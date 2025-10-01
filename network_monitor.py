#!/usr/bin/env python3
"""
네트워크 성능 모니터링 스크립트
공격 중 네트워크 지연, 패킷 손실 등을 모니터링
"""

import subprocess
import time
import threading
import json
import re
from datetime import datetime

class NetworkMonitor:
    def __init__(self, target_ip="127.0.0.1", interval=5):
        self.target_ip = target_ip
        self.interval = interval
        self.monitoring = False
        self.stats = []
        
    def ping_test(self):
        """Ping 테스트로 지연 시간 측정"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", self.target_ip],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                # ping 결과에서 시간 추출
                match = re.search(r'time=(\d+\.?\d*)', result.stdout)
                if match:
                    return float(match.group(1))
            return None
        except:
            return None
    
    def check_port_connectivity(self, port):
        """포트 연결성 확인"""
        try:
            result = subprocess.run(
                ["nc", "-z", "-v", self.target_ip, str(port)],
                capture_output=True, text=True, timeout=3
            )
            return result.returncode == 0
        except:
            return False
    
    def get_network_stats(self):
        """네트워크 통계 수집"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "ping_time": self.ping_test(),
            "ports": {
                "36412": self.check_port_connectivity(36412),  # RRC
                "36422": self.check_port_connectivity(36422),  # Paging
                "36432": self.check_port_connectivity(36432),  # NAS
            }
        }
        return stats
    
    def monitor_loop(self):
        """모니터링 루프"""
        while self.monitoring:
            stats = self.get_network_stats()
            self.stats.append(stats)
            
            # 실시간 출력
            ping_status = f"{stats['ping_time']:.1f}ms" if stats['ping_time'] else "N/A"
            port_status = " ".join([f"{port}:{'✓' if status else '✗'}" 
                                  for port, status in stats['ports'].items()])
            
            print(f"[{stats['timestamp']}] Ping: {ping_status} | Ports: {port_status}")
            
            time.sleep(self.interval)
    
    def start_monitoring(self):
        """모니터링 시작"""
        print(f"네트워크 모니터링 시작 (대상: {self.target_ip})...")
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
        print("모니터링 중지됨")
    
    def analyze_network_performance(self):
        """네트워크 성능 분석"""
        if len(self.stats) < 2:
            return
        
        # Ping 시간 분석
        ping_times = [s['ping_time'] for s in self.stats if s['ping_time'] is not None]
        if ping_times:
            avg_ping = sum(ping_times) / len(ping_times)
            max_ping = max(ping_times)
            min_ping = min(ping_times)
        else:
            avg_ping = max_ping = min_ping = 0
        
        # 포트 연결성 분석
        port_stats = {}
        for port in ["36412", "36422", "36432"]:
            connected_count = sum(1 for s in self.stats if s['ports'][port])
            total_count = len(self.stats)
            port_stats[port] = {
                "connection_rate": (connected_count / total_count) * 100 if total_count > 0 else 0,
                "total_checks": total_count,
                "successful_checks": connected_count
            }
        
        print("\n=== 네트워크 성능 분석 결과 ===")
        print(f"평균 Ping 시간: {avg_ping:.1f}ms")
        print(f"최대 Ping 시간: {max_ping:.1f}ms")
        print(f"최소 Ping 시간: {min_ping:.1f}ms")
        
        print("\n포트 연결성:")
        for port, stats in port_stats.items():
            print(f"  포트 {port}: {stats['connection_rate']:.1f}% "
                  f"({stats['successful_checks']}/{stats['total_checks']})")
        
        # 성능 저하 경고
        if max_ping > 100:
            print("⚠️  Ping 시간이 높습니다 (100ms 초과)")
        
        for port, stats in port_stats.items():
            if stats['connection_rate'] < 80:
                print(f"⚠️  포트 {port} 연결성이 낮습니다 ({stats['connection_rate']:.1f}%)")
        
        return {
            "avg_ping": avg_ping,
            "max_ping": max_ping,
            "min_ping": min_ping,
            "port_stats": port_stats
        }
    
    def save_stats(self, filename="network_stats.json"):
        """통계를 JSON 파일로 저장"""
        with open(filename, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"네트워크 통계 저장됨: {filename}")

def main():
    import sys
    
    target_ip = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    monitor = NetworkMonitor(target_ip, interval=5)
    
    try:
        monitor.start_monitoring()
        print("모니터링 중... (Ctrl+C로 중지)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n모니터링 중지")
        monitor.stop_monitoring()
        monitor.analyze_network_performance()
        monitor.save_stats()

if __name__ == "__main__":
    main()
