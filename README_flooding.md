# srsRAN eNB RRC Flooding Attack

srsRAN 환경에서 eNB에 대한 RRC 메시지 기반 flooding 공격을 수행하는 도구입니다.

## 개요

이 도구는 실제 RRC 메시지 형식을 기반으로 srsRAN eNB에 대량의 RRC 메시지를 전송하여 네트워크 부하를 발생시키는 flooding 공격을 수행합니다.

## 주요 기능

### 1. RRC 메시지 생성
- **RRCConnectionRequest**: UE가 eNB에 연결을 요청하는 메시지
- **RRCConnectionReestablishmentRequest**: 연결 재설정 요청 메시지
- 3GPP TS 36.331 표준에 따른 정확한 메시지 형식

### 2. Flooding 공격
- 멀티스레딩을 통한 동시 메시지 전송
- 다양한 전송 속도 및 패턴 지원
- 실시간 통계 및 모니터링

### 3. 테스트 및 분석
- 시스템 리소스 모니터링
- 공격 효과 분석
- 로그 기록 및 저장

## 파일 구조

```
lte_dos/
├── rrc_flooding_attack.py      # 메인 flooding 공격 스크립트
├── test_rrc_flooding.py        # 테스트 및 분석 스크립트
├── capture_real_ue_rrc.py      # 실제 UE RRC 메시지 캡처
└── logs/                       # 로그 및 결과 저장 디렉토리
```

## 사용법

### 1. 기본 Flooding 공격

```bash
# 기본 설정으로 Connection Request flooding
python3 rrc_flooding_attack.py

# 사용자 정의 설정
python3 rrc_flooding_attack.py --enb-ip 192.168.1.100 --threads 20 --duration 120
```

### 2. 다양한 메시지 타입

```bash
# Connection Request flooding
python3 rrc_flooding_attack.py --message-type connection_request

# Reestablishment Request flooding
python3 rrc_flooding_attack.py --message-type reestablishment_request
```

### 3. 샘플 메시지 생성

```bash
# RRC 메시지 샘플 생성
python3 rrc_flooding_attack.py --generate-samples
```

### 4. 테스트 실행

```bash
# srsRAN 상태 확인
python3 test_rrc_flooding.py --check-status

# 종합 테스트 실행
python3 test_rrc_flooding.py --comprehensive
```

## 명령행 옵션

### rrc_flooding_attack.py

- `--enb-ip`: eNB IP 주소 (기본값: 127.0.0.1)
- `--enb-port`: eNB 포트 (기본값: 2000)
- `--threads`: 동시 스레드 수 (기본값: 10)
- `--duration`: 공격 지속 시간 (초, 기본값: 60)
- `--message-type`: 메시지 타입 (connection_request, reestablishment_request)
- `--generate-samples`: 샘플 메시지 생성

### test_rrc_flooding.py

- `--comprehensive`: 종합 테스트 실행
- `--check-status`: srsRAN 상태만 확인

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

### 1. 기본 Connection Request Flooding
- 5개 스레드, 30초간 실행
- 일반적인 부하 테스트

### 2. 고강도 Connection Request Flooding
- 20개 스레드, 60초간 실행
- 높은 부하 상황 시뮬레이션

### 3. Reestablishment Request Flooding
- 10개 스레드, 30초간 실행
- 연결 재설정 공격

## 모니터링 및 분석

### 시스템 리소스 모니터링
- CPU 사용률
- 메모리 사용량
- 네트워크 트래픽

### 공격 효과 분석
- 전송된 메시지 수
- 오류율
- 성공률
- 초당 메시지 처리량

## 로그 파일

### Flooding Attack 로그
- `logs/flooding_attack_YYYYMMDD_HHMMSS.json`
- 공격 설정 및 결과 정보

### 시스템 모니터링 로그
- `logs/system_monitor_YYYYMMDD_HHMMSS.log`
- 시스템 리소스 사용 현황

### 샘플 메시지 로그
- `logs/rrc_message_samples_YYYYMMDD_HHMMSS.json`
- 생성된 RRC 메시지 샘플

## 주의사항

### 보안 및 윤리
- **폐쇄된 테스트 환경에서만 사용**
- 실제 운영 네트워크에서 사용 금지
- 법적 및 윤리적 책임은 사용자에게 있음

### 기술적 주의사항
- srsRAN이 정상적으로 실행 중이어야 함
- 충분한 시스템 리소스 확보 필요
- 네트워크 설정 확인 필요

## 문제 해결

### 일반적인 문제
1. **연결 실패**: eNB IP/포트 확인
2. **권한 오류**: sudo 권한 필요할 수 있음
3. **메모리 부족**: 스레드 수 조정

### 디버깅
- 로그 파일 확인
- 시스템 리소스 모니터링
- srsRAN 로그 분석

## 참고 자료

- 3GPP TS 36.331: RRC 프로토콜 사양
- srsRAN 공식 문서
- LTE 네트워크 보안 연구

## 라이선스

이 도구는 교육 및 연구 목적으로만 사용되어야 합니다.
