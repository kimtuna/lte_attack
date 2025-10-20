#!/usr/bin/env python3
"""
의존성 설치 스크립트 (Ubuntu/Debian 환경)
DoS 공격 분석 도구에 필요한 Python 패키지들을 시스템 패키지로 설치합니다.
"""

import subprocess
import sys
import os

def run_command(cmd):
    """명령어 실행"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 명령어 실행 성공: {cmd}")
            return True
        else:
            print(f"❌ 명령어 실행 실패: {cmd}")
            print(f"오류: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 명령어 실행 오류: {e}")
        return False

def install_system_packages():
    """시스템 패키지 설치"""
    print("=== Ubuntu/Debian 시스템 패키지 설치 ===")
    
    # 패키지 목록 업데이트
    print("\n📦 패키지 목록 업데이트 중...")
    if not run_command("sudo apt update"):
        return False
    
    # 필요한 패키지들
    packages = [
        "python3-psutil",      # 시스템 모니터링
        "python3-matplotlib", # 그래프 생성
        "python3-numpy",      # 수치 계산
        "python3-pandas",     # 데이터 처리
        "python3-seaborn",    # 고급 시각화
    ]
    
    print(f"\n📦 설치할 패키지: {', '.join(packages)}")
    
    # 한 번에 설치
    install_cmd = f"sudo apt install -y {' '.join(packages)}"
    print(f"\n🔧 설치 명령어: {install_cmd}")
    
    if run_command(install_cmd):
        print("\n🎉 모든 시스템 패키지 설치가 완료되었습니다!")
        return True
    else:
        print("\n⚠️  시스템 패키지 설치에 실패했습니다.")
        return False

def verify_installation():
    """설치 확인"""
    print("\n🔍 설치 확인 중...")
    
    try:
        import psutil
        import matplotlib
        import numpy
        import pandas
        import seaborn
        print("✅ 모든 패키지가 정상적으로 설치되었습니다!")
        return True
    except ImportError as e:
        print(f"❌ 패키지 확인 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=== DoS 공격 분석 도구 의존성 설치 (Ubuntu 환경) ===")
    
    # 시스템 확인
    if os.name != 'posix':
        print("❌ 이 스크립트는 Linux/Unix 환경에서만 실행됩니다.")
        return
    
    # 설치 실행
    if install_system_packages():
        # 설치 확인
        if verify_installation():
            print("\n🎯 설치 완료! 이제 다음 명령어로 도구를 사용할 수 있습니다:")
            print("1. 메모리 모니터링: python3 memory_analysis.py --monitor-only")
            print("2. 시뮬레이션 실행: python3 memory_analysis.py --duration 10 --intensity medium")
            print("3. 통합 분석: python3 integrated_dos_analyzer.py --messages your_messages.json")
            print("4. 메모리 시각화: python3 memory_visualizer.py --data your_data.json")
        else:
            print("\n⚠️  설치 확인에 실패했습니다. 수동으로 확인해주세요.")
    else:
        print("\n❌ 설치에 실패했습니다. 수동으로 설치해주세요:")
        print("sudo apt install python3-psutil python3-matplotlib python3-numpy python3-pandas python3-seaborn")

if __name__ == "__main__":
    main()
