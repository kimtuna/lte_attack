# TCP 기반 srsRAN eNB RRC Flooding Attack

TCP 소켓을 사용한 실제 연결 기반 srsRAN eNB flooding 공격 도구입니다.

## 개요

이 도구는 TCP 소켓을 사용하여 srsRAN eNB와 실제 연결을 맺고 RRC 메시지를 전송하는 flooding 공격을 수행합니다. UDP 기반 공격과 달리 실제 응답을 받아 공격 효과를 정확히 측정할 수 있습니다.

## 주요 기능

### 1. TCP 기반 RRC 메시지 전송
- **실제 TCP 연결**: srsRAN eNB와 안정적인 연결
- **응답 확인**: 메시지 전송 후 응답 수신
- **연결 상태 모니터링**: 연결 안정성 실시간 확인

### 2. RRC 메시지 생성
- **RRCConnectionRequest**: UE가 eNB에 연결을 요청하는 메시지
- **RRCConnectionReestablishmentRequest**: 연결 재설정 요청 메시지
- **3GPP TS 36.331 표준 준수**: 정확한 메시지 형식

### 3. Flooding 공격
- **멀티스레딩**: 동시 다중 연결로 공격
- **응답 시간 측정**: 실제 처리 시간 측정
- **응답률 계산**: 성공적인 응답 비율 측정

### 4. 테스트 및 분석
- **실시간 모니터링**: 시스템 리소스 및 네트워크 상태
- **성능 분석**: 응답률, 처리량, 지연시간 분석
- **최적화 제안**: 성능 향상을 위한 설정 제안

## 파일 구조

```
lte_dos/
├── tcp_rrc_flooding_attack.py      # 메인 TCP flooding 공격 스크립트
├── test_tcp_flooding.py            # TCP 테스트 및 분석 스크립트
├── test_tcp_message.py             # 단일 TCP 메시지 테스트
├── analyze_tcp_results.py          # TCP 결과 분석 도구
├── test_single_message.py          # 단일 메시지 테스트 (UDP)
└── logs/                           # 로그 및 결과 저장 디렉토리
```

## 사용법

### 1. 기본 TCP Flooding 공격

```bash
# 기본 설정으로 TCP flooding
python3 tcp_rrc_flooding_attack.py

# 사용자 정의 설정
python3 tcp_rrc_flooding_attack.py --threads 20 --duration 120
```

### 2. 다양한 메시지 타입

```bash
# Connection Request flooding
python3 tcp_rrc_flooding_attack.py --message-type connection_request

# Reestablishment Request flooding
python3 tcp_rrc_flooding_attack.py --message-type reestablishment_request
```

### 3. 단일 메시지 테스트

```bash
# TCP 연결 및 단일 메시지 테스트
python3 test_tcp_message.py --comprehensive

# 특정 메시지 타입 테스트
python3 test_tcp_message.py --message-type reestablishment_request
```

### 4. 종합 테스트

```bash
# srsRAN 상태 확인
python3 test_tcp_flooding.py --check-status

# TCP 연결 확인
python3 test_tcp_flooding.py --check-tcp

# 종합 테스트 실행
python3 test_tcp_flooding.py --comprehensive
```

### 5. 결과 분석

```bash
# TCP 결과 분석
python3 analyze_tcp_results.py
```

## 명령행 옵션

### tcp_rrc_flooding_attack.py

- `--enb-ip`: eNB IP 주소 (기본값: 127.0.0.1)
- `--enb-port`: eNB 포트 (기본값: 2001)
- `--threads`: 동시 스레드 수 (기본값: 10)
- `--duration`: 공격 지속 시간 (초, 기본값: 60)
- `--message-type`: 메시지 타입 (connection_request, reestablishment_request)
- `--generate-samples`: 샘플 메시지 생성

### test_tcp_flooding.py

- `--comprehensive`: 종합 테스트 실행
- `--check-status`: srsRAN 상태만 확인
- `--check-tcp`: TCP 연결만 확인

### test_tcp_message.py

- `--comprehensive`: 종합 테스트 실행
- `--message-type`: 메시지 타입 선택
- `--count`: 연속 메시지 수

## TCP vs UDP 비교

### UDP 기반 (기존)
- **장점**: 빠른 전송 속도
- **단점**: 응답 확인 불가, 연결 상태 불명확
- **용도**: 단순 부하 테스트

### TCP 기반 (새로운)
- **장점**: 실제 연결, 응답 확인, 안정적 통신
- **단점**: 상대적으로 느린 전송 속도
- **용도**: 정확한 공격 효과 측정

## RRC 메시지 형식

### RRCConnectionRequest
```
- Message Type: 1 byte
- UE Identity: 5 bytes (40-bit)
- Establishment Cause: 3 bits
- Spare: 5 bits
```

### RRCConnectionReestablishmentRequest
```
- Message Type: 1 byte
- C-RNTI: 2 bytes (16-bit)
- PCI: 2 bytes (16-bit)
- ShortMAC-I: 2 bytes (16-bit)
```

## 테스트 시나리오

### 1. 기본 TCP Reestablishment Request Flooding
- 5개 스레드, 30초간 실행
- 기본 연결 테스트

### 2. 고강도 TCP Reestablishment Request Flooding
- 10개 스레드, 60초간 실행
- 높은 부하 상황 시뮬레이션

### 3. TCP Connection Request Flooding
- 5개 스레드, 30초간 실행
- 연결 요청 공격

## 모니터링 및 분석

### 시스템 리소스 모니터링
- CPU 사용률
- 메모리 사용량
- 네트워크 트래픽

### TCP 연결 모니터링
- 연결 상태
- 응답 시간
- 응답률

### 공격 효과 분석
- 전송된 메시지 수
- 응답 수신 수
- 응답률
- 평균 응답 시간
- 오류율

## 로그 파일

### TCP Flooding Attack 로그
- `logs/tcp_flooding_attack_YYYYMMDD_HHMMSS.json`
- 공격 설정 및 결과 정보

### TCP 메시지 테스트 로그
- `logs/tcp_message_test_YYYYMMDD_HHMMSS.json`
- 단일 메시지 테스트 결과

### 시스템 모니터링 로그
- `logs/tcp_system_monitor_YYYYMMDD_HHMMSS.log`
- 시스템 리소스 사용 현황

### 분석 보고서
- `logs/tcp_analysis_report_YYYYMMDD_HHMMSS.txt`
- 종합 분석 결과

## 주의사항

### 보안 및 윤리
- **폐쇄된 테스트 환경에서만 사용**
- 실제 운영 네트워크에서 사용 금지
- 법적 및 윤리적 책임은 사용자에게 있음

### 기술적 주의사항
- srsRAN이 정상적으로 실행 중이어야 함
- TCP 포트 2001이 사용 가능해야 함
- 충분한 시스템 리소스 확보 필요
- 네트워크 설정 확인 필요

## 문제 해결

### 일반적인 문제
1. **TCP 연결 실패**: srsRAN 프로세스 확인
2. **응답 없음**: 포트 번호 확인
3. **권한 오류**: sudo 권한 필요할 수 있음
4. **메모리 부족**: 스레드 수 조정

### 디버깅
- 로그 파일 확인
- 시스템 리소스 모니터링
- srsRAN 로그 분석
- TCP 연결 상태 확인

## 참고 자료

- 3GPP TS 36.331: RRC 프로토콜 사양
- srsRAN 공식 문서
- LTE 네트워크 보안 연구
- TCP 소켓 프로그래밍

## 라이선스

이 도구는 교육 및 연구 목적으로만 사용되어야 합니다.
