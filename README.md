# LTE DoS 공격 연구 - UE RRC 메시지 분석 및 Flooding 공격

## 개요
이 프로젝트는 srsRAN 환경에서 UE(User Equipment)가 eNB(eNodeB)에게 보내는 RRC(Radio Resource Control) 메시지를 캡처하고 분석하여, 이를 기반으로 한 DoS(Denial of Service) 공격을 연구합니다.

## 파일 구성

### 1. `capture_ue_packets.py`
**UE가 eNB에게 보내는 RRC 메시지 캡처 및 분석**

#### 기능
- srsUE 실행 시 생성되는 RRC 메시지를 실시간으로 캡처
- tcpdump를 사용하여 루프백 인터페이스에서 패킷 수집
- tshark를 사용하여 패킷 분석 및 RRC 메시지 추출
- 분석 결과를 JSON 형식으로 저장

#### 사용법
```bash
# 패킷 캡처 (60초)
python3 capture_ue_packets.py --duration 60

# 기존 캡처 파일 분석
python3 capture_ue_packets.py --analyze /tmp/ue_packets_20251013_154302.pcap
```

#### 실행 순서
1. **srsUE 실행** (별도 터미널)
   ```bash
   cd /home/tuna/libzmq/czmq/srsRAN_4G/build
   sudo ./srsue/src/srsue --rf.device_name=zmq --rf.device_args="tx_port=tcp://*:2000,rx_port=tcp://localhost:2001,id=ue,base_srate=23.04e6"
   ```

2. **패킷 캡처 실행** (새 터미널)
   ```bash
   python3 capture_ue_packets.py --duration 60
   ```

3. **결과 확인**
   - 생성된 `ue_packet_analysis_*.json` 파일에서 RRC 메시지 확인
   - 각 메시지의 페이로드(16진수) 데이터 분석

### 2. `flooding_attack.py`
**캡처된 RRC 메시지를 기반으로 한 Flooding 공격**

#### 기능
- 분석된 RRC 메시지를 기반으로 다수의 메시지 생성
- 멀티스레드를 사용한 고속 메시지 전송
- 랜덤화를 통한 메시지 변형 (UE ID 등)
- 실시간 통계 및 결과 저장

#### 사용법
```bash
# 기본 Flooding 공격 (10 스레드, 60초)
python3 flooding_attack.py --messages ue_packet_analysis_20251013_154302.json

# 고강도 공격 (20 스레드, 120초)
python3 flooding_attack.py --messages ue_packet_analysis_20251013_154302.json --threads 20 --duration 120

# 빠른 공격 (간격 0.0001초)
python3 flooding_attack.py --messages ue_packet_analysis_20251013_154302.json --interval 0.0001
```

#### 매개변수
- `--target-ip`: 대상 IP 주소 (기본값: 127.0.0.1)
- `--target-port`: 대상 포트 (기본값: 2001)
- `--messages`: RRC 메시지 분석 파일 (필수)
- `--threads`: 스레드 수 (기본값: 10)
- `--duration`: 지속 시간 초 (기본값: 60)
- `--interval`: 메시지 간격 초 (기본값: 0.001)

## 연구 과정

### 1단계: RRC 메시지 캡처
- srsUE를 실행하여 실제 RRC 메시지 생성
- tcpdump로 패킷 캡처
- tshark로 RRC 메시지 추출 및 분석

### 2단계: 메시지 형식 분석
- 캡처된 RRC 메시지의 페이로드 분석
- 메시지 구조 및 필드 파악
- UE ID, 시퀀스 번호 등 변형 가능한 필드 식별

### 3단계: Flooding 공격 구현
- 분석된 메시지를 기반으로 다수의 메시지 생성
- 랜덤화를 통한 메시지 변형
- 멀티스레드를 사용한 고속 전송

### 4단계: 공격 효과 분석
- 전송 속도 및 성공률 측정
- 시스템 리소스 사용량 모니터링
- eNB 로그 분석을 통한 공격 효과 확인

## 예상 결과

### RRC 메시지 캡처
- srsUE 실행 시 RRC Connection Request, RRC Connection Reestablishment Request 등 캡처
- 각 메시지의 16진수 페이로드 데이터 추출
- 메시지 크기, 전송 시간, 응답 패턴 분석

### Flooding 공격
- 초당 수천 개의 RRC 메시지 전송
- eNB의 RRC 처리 능력 초과
- 정상 UE의 연결 요청 처리 지연 또는 실패

## 기술적 배경

### RRC (Radio Resource Control)
- LTE 네트워크의 Layer 3 프로토콜
- UE와 eNB 간의 무선 자원 제어
- 연결 설정, 해제, 재설정 등 담당

### srsRAN
- 오픈소스 LTE/5G 소프트웨어 스택
- eNB, UE, EPC 구현
- ZMQ 기반 RF 디바이스 지원

### DoS 공격
- 서비스 거부 공격
- 대량의 요청으로 시스템 과부하 유발
- 정상 사용자의 서비스 이용 방해

## 주의사항
- 이 연구는 교육 및 보안 연구 목적입니다
- 실제 네트워크에서의 사용은 법적 문제가 될 수 있습니다
- 테스트 환경에서만 사용하세요

## 문제 해결

### srsUE 실행 오류
- RF 디바이스 설정 확인
- ZMQ 포트 설정 확인
- 권한 문제 해결 (sudo 사용)

### 패킷 캡처 실패
- tcpdump 권한 확인
- 네트워크 인터페이스 확인
- 포트 번호 확인

### Flooding 공격 실패
- 대상 서비스 실행 상태 확인
- 네트워크 연결 확인
- 방화벽 설정 확인

## 결론
이 연구를 통해 UE가 eNB에게 보내는 RRC 메시지의 형식을 분석하고, 이를 기반으로 한 DoS 공격의 가능성을 확인했습니다. 실제 RRC 메시지를 캡처하여 분석한 결과, 메시지 구조를 파악하고 변형하여 대량 전송이 가능함을 확인했습니다.
