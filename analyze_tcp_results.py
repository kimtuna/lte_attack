#!/usr/bin/env python3
"""
TCP 기반 RRC Flooding Attack 결과 분석 도구
TCP 테스트 결과를 분석하고 최적화 방안 제시
"""

import json
import os
import glob
from datetime import datetime
import numpy as np

class TCPResultAnalyzer:
    """TCP 기반 Flooding 공격 결과 분석 클래스"""
    
    def __init__(self):
        self.log_dir = "logs"
        self.results = []
    
    def load_results(self):
        """로그 디렉토리에서 TCP 결과 파일들 로드"""
        if not os.path.exists(self.log_dir):
            print("로그 디렉토리가 없습니다.")
            return
        
        # tcp_flooding_attack_*.json 파일들 찾기
        pattern = os.path.join(self.log_dir, "tcp_flooding_attack_*.json")
        result_files = glob.glob(pattern)
        
        for file_path in result_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results.append({
                        'file': file_path,
                        'data': data,
                        'timestamp': data['results']['start_time']
                    })
            except Exception as e:
                print(f"파일 로드 오류 {file_path}: {e}")
        
        # 시간순 정렬
        self.results.sort(key=lambda x: x['timestamp'])
        print(f"총 {len(self.results)}개 TCP 결과 파일 로드됨")
    
    def analyze_latest_result(self):
        """최신 TCP 결과 분석"""
        if not self.results:
            print("분석할 결과가 없습니다.")
            return
        
        latest = self.results[-1]
        data = latest['data']
        
        print("=== 최신 TCP Flooding Attack 결과 분석 ===")
        print(f"파일: {latest['file']}")
        print(f"시간: {latest['timestamp']}")
        print()
        
        # 공격 정보
        attack_info = data['attack_info']
        print("공격 설정:")
        print(f"  대상: {attack_info['target_ip']}:{attack_info['target_port']}")
        print(f"  프로토콜: {attack_info['protocol']}")
        print(f"  메시지 타입: {attack_info['message_type']}")
        print(f"  스레드 수: {attack_info['num_threads']}")
        print(f"  지속 시간: {attack_info['duration']}초")
        print()
        
        # 결과 분석
        results = data['results']
        print("공격 결과:")
        print(f"  총 전송 메시지: {results['total_messages']:,}")
        print(f"  총 응답 수신: {results['total_responses']:,}")
        print(f"  응답 수신률: {results['response_rate']:.2f}%")
        print(f"  초당 메시지 수: {results['messages_per_second']:.2f}")
        print(f"  평균 응답 시간: {results['avg_response_time_ms']:.2f}ms")
        print(f"  오류 수: {results['errors']}")
        print()
        
        # 성능 평가
        self.evaluate_tcp_performance(results, attack_info)
    
    def evaluate_tcp_performance(self, results, attack_info):
        """TCP 성능 평가 및 개선 방안 제시"""
        print("TCP 성능 평가:")
        
        messages_per_second = results['messages_per_second']
        response_rate = results['response_rate']
        avg_response_time = results['avg_response_time_ms']
        threads = attack_info['num_threads']
        messages_per_thread = messages_per_second / threads
        
        print(f"  스레드당 초당 메시지: {messages_per_thread:.2f}")
        print(f"  응답 수신률: {response_rate:.2f}%")
        print(f"  평균 응답 시간: {avg_response_time:.2f}ms")
        
        # 성능 등급 평가
        if response_rate > 90 and avg_response_time < 10:
            grade = "매우 높음"
            color = "🟢"
        elif response_rate > 70 and avg_response_time < 50:
            grade = "높음"
            color = "🟡"
        elif response_rate > 50 and avg_response_time < 100:
            grade = "보통"
            color = "🟠"
        else:
            grade = "낮음"
            color = "🔴"
        
        print(f"  성능 등급: {color} {grade}")
        print()
        
        # 개선 방안 제시
        print("개선 방안:")
        
        if response_rate < 90:
            print("  - 응답 수신률이 낮음. 연결 안정성 확인 필요")
            print("  - 전송 간격 조정 고려")
        
        if avg_response_time > 50:
            print("  - 응답 시간이 느림. 네트워크 지연 확인 필요")
            print("  - 서버 부하 확인 필요")
        
        if messages_per_thread < 10:
            print("  - 스레드당 처리량이 낮음. 스레드 수 증가 고려")
        
        # 최적화 제안
        print("\n최적화 제안:")
        
        # 스레드 수 최적화
        if response_rate > 80:
            optimal_threads = min(20, max(10, int(messages_per_second / 5)))
            print(f"  - 권장 스레드 수: {optimal_threads}")
        
        # 전송 간격 최적화
        if avg_response_time < 10:
            print("  - 전송 간격을 5ms로 줄여서 성능 향상")
        else:
            print("  - 전송 간격을 20ms로 늘려서 안정성 향상")
    
    def compare_results(self):
        """여러 TCP 결과 비교 분석"""
        if len(self.results) < 2:
            print("비교할 결과가 부족합니다.")
            return
        
        print("=== TCP 결과 비교 분석 ===")
        
        # 성능 지표 비교
        print("성능 지표 비교:")
        print(f"{'순위':<4} {'초당메시지':<12} {'응답률':<8} {'응답시간':<10} {'스레드수':<8} {'오류수':<8}")
        print("-" * 70)
        
        # 성능순 정렬 (응답률과 처리량을 고려)
        sorted_results = sorted(self.results, 
                               key=lambda x: x['data']['results']['response_rate'] * x['data']['results']['messages_per_second'], 
                               reverse=True)
        
        for i, result in enumerate(sorted_results[:5]):  # 상위 5개만
            data = result['data']
            results = data['results']
            attack_info = data['attack_info']
            
            print(f"{i+1:<4} {results['messages_per_second']:<12.2f} "
                  f"{results['response_rate']:<8.2f}% {results['avg_response_time_ms']:<10.2f}ms "
                  f"{attack_info['num_threads']:<8} {results['errors']:<8}")
        
        print()
        
        # 최적 설정 추천
        best_result = sorted_results[0]
        best_data = best_result['data']
        
        print("최적 TCP 설정 추천:")
        print(f"  스레드 수: {best_data['attack_info']['num_threads']}")
        print(f"  메시지 타입: {best_data['attack_info']['message_type']}")
        print(f"  지속 시간: {best_data['attack_info']['duration']}초")
        print(f"  예상 성능: {best_data['results']['messages_per_second']:.2f} msg/sec")
        print(f"  예상 응답률: {best_data['results']['response_rate']:.2f}%")
    
    def generate_report(self):
        """종합 TCP 분석 보고서 생성"""
        if not self.results:
            print("분석할 결과가 없습니다.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"{self.log_dir}/tcp_analysis_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("TCP 기반 RRC Flooding Attack 결과 분석 보고서\n")
            f.write("=" * 60 + "\n")
            f.write(f"생성 시간: {datetime.now()}\n")
            f.write(f"분석 대상: {len(self.results)}개 테스트 결과\n\n")
            
            # 전체 통계
            total_messages = sum(r['data']['results']['total_messages'] for r in self.results)
            total_responses = sum(r['data']['results']['total_responses'] for r in self.results)
            total_errors = sum(r['data']['results']['errors'] for r in self.results)
            avg_messages_per_second = np.mean([r['data']['results']['messages_per_second'] for r in self.results])
            avg_response_rate = np.mean([r['data']['results']['response_rate'] for r in self.results])
            avg_response_time = np.mean([r['data']['results']['avg_response_time_ms'] for r in self.results])
            
            f.write("전체 통계:\n")
            f.write(f"  총 전송 메시지: {total_messages:,}\n")
            f.write(f"  총 응답 수신: {total_responses:,}\n")
            f.write(f"  총 오류 수: {total_errors:,}\n")
            f.write(f"  평균 초당 메시지: {avg_messages_per_second:.2f}\n")
            f.write(f"  평균 응답 수신률: {avg_response_rate:.2f}%\n")
            f.write(f"  평균 응답 시간: {avg_response_time:.2f}ms\n")
            f.write(f"  전체 성공률: {((total_messages - total_errors) / total_messages * 100):.2f}%\n\n")
            
            # 개별 결과
            f.write("개별 테스트 결과:\n")
            f.write("-" * 30 + "\n")
            
            for i, result in enumerate(self.results):
                data = result['data']
                f.write(f"\n테스트 {i+1}:\n")
                f.write(f"  시간: {result['timestamp']}\n")
                f.write(f"  설정: {data['attack_info']['num_threads']}스레드, "
                       f"{data['attack_info']['duration']}초, "
                       f"{data['attack_info']['message_type']}\n")
                f.write(f"  결과: {data['results']['total_messages']:,}개 메시지, "
                       f"{data['results']['messages_per_second']:.2f} msg/sec, "
                       f"{data['results']['response_rate']:.2f}% 응답률, "
                       f"{data['results']['avg_response_time_ms']:.2f}ms 응답시간\n")
            
            # 최적화 제안
            f.write("\n최적화 제안:\n")
            f.write("-" * 20 + "\n")
            
            # 최고 성능 결과 분석
            best_result = max(self.results, 
                             key=lambda x: x['data']['results']['response_rate'] * x['data']['results']['messages_per_second'])
            best_data = best_result['data']
            
            f.write(f"최고 성능 설정:\n")
            f.write(f"  스레드 수: {best_data['attack_info']['num_threads']}\n")
            f.write(f"  메시지 타입: {best_data['attack_info']['message_type']}\n")
            f.write(f"  지속 시간: {best_data['attack_info']['duration']}초\n")
            f.write(f"  성능: {best_data['results']['messages_per_second']:.2f} msg/sec\n")
            f.write(f"  응답률: {best_data['results']['response_rate']:.2f}%\n")
            f.write(f"  응답시간: {best_data['results']['avg_response_time_ms']:.2f}ms\n")
        
        print(f"TCP 분석 보고서 생성: {report_file}")
    
    def run_analysis(self):
        """전체 TCP 분석 실행"""
        print("=== TCP 기반 RRC Flooding Attack 결과 분석 ===")
        
        # 결과 로드
        self.load_results()
        
        if not self.results:
            print("분석할 결과가 없습니다.")
            return
        
        # 최신 결과 분석
        self.analyze_latest_result()
        
        # 결과 비교
        if len(self.results) > 1:
            self.compare_results()
        
        # 보고서 생성
        self.generate_report()

def main():
    analyzer = TCPResultAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
