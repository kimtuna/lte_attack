#!/usr/bin/env python3
"""
의존성 설치 스크립트
DoS 공격 분석 도구에 필요한 Python 패키지들을 설치합니다.
"""

import subprocess
import sys

def install_package(package):
    """패키지 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 설치 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("=== DoS 공격 분석 도구 의존성 설치 ===")
    
    # 필요한 패키지 목록
    required_packages = [
        "psutil",           # 시스템 모니터링
        "matplotlib",       # 그래프 생성
        "numpy",           # 수치 계산
        "pandas",          # 데이터 처리
        "seaborn",         # 고급 시각화
    ]
    
    print(f"설치할 패키지: {', '.join(required_packages)}")
    print()
    
    # 패키지 설치
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print()
    print(f"설치 완료: {success_count}/{len(required_packages)} 패키지")
    
    if success_count == len(required_packages):
        print("🎉 모든 의존성 설치가 완료되었습니다!")
    else:
        print("⚠️  일부 패키지 설치에 실패했습니다. 수동으로 설치해주세요.")
        print("pip install psutil matplotlib numpy pandas seaborn")

if __name__ == "__main__":
    main()
