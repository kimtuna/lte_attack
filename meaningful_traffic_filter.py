#!/usr/bin/env python3
"""
의미있는 트래픽만 필터링하는 tshark 스크립트
연결 유지용 메시지를 제외하고 실제 RRC/NAS/S1AP 메시지만 표시
"""

import subprocess
import time
import sys

class MeaningfulTrafficFilter:
    def __init__(self):
        self.filters = {
            "rrc_only": "udp contains 0x0001 or udp contains 0x0002 or udp contains 0x0003 or udp contains 0x0004 or udp contains 0x0005",
            "nas_only": "udp contains 0x41 or udp contains 0x48 or udp contains 0x45",
            "s1ap_only": "udp[8:2] == 0x0000",
            "no_heartbeat": "frame.len > 50 and not (udp[8] == 0x01 or udp[8] == 0x02)",
            "meaningful_only": "(udp contains 0x0001 or udp contains 0x0002 or udp contains 0x0003 or udp contains 0x0004 or udp contains 0x0005 or udp contains 0x41 or udp contains 0x48 or udp contains 0x45) and frame.len > 50"
        }
    
    def show_filters(self):
        """사용 가능한 필터 목록 표시"""
        print("사용 가능한 필터:")
        for name, filter_expr in self.filters.items():
            print(f"  {name}: {filter_expr}")
    
    def run_filter(self, filter_name, duration=60):
        """지정된 필터로 tshark 실행"""
        if filter_name not in self.filters:
            print(f"❌ 알 수 없는 필터: {filter_name}")
            self.show_filters()
            return
        
        filter_expr = self.filters[filter_name]
        
        cmd = [
            "sudo", "tshark",
            "-i", "any",
            "-f", "port 2000 or port 2001",
            "-Y", filter_expr,
            "-T", "fields",
            "-e", "frame.time",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "udp.srcport",
            "-e", "udp.dstport",
            "-e", "frame.len",
            "-e", "data"
        ]
        
        print(f"🔍 필터: {filter_name}")
        print(f"📋 표현식: {filter_expr}")
        print(f"⏱️  지속 시간: {duration}초")
        print("=" * 60)
        
        try:
            if duration > 0:
                # timeout으로 제한된 실행
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=duration)
                    if stdout:
                        print(stdout)
                    if stderr:
                        print(f"오류: {stderr}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"\n⏰ {duration}초 후 자동 종료")
            else:
                # 무제한 실행
                subprocess.run(cmd)
                
        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단됨")
        except Exception as e:
            print(f"❌ 실행 오류: {e}")

def main():
    filter_tool = MeaningfulTrafficFilter()
    
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python3 meaningful_traffic_filter.py <filter_name> [duration]")
        print("")
        filter_tool.show_filters()
        print("")
        print("예시:")
        print("  python3 meaningful_traffic_filter.py rrc_only 30")
        print("  python3 meaningful_traffic_filter.py meaningful_only 60")
        print("  python3 meaningful_traffic_filter.py no_heartbeat 0  # 무제한")
        return
    
    filter_name = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    filter_tool.run_filter(filter_name, duration)

if __name__ == "__main__":
    main()
