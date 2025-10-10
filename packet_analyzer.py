#!/usr/bin/env python3
"""
실제 UE 패킷 분석 및 형식 추출 도구
tshark 캡처 데이터에서 실제 RRC 메시지 형식을 분석
"""

import subprocess
import re
import struct
from datetime import datetime

class PacketAnalyzer:
    def __init__(self):
        self.captured_packets = []
        self.message_formats = {}
        
    def capture_real_packets(self, duration=30):
        """실제 UE 패킷 캡처"""
        print(f"=== 실제 UE 패킷 캡처 시작 ({duration}초) ===")
        print("UE를 사용해서 실제 RRC 메시지를 보내주세요...")
        
        try:
            # tshark로 패킷 캡처
            cmd = [
                "sudo", "tshark", 
                "-i", "any",
                "-f", "port 2001",
                "-T", "fields",
                "-e", "frame.time",
                "-e", "ip.src",
                "-e", "ip.dst", 
                "-e", "udp.srcport",
                "-e", "udp.dstport",
                "-e", "data"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration)
            
            if result.returncode == 0 and result.stdout.strip():
                self.parse_tshark_output(result.stdout)
                return True
            else:
                print(f"패킷 캡처 실패: {result.stderr}")
                print("기본 패킷으로 진행합니다...")
                # 기본 패킷 생성
                self.create_default_packets()
                return True
                
        except subprocess.TimeoutExpired:
            print("캡처 시간 초과")
            print("기본 패킷으로 진행합니다...")
            self.create_default_packets()
            return True
        except Exception as e:
            print(f"캡처 오류: {e}")
            print("기본 패킷으로 진행합니다...")
            self.create_default_packets()
            return True
    
    def parse_tshark_output(self, output):
        """tshark 출력 파싱"""
        lines = output.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) >= 6:
                timestamp = parts[0]
                src_ip = parts[1]
                dst_ip = parts[2]
                src_port = parts[3]
                dst_port = parts[4]
                data_hex = parts[5]
                
                # 데이터가 있는 패킷만 저장
                if data_hex and data_hex != '':
                    packet = {
                        'timestamp': timestamp,
                        'src_ip': src_ip,
                        'dst_ip': dst_ip,
                        'src_port': src_port,
                        'dst_port': dst_port,
                        'data_hex': data_hex,
                        'data_bytes': bytes.fromhex(data_hex.replace(':', ''))
                    }
                    self.captured_packets.append(packet)
        
        print(f"총 {len(self.captured_packets)}개 패킷 캡처됨")
    
    def create_default_packets(self):
        """기본 패킷 생성 (캡처 실패 시 사용)"""
        import struct
        import random
        
        print("기본 RRC 메시지 패킷 생성 중...")
        
        # RRC Connection Request
        rrc_request = struct.pack('>H', 0x0001) +  # Message Type
        rrc_request += struct.pack('>I', 1001) +     # UE Identity
        rrc_request += struct.pack('>H', 0x0001) +   # Establishment Cause
        rrc_request += struct.pack('>H', 0x0000) +   # Spare
        rrc_request += struct.pack('>Q', 1234567890123456) +  # IMSI
        rrc_request += struct.pack('>I', 123456) +   # TMSI
        rrc_request += struct.pack('>H', 12345) +    # LAI
        rrc_request += struct.pack('>B', 0x01) +     # RRC State
        rrc_request += struct.pack('>I', 123456) +   # Cell ID
        rrc_request += struct.pack('>H', 12345) +    # Tracking Area Code
        rrc_request += b'\x00' * 50  # 추가 필드
        
        # RRC Connection Setup Complete
        rrc_setup = struct.pack('>H', 0x0003) +  # Message Type
        rrc_setup += struct.pack('>I', 1001) +     # UE Identity
        rrc_setup += struct.pack('>H', 0x0000) +   # Spare
        rrc_setup += struct.pack('>H', 0x0041) +   # NAS Message Type
        rrc_setup += struct.pack('>I', 123456) +   # NAS Transaction ID
        rrc_setup += struct.pack('>B', 0x01) +     # NAS Security Header
        rrc_setup += struct.pack('>B', 0x00) +     # NAS Spare
        rrc_setup += b'\x00' * 30  # 추가 필드
        
        # RRC Measurement Report
        rrc_measurement = struct.pack('>H', 0x0005) +  # Message Type
        rrc_measurement += struct.pack('>I', 1001) +     # UE Identity
        rrc_measurement += struct.pack('>H', 12345) +   # Cell ID 1
        rrc_measurement += struct.pack('>B', 0x8C) +     # RSRP (-100)
        rrc_measurement += struct.pack('>B', 0xF6) +     # RSRQ (-10)
        rrc_measurement += struct.pack('>B', 0x64) +     # SINR (100)
        rrc_measurement += struct.pack('>H', 12346) +   # Cell ID 2
        rrc_measurement += struct.pack('>B', 0x8D) +     # RSRP (-99)
        rrc_measurement += struct.pack('>B', 0xF7) +     # RSRQ (-9)
        rrc_measurement += struct.pack('>B', 0x63) +     # SINR (99)
        rrc_measurement += b'\x00' * 40  # 추가 필드
        
        # 패킷 저장
        self.captured_packets = [
            {'data_bytes': rrc_request, 'data_hex': rrc_request.hex()},
            {'data_bytes': rrc_setup, 'data_hex': rrc_setup.hex()},
            {'data_bytes': rrc_measurement, 'data_hex': rrc_measurement.hex()}
        ]
        
        # 메시지 형식 저장
        self.message_formats[0x0001] = [rrc_request]
        self.message_formats[0x0003] = [rrc_setup]
        self.message_formats[0x0005] = [rrc_measurement]
        
        print(f"기본 패킷 생성 완료: {len(self.captured_packets)}개")
    
    def analyze_message_formats(self):
        """메시지 형식 분석"""
        print("\n=== 메시지 형식 분석 ===")
        
        for i, packet in enumerate(self.captured_packets):
            print(f"\n패킷 #{i+1}:")
            print(f"  시간: {packet['timestamp']}")
            print(f"  소스: {packet['src_ip']}:{packet['src_port']}")
            print(f"  대상: {packet['dst_ip']}:{packet['dst_port']}")
            print(f"  데이터: {packet['data_hex']}")
            print(f"  크기: {len(packet['data_bytes'])} bytes")
            
            # RRC 메시지 타입 추출
            if len(packet['data_bytes']) >= 2:
                message_type = struct.unpack('>H', packet['data_bytes'][:2])[0]
                print(f"  메시지 타입: 0x{message_type:04X}")
                
                # 메시지 형식 저장
                if message_type not in self.message_formats:
                    self.message_formats[message_type] = []
                self.message_formats[message_type].append(packet['data_bytes'])
    
    def generate_attack_messages(self):
        """공격용 메시지 생성"""
        print("\n=== 공격용 메시지 생성 ===")
        
        attack_messages = {}
        
        for msg_type, packets in self.message_formats.items():
            print(f"\n메시지 타입 0x{msg_type:04X}:")
            
            # 가장 긴 패킷을 기준으로 사용
            longest_packet = max(packets, key=len)
            print(f"  기준 패킷 크기: {len(longest_packet)} bytes")
            print(f"  패킷 수: {len(packets)}")
            
            # 공격용 메시지 생성 (여러 변형)
            attack_messages[msg_type] = []
            
            for i in range(10):  # 10개 변형 생성
                # 기본 패킷 복사
                attack_msg = bytearray(longest_packet)
                
                # UE ID 변경 (다양한 UE 시뮬레이션)
                if len(attack_msg) >= 6:
                    ue_id = 1000 + i
                    attack_msg[2:6] = struct.pack('>I', ue_id)
                
                # 일부 필드 랜덤화
                for j in range(10, min(len(attack_msg), 50)):
                    attack_msg[j] = (attack_msg[j] + i) % 256
                
                attack_messages[msg_type].append(bytes(attack_msg))
            
            print(f"  생성된 공격 메시지: {len(attack_messages[msg_type])}개")
        
        return attack_messages
    
    def save_attack_messages(self, attack_messages):
        """공격 메시지를 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"real_ue_attack_messages_{timestamp}.py"
        
        with open(filename, 'w') as f:
            f.write("#!/usr/bin/env python3\n")
            f.write("# 실제 UE 패킷 형식으로 생성된 공격 메시지\n")
            f.write("# 자동 생성됨 - 수정하지 마세요\n\n")
            
            f.write("ATTACK_MESSAGES = {\n")
            
            for msg_type, messages in attack_messages.items():
                f.write(f"    0x{msg_type:04X}: [\n")
                for i, msg in enumerate(messages):
                    hex_str = msg.hex()
                    f.write(f"        bytes.fromhex('{hex_str}'),  # 변형 {i+1}\n")
                f.write("    ],\n")
            
            f.write("}\n\n")
            f.write("def get_attack_message(msg_type, variant=0):\n")
            f.write("    \"\"\"공격 메시지 가져오기\"\"\"\n")
            f.write("    if msg_type in ATTACK_MESSAGES:\n")
            f.write("        messages = ATTACK_MESSAGES[msg_type]\n")
            f.write("        return messages[variant % len(messages)]\n")
            f.write("    return None\n")
        
        print(f"\n공격 메시지가 {filename}에 저장되었습니다.")
        return filename

def main():
    analyzer = PacketAnalyzer()
    
    print("=== 실제 UE 패킷 분석 도구 ===")
    print("1. 실제 UE로 RRC 메시지를 보내주세요")
    print("2. 패킷을 캡처하고 분석합니다")
    print("3. 공격용 메시지를 생성합니다")
    print()
    
    # 패킷 캡처
    if analyzer.capture_real_packets(30):
        # 메시지 형식 분석
        analyzer.analyze_message_formats()
        
        # 공격 메시지 생성
        attack_messages = analyzer.generate_attack_messages()
        
        # 파일로 저장
        filename = analyzer.save_attack_messages(attack_messages)
        
        print(f"\n=== 완료 ===")
        print(f"분석된 메시지 타입: {len(analyzer.message_formats)}개")
        print(f"생성된 공격 메시지: {sum(len(msgs) for msgs in attack_messages.values())}개")
        print(f"저장된 파일: {filename}")
        
    else:
        print("패킷 캡처에 실패했습니다.")

if __name__ == "__main__":
    main()
