#!/usr/bin/env python3
"""
메모리 시각화 도구
DoS 공격 분석 데이터를 기반으로 메모리 사용량과 시스템 리소스를 시각화합니다.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import seaborn as sns
from pathlib import Path
import argparse

class MemoryVisualizer:
    def __init__(self):
        """메모리 시각화 도구 초기화"""
        self.data = None
        self.output_dir = "memory_charts"
        
        # 출력 디렉토리 생성
        Path(self.output_dir).mkdir(exist_ok=True)
        
        # 한글 폰트 및 스타일 설정
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
    def load_analysis_data(self, data_file):
        """분석 데이터 로드"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"데이터 로드 완료: {data_file}")
            return True
        except Exception as e:
            print(f"데이터 로드 오류: {e}")
            return False
    
    def create_executive_summary_chart(self):
        """경영진용 요약 차트 생성"""
        if not self.data:
            return None
        
        stats = self.data.get("stats", {})
        data_points = self.data.get("data", {})
        
        # 데이터 준비
        timestamps = [datetime.fromisoformat(t) for t in data_points.get("timestamps", [])]
        memory_usage = data_points.get("memory_usage", [])
        connections = data_points.get("connections", [])
        
        if not timestamps:
            return None
        
        # 시간을 분 단위로 변환
        start_time = timestamps[0]
        minutes = [(t - start_time).total_seconds() / 60 for t in timestamps]
        
        # 크래시 시점 찾기
        crash_minutes = None
        crash_time_str = stats.get("crash_time")
        if crash_time_str:
            crash_time = datetime.fromisoformat(crash_time_str)
            crash_minutes = (crash_time - start_time).total_seconds() / 60
        
        # 경영진용 요약 차트
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('DoS Attack Impact Analysis - Executive Report', fontsize=20, fontweight='bold', y=0.95)
        
        # 1. 메모리 사용률 (메인 차트)
        ax1.plot(minutes, memory_usage, 'b-', linewidth=4, label='Memory Usage')
        ax1.axhline(y=95, color='red', linestyle='--', linewidth=3, alpha=0.8, label='Crash Threshold')
        ax1.axhline(y=80, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Warning Threshold')
        
        if crash_minutes:
            ax1.axvline(x=crash_minutes, color='red', linestyle=':', linewidth=4, alpha=0.9, 
                       label=f'Crash Detected ({crash_minutes:.1f}min)')
        
        ax1.set_title('System Memory Usage', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Time (minutes)', fontsize=14)
        ax1.set_ylabel('Memory Usage (%)', fontsize=14)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        
        # 2. 네트워크 연결 수
        ax2.plot(minutes, connections, 'g-', linewidth=3, label='Network Connections')
        if crash_minutes:
            ax2.axvline(x=crash_minutes, color='red', linestyle=':', linewidth=3, alpha=0.8)
        ax2.set_title('Network Connections Change', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Time (minutes)', fontsize=14)
        ax2.set_ylabel('Connections', fontsize=14)
        ax2.legend(fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # 3. 핵심 지표 요약
        peak_memory = stats.get("peak_memory", 0)
        peak_connections = stats.get("peak_connections", 0)
        crash_detected = bool(crash_time_str)
        
        metrics = ['Memory Usage', 'Network Connections', 'Crash Detected']
        values = [f'{peak_memory:.1f}%', f'{peak_connections}', 'Yes' if crash_detected else 'No']
        colors = ['red' if peak_memory >= 95 else 'orange' if peak_memory >= 80 else 'green',
                 'red' if peak_connections > 1000 else 'orange' if peak_connections > 500 else 'green',
                 'red' if crash_detected else 'green']
        
        bars = ax3.bar(metrics, [peak_memory, min(peak_connections/10, 100), 100 if crash_detected else 0], 
                      color=colors, alpha=0.7)
        ax3.set_title('Key Metrics Summary', fontsize=16, fontweight='bold')
        ax3.set_ylabel('Value', fontsize=14)
        ax3.set_ylim(0, 100)
        
        # 값 표시
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 2,
                    value, ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        # 4. 시간별 위험도 분석
        risk_levels = []
        for mem in memory_usage:
            if mem >= 95:
                risk_levels.append(3)  # 높음
            elif mem >= 80:
                risk_levels.append(2)  # 중간
            elif mem >= 60:
                risk_levels.append(1)  # 낮음
            else:
                risk_levels.append(0)  # 정상
        
        risk_colors = ['green', 'yellow', 'orange', 'red']
        risk_labels = ['Normal', 'Low', 'Medium', 'High']
        
        ax4.fill_between(minutes, risk_levels, alpha=0.6, color='red')
        ax4.plot(minutes, risk_levels, 'k-', linewidth=2)
        ax4.set_title('Risk Level Over Time', fontsize=16, fontweight='bold')
        ax4.set_xlabel('Time (minutes)', fontsize=14)
        ax4.set_ylabel('Risk Level', fontsize=14)
        ax4.set_ylim(0, 3)
        ax4.set_yticks([0, 1, 2, 3])
        ax4.set_yticklabels(risk_labels)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        filename = f"{self.output_dir}/executive_summary_chart.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"경영진용 요약 차트 저장: {filename}")
        
        plt.show()
        return fig
    
    def create_technical_analysis_chart(self):
        """기술진용 상세 분석 차트 생성"""
        if not self.data:
            return None
        
        data_points = self.data.get("data", {})
        
        # 데이터 준비
        timestamps = [datetime.fromisoformat(t) for t in data_points.get("timestamps", [])]
        memory_usage = data_points.get("memory_usage", [])
        cpu_usage = data_points.get("cpu_usage", [])
        connections = data_points.get("connections", [])
        process_count = data_points.get("process_count", [])
        
        if not timestamps:
            return None
        
        # 시간을 분 단위로 변환
        start_time = timestamps[0]
        minutes = [(t - start_time).total_seconds() / 60 for t in timestamps]
        
        # 기술진용 상세 차트
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('DoS Attack Technical Analysis - Detailed Report', fontsize=20, fontweight='bold')
        
        # 1. 메모리 사용률 (상세)
        axes[0, 0].plot(minutes, memory_usage, 'b-', linewidth=2, label='Memory Usage')
        axes[0, 0].axhline(y=95, color='red', linestyle='--', alpha=0.8, label='Crash Threshold (95%)')
        axes[0, 0].axhline(y=80, color='orange', linestyle='--', alpha=0.7, label='Warning Threshold (80%)')
        axes[0, 0].axhline(y=60, color='yellow', linestyle='--', alpha=0.6, label='Caution Threshold (60%)')
        axes[0, 0].set_title('Memory Usage Change', fontweight='bold')
        axes[0, 0].set_xlabel('Time (minutes)')
        axes[0, 0].set_ylabel('Memory Usage (%)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 100)
        
        # 2. CPU 사용률
        axes[0, 1].plot(minutes, cpu_usage, 'purple', linewidth=2, label='CPU Usage')
        axes[0, 1].set_title('CPU Usage Change', fontweight='bold')
        axes[0, 1].set_xlabel('Time (minutes)')
        axes[0, 1].set_ylabel('CPU Usage (%)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(0, 100)
        
        # 3. 네트워크 연결 수
        axes[0, 2].plot(minutes, connections, 'g-', linewidth=2, label='Network Connections')
        axes[0, 2].set_title('Network Connections Change', fontweight='bold')
        axes[0, 2].set_xlabel('Time (minutes)')
        axes[0, 2].set_ylabel('Connections')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. 프로세스 수
        axes[1, 0].plot(minutes, process_count, 'orange', linewidth=2, label='Process Count')
        axes[1, 0].set_title('Process Count Change', fontweight='bold')
        axes[1, 0].set_xlabel('Time (minutes)')
        axes[1, 0].set_ylabel('Process Count')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. 메모리 사용률 히스토그램
        axes[1, 1].hist(memory_usage, bins=20, alpha=0.7, color='blue', edgecolor='black')
        axes[1, 1].axvline(np.mean(memory_usage), color='red', linestyle='--', linewidth=2, 
                          label=f'Mean: {np.mean(memory_usage):.1f}%')
        axes[1, 1].axvline(np.median(memory_usage), color='green', linestyle='--', linewidth=2, 
                          label=f'Median: {np.median(memory_usage):.1f}%')
        axes[1, 1].set_title('Memory Usage Distribution', fontweight='bold')
        axes[1, 1].set_xlabel('Memory Usage (%)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. 상관관계 분석
        correlation_data = pd.DataFrame({
            'Memory': memory_usage,
            'CPU': cpu_usage,
            'Connections': connections,
            'Processes': process_count
        })
        
        correlation_matrix = correlation_data.corr()
        im = axes[1, 2].imshow(correlation_matrix, cmap='coolwarm', aspect='auto')
        axes[1, 2].set_title('Resource Correlation Matrix', fontweight='bold')
        
        # 상관관계 값 표시
        for i in range(len(correlation_matrix.columns)):
            for j in range(len(correlation_matrix.columns)):
                text = axes[1, 2].text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                      ha="center", va="center", color="black", fontweight='bold')
        
        axes[1, 2].set_xticks(range(len(correlation_matrix.columns)))
        axes[1, 2].set_yticks(range(len(correlation_matrix.columns)))
        axes[1, 2].set_xticklabels(correlation_matrix.columns, rotation=45)
        axes[1, 2].set_yticklabels(correlation_matrix.columns)
        
        plt.tight_layout()
        
        # 저장
        filename = f"{self.output_dir}/technical_analysis_chart.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"기술진용 상세 분석 차트 저장: {filename}")
        
        plt.show()
        return fig
    
    def create_timeline_chart(self):
        """타임라인 차트 생성"""
        if not self.data:
            return None
        
        stats = self.data.get("stats", {})
        data_points = self.data.get("data", {})
        
        # 데이터 준비
        timestamps = [datetime.fromisoformat(t) for t in data_points.get("timestamps", [])]
        memory_usage = data_points.get("memory_usage", [])
        
        if not timestamps:
            return None
        
        # 타임라인 차트
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # 메모리 사용률 플롯
        ax.plot(timestamps, memory_usage, 'b-', linewidth=3, label='Memory Usage')
        
        # 임계점 라인
        ax.axhline(y=95, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Crash Threshold (95%)')
        ax.axhline(y=80, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Warning Threshold (80%)')
        ax.axhline(y=60, color='yellow', linestyle='--', linewidth=2, alpha=0.6, label='Caution Threshold (60%)')
        
        # 크래시 시점 표시
        crash_time_str = stats.get("crash_time")
        if crash_time_str:
            crash_time = datetime.fromisoformat(crash_time_str)
            ax.axvline(x=crash_time, color='red', linestyle=':', linewidth=4, alpha=0.9, 
                      label=f'Crash Detected ({crash_time.strftime("%H:%M:%S")})')
        
        # 시간 축 포맷팅
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        ax.set_title('DoS Attack Timeline - Memory Usage Change', fontsize=18, fontweight='bold')
        ax.set_xlabel('Time', fontsize=14)
        ax.set_ylabel('Memory Usage (%)', fontsize=14)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
        
        plt.tight_layout()
        
        # 저장
        filename = f"{self.output_dir}/timeline_chart.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"타임라인 차트 저장: {filename}")
        
        plt.show()
        return fig
    
    def generate_presentation_summary(self):
        """프레젠테이션 요약 생성"""
        if not self.data:
            return "데이터가 없습니다."
        
        stats = self.data.get("stats", {})
        data_points = self.data.get("data", {})
        
        # 기본 통계 계산
        memory_usage = data_points.get("memory_usage", [])
        connections = data_points.get("connections", [])
        cpu_usage = data_points.get("cpu_usage", [])
        
        peak_memory = stats.get("peak_memory", 0)
        peak_connections = stats.get("peak_connections", 0)
        crash_detected = bool(stats.get("crash_time"))
        
        duration_minutes = stats.get("total_data_points", 0) * stats.get("monitoring_interval", 1) / 60
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DoS 공격 분석 프레젠테이션 요약                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 핵심 지표:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 분석 기간: {duration_minutes:.1f}분{'':<45} │
│ 최대 메모리 사용률: {peak_memory:.1f}%{'':<40} │
│ 최대 네트워크 연결 수: {peak_connections}개{'':<40} │
│ 평균 CPU 사용률: {np.mean(cpu_usage):.1f}%{'':<40} │
│ 크래시 발생: {'예' if crash_detected else '아니오'}{'':<45} │
└─────────────────────────────────────────────────────────────────────────────┘

🚨 위험도 평가:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 메모리 위험도: {'높음' if peak_memory >= 95 else '중간' if peak_memory >= 80 else '낮음'}{'':<45} │
│ 네트워크 위험도: {'높음' if peak_connections > 1000 else '중간' if peak_connections > 500 else '낮음'}{'':<40} │
│ 전체 위험도: {'높음' if crash_detected else '중간' if peak_memory >= 80 else '낮음'}{'':<45} │
└─────────────────────────────────────────────────────────────────────────────┘

📈 트렌드 분석:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 메모리 증가율: {((memory_usage[-1] - memory_usage[0]) / len(memory_usage) * 60):.2f}% per minute{'':<30} │
│ 연결 증가율: {((connections[-1] - connections[0]) / len(connections) * 60):.1f} connections per minute{'':<20} │
│ 메모리 변동성: {np.std(memory_usage):.1f}%{'':<45} │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 권장사항:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 즉시 조치: {'메모리 제한 설정' if crash_detected else '모니터링 강화'}{'':<40} │
│ 2. 예방 조치: {'연결 수 제한 및 리소스 모니터링' if peak_memory >= 80 else '정상 범위 내 운영'}{'':<25} │
│ 3. 장기 대응: {'DoS 방어 시스템 구축' if crash_detected else '정기적 모니터링'}{'':<40} │
└─────────────────────────────────────────────────────────────────────────────┘

📋 프레젠테이션 구성:
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 경영진용 요약 차트 (executive_summary_chart.png)                          │
│ 2. 기술진용 상세 분석 차트 (technical_analysis_chart.png)                   │
│ 3. 타임라인 차트 (timeline_chart.png)                                       │
│ 4. 상세 분석 보고서 (comprehensive_report.txt)                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
        """
        
        return summary
    
    def create_all_presentations(self):
        """모든 프레젠테이션 자료 생성"""
        if not self.data:
            print("데이터가 로드되지 않았습니다.")
            return False
        
        print("=== 프레젠테이션 자료 생성 시작 ===")
        
        # 1. 경영진용 요약 차트
        print("1. 경영진용 요약 차트 생성 중...")
        self.create_executive_summary_chart()
        
        # 2. 기술진용 상세 분석 차트
        print("2. 기술진용 상세 분석 차트 생성 중...")
        self.create_technical_analysis_chart()
        
        # 3. 타임라인 차트
        print("3. 타임라인 차트 생성 중...")
        self.create_timeline_chart()
        
        # 4. 요약 보고서 생성
        print("4. 요약 보고서 생성 중...")
        summary = self.generate_presentation_summary()
        
        # 요약 보고서 저장
        summary_filename = f"{self.output_dir}/presentation_summary.txt"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"프레젠테이션 요약 저장: {summary_filename}")
        
        print("\n=== 프레젠테이션 자료 생성 완료 ===")
        print(f"출력 디렉토리: {self.output_dir}/")
        print("생성된 파일들:")
        print("- executive_summary_chart.png (경영진용)")
        print("- technical_analysis_chart.png (기술진용)")
        print("- timeline_chart.png (타임라인)")
        print("- presentation_summary.txt (요약)")
        
        return True
    
    def start_web_server(self, port=8080):
        """웹 서버 시작"""
        import subprocess
        import threading
        import time
        
        def run_server():
            try:
                subprocess.run([
                    "python3", "-m", "http.server", str(port)
                ], cwd=self.output_dir)
            except Exception as e:
                print(f"웹 서버 실행 오류: {e}")
        
        # 백그라운드에서 서버 실행
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # 서버 시작 대기
        time.sleep(2)
        
        print(f"\n🌐 웹 서버가 시작되었습니다!")
        print(f"📱 브라우저에서 접속: http://localhost:{port}")
        print(f"📁 서빙 디렉토리: {self.output_dir}")
        print(f"⏹️  서버 중지: Ctrl+C")
        
        return server_thread

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="메모리 시각화 도구")
    parser.add_argument("--data", required=True, help="분석 데이터 JSON 파일")
    parser.add_argument("--output-dir", default="memory_charts", help="출력 디렉토리")
    parser.add_argument("--web-server", action="store_true", help="웹 서버 자동 시작")
    parser.add_argument("--port", type=int, default=8080, help="웹 서버 포트")
    
    args = parser.parse_args()
    
    # 메모리 시각화 도구 생성
    visualizer = MemoryVisualizer()
    visualizer.output_dir = args.output_dir
    Path(visualizer.output_dir).mkdir(exist_ok=True)
    
    # 데이터 로드
    if not visualizer.load_analysis_data(args.data):
        return
    
    # 모든 시각화 자료 생성
    visualizer.create_all_presentations()
    
    # 웹 서버 시작 (옵션)
    if args.web_server:
        visualizer.start_web_server(args.port)
    
    # 요약 출력
    print("\n" + "="*60)
    print(visualizer.generate_presentation_summary())
    print("="*60)

if __name__ == "__main__":
    main()
