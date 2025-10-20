# LTE DoS 공격 분석 도구

이 프로젝트는 LTE 네트워크에서 발생하는 DoS(Denial of Service) 공격을 분석하고, 메모리 사용량과 네트워크 연결 수를 모니터링하여 시스템 크래시까지의 과정을 시각화하는 도구입니다.

## 📁 프로젝트 구조

```
lte_dos/
├── flooding_attack.py          # RRC 메시지 Flooding 공격 도구
├── memory_analysis.py          # 메모리 사용량 분석 및 시각화
├── integrated_dos_analyzer.py  # 통합 DoS 공격 분석 도구
├── memory_visualizer.py        # 메모리 시각화 도구
├── install_dependencies.py    # 의존성 설치 스크립트
└── README.md                  # 이 파일
```

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
python3 install_dependencies.py
```

### 2. 메모리 모니터링만 실행

```bash
python3 memory_analysis.py --monitor-only
```

### 3. 시뮬레이션과 함께 실행

```bash
python3 memory_analysis.py --duration 10 --intensity medium
```

## 📊 주요 기능

### 1. 메모리 모니터링 (`memory_analysis.py`)

- **실시간 시스템 리소스 모니터링**
  - 메모리 사용률
  - CPU 사용률
  - 네트워크 연결 수
  - 프로세스 수

- **크래시 감지**
  - 메모리 사용률 95% 이상 시 자동 감지
  - 크래시 시점 기록 및 분석

- **시각화**
  - 시간별 리소스 사용량 그래프
  - 크래시까지의 과정 시각화
  - 상세 분석 보고서 생성

### 2. 통합 분석 도구 (`integrated_dos_analyzer.py`)

- **실제 Flooding 공격과 연동**
  - RRC 메시지 기반 공격 실행
  - 실시간 메모리 모니터링
  - 공격 진행 상황 추적

- **종합 분석**
  - 공격 시작부터 크래시까지의 전체 과정 분석
  - 상세한 통계 및 보고서 생성
  - 프레젠테이션용 데이터 생성

### 3. 메모리 시각화 (`memory_visualizer.py`)

- **경영진용 요약 차트**
  - 핵심 지표 요약
  - 위험도 평가
  - 권장사항 제시

- **기술진용 상세 분석**
  - 상세한 리소스 사용량 분석
  - 상관관계 분석
  - 통계적 분석

- **타임라인 차트**
  - 시간별 변화 추이
  - 크래시 시점 표시
  - 임계점 분석

## 🛠️ 사용법

### 메모리 분석 도구

```bash
# 기본 시뮬레이션 (10분, 중간 강도)
python3 memory_analysis.py --duration 10 --intensity medium

# 높은 강도 시뮬레이션 (5분)
python3 memory_analysis.py --duration 5 --intensity high

# 모니터링만 실행
python3 memory_analysis.py --monitor-only
```

### 통합 분석 도구

```bash
# 기본 분석 (RRC 메시지 파일 필요)
python3 integrated_dos_analyzer.py --messages rrc_messages.json

# 고강도 공격 분석
python3 integrated_dos_analyzer.py --messages rrc_messages.json --threads 50 --batch-size 10

# 장시간 분석
python3 integrated_dos_analyzer.py --messages rrc_messages.json --duration 600
```

### 메모리 시각화

```bash
# 분석 데이터로 메모리 차트 생성
python3 memory_visualizer.py --data analysis_data.json

# 사용자 정의 출력 디렉토리
python3 memory_visualizer.py --data analysis_data.json --output-dir my_charts
```

## 📈 출력 결과

### 1. 그래프 파일
- `executive_summary_chart.png` - 경영진용 요약 차트
- `technical_analysis_chart.png` - 기술진용 상세 분석
- `timeline_chart.png` - 타임라인 차트
- `comprehensive_dos_analysis_YYYYMMDD_HHMMSS.png` - 종합 분석 그래프

### 2. 데이터 파일
- `memory_monitor_data_YYYYMMDD_HHMMSS.json` - 모니터링 데이터
- `integrated_dos_analysis_YYYYMMDD_HHMMSS.json` - 통합 분석 데이터
- `flooding_results_YYYYMMDD_HHMMSS.json` - 공격 결과 데이터

### 3. 보고서 파일
- `comprehensive_dos_report_YYYYMMDD_HHMMSS.txt` - 종합 분석 보고서
- `presentation_summary.txt` - 프레젠테이션 요약

## 🔧 고급 설정

### 공격 파라미터 조정

```bash
# 스레드 수 조정
--threads 20

# 메시지 간격 조정
--interval 0.001

# 배치 크기 조정
--batch-size 5

# 대상 서버 변경
--target-ip 192.168.1.100 --target-port 8080
```

### 모니터링 설정

```bash
# 모니터링 간격 조정 (기본값: 1초)
monitoring_interval=0.5

# 최대 데이터 포인트 수 (기본값: 3600개)
max_data_points=7200
```

## 📊 분석 지표

### 메모리 분석
- **초기 메모리 사용률**: 공격 시작 시점의 메모리 사용률
- **최대 메모리 사용률**: 공격 중 최고 메모리 사용률
- **메모리 증가율**: 분당 메모리 사용률 증가량
- **크래시 임계점**: 메모리 사용률 95% 도달 시점

### 네트워크 분석
- **초기 연결 수**: 공격 시작 시점의 네트워크 연결 수
- **최대 연결 수**: 공격 중 최고 연결 수
- **연결 증가율**: 분당 연결 수 증가량
- **연결 효율성**: 메모리 대비 연결 수 비율

### 시간 분석
- **공격 지속 시간**: 공격 시작부터 종료까지의 시간
- **크래시까지 소요 시간**: 공격 시작부터 크래시까지의 시간
- **임계점 도달 시간**: 각 위험 수준 도달 시간

## ⚠️ 주의사항

1. **시스템 리소스**: 고강도 시뮬레이션은 시스템 리소스를 많이 사용합니다.
2. **네트워크 영향**: 실제 네트워크 공격은 대상 시스템에 영향을 줄 수 있습니다.
3. **데이터 백업**: 중요한 데이터는 미리 백업해두세요.
4. **권한 확인**: 시스템 모니터링을 위해 적절한 권한이 필요합니다.

## 🐛 문제 해결

### 의존성 설치 오류
```bash
# pip 업그레이드
python3 -m pip install --upgrade pip

# 개별 패키지 설치
pip install psutil matplotlib numpy pandas seaborn
```

### 권한 오류
```bash
# macOS/Linux에서 권한 문제 시
sudo python3 memory_analysis.py --monitor-only
```

### 메모리 부족
```bash
# 낮은 강도로 실행
python3 memory_analysis.py --intensity low --duration 5
```

## 📞 지원

문제가 발생하거나 추가 기능이 필요한 경우, 이슈를 등록해주세요.

## 📄 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 상업적 사용 시 별도 문의가 필요합니다.
