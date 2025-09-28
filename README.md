# LTE Resource Depletion Attack 테스트 환경

srsRAN LTE 테스트 환경에서 Resource Depletion DoS 공격을 테스트하기 위한 도구 모음입니다.

## 공격 유형

### 1. RRC Connection Flood (`rrc_connection_flood.py`)
- **목적**: 대량의 RRC 연결 요청으로 eNB의 리소스 고갈
- **방법**: 500개의 가상 UE가 동시에 RRC Connection Request 전송
- **영향**: eNB의 연결 처리 능력 초과

### 2. Paging Storm (`paging_storm_attack.py`)
- **목적**: 대량의 Paging 메시지로 UE의 리소스 고갈
- **방법**: 20개 스레드가 100개씩 Paging 메시지를 0.05초 간격으로 전송
- **영향**: UE의 배터리 및 처리 리소스 고갈

### 3. NAS Signaling Flood (`nas_signaling_flood.py`)
- **목적**: NAS 시그널링 메시지로 MME의 리소스 고갈
- **방법**: 300개 UE가 Attach/TAU/Detach 요청을 랜덤하게 전송
- **영향**: MME의 시그널링 처리 능력 초과

### 4. Bearer Setup Flood (`bearer_setup_flood.py`)
- **목적**: Bearer 설정 요청으로 네트워크 리소스 고갈
- **방법**: 200개 UE가 Bearer Setup/Modify 요청을 전송
- **영향**: 네트워크의 Bearer 관리 리소스 고갈

## 사용 방법

### 1. 개별 공격 실행
```bash
# RRC Connection Flood
python3 rrc_connection_flood.py

# Paging Storm
python3 paging_storm_attack.py

# NAS Signaling Flood
python3 nas_signaling_flood.py

# Bearer Setup Flood
python3 bearer_setup_flood.py
```

### 2. 모든 공격 순차 실행
```bash
# 로컬 환경
python3 attack_runner.py

# 클라우드 환경 (IP 지정)
python3 attack_runner.py 192.168.1.100
```

### 3. Wireshark 모니터링
```bash
# 별도 터미널에서 실행
python3 wireshark_monitor.py
```

## 설정 변경

각 공격 스크립트에서 다음 파라미터를 조정할 수 있습니다:

- `target_ip`: 공격 대상 IP 주소
- `target_port`: srsRAN 포트 (기본: 36412)
- `num_ues`: 동시 UE 수
- `duration`: 공격 지속 시간 (초)
- `num_threads`: 공격 스레드 수

## 모니터링

### Wireshark 필터
```
# RRC 메시지
udp.port == 36412

# Paging 메시지
udp.port == 36422

# NAS 메시지
udp.port == 36432

# 전체 LTE 트래픽
udp.port == 36412 or udp.port == 36422 or udp.port == 36432
```

### 시스템 모니터링
```bash
# CPU 사용률
top -p $(pgrep -f srs)

# 메모리 사용률
ps aux | grep srs

# 네트워크 트래픽
iftop -i any

# 포트 사용률
netstat -tulpn | grep 36412
```

## 주의사항

1. **테스트 환경에서만 사용**: 실제 운영 네트워크에서는 사용하지 마세요
2. **리소스 모니터링**: 공격 중 시스템 리소스를 모니터링하세요
3. **네트워크 대역폭**: 대량 트래픽으로 인한 네트워크 혼잡을 고려하세요
4. **법적 책임**: 테스트 환경에서만 사용하고, 적절한 권한을 받은 후 실행하세요

## 결과 분석

공격 실행 후 다음 파일들이 생성됩니다:

- `attack_results.json`: 공격 실행 결과
- `attack_stats.json`: Wireshark 모니터링 통계
- `lte_attack_capture.pcap`: 캡처된 네트워크 트래픽

## 문제 해결

### 공격이 작동하지 않는 경우
1. srsRAN 프로세스가 실행 중인지 확인
2. 네트워크 인터페이스 설정 확인
3. 방화벽 설정 확인
4. 포트 번호 확인

### 성능 문제
1. UE 수를 줄여서 테스트
2. 공격 지속 시간을 단축
3. 시스템 리소스 확인

## 추가 정보

- srsRAN 공식 문서: https://docs.srsran.com/
- LTE 시그널링 프로토콜: 3GPP TS 36.331, 36.413
- Wireshark LTE 필터: https://wiki.wireshark.org/LTE
