import os
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# kaggle.json 자동 생성 및 복사
KAGGLE_DIR = Path.home() / ".kaggle"
KAGGLE_DIR.mkdir(exist_ok=True)
KAGGLE_JSON = KAGGLE_DIR / "kaggle.json"

if not KAGGLE_JSON.exists():
    print("kaggle.json 생성 중...")
    username = os.getenv("KAGGLE_USERNAME")
    key = os.getenv("KAGGLE_KEY")

    if not username or not key:
        raise ValueError("오류: .env 파일에 KAGGLE_USERNAME 또는 KAGGLE_KEY가 없습니다!")

    config = f'{{"username":"{username}","key":"{key}"}}'
    KAGGLE_JSON.write_text(config)
    try:
        KAGGLE_JSON.chmod(0o600)
    except:
        pass  # Windows는 무시
    print(f"kaggle.json 생성 완료: {KAGGLE_JSON}")
else:
    print("kaggle.json 이미 존재함")

# 이제 import (인증 자동 수행)
import kaggle
import pandas as pd
import google.generativeai as genai

# 환경 변수 재설정 (안전장치)
os.environ['KAGGLE_USERNAME'] = os.getenv("KAGGLE_USERNAME")
os.environ['KAGGLE_KEY'] = os.getenv("KAGGLE_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Kaggle 인증 성공!")
kaggle.api.authenticate()

print("데이터 다운로드 중...")
kaggle.api.dataset_download_files('muhammetvarl/laptop-price', path='.', unzip=True)

print("데이터 로드 중...")
df = pd.read_csv('laptop_price.csv', encoding='cp1252')
df['Ram'] = df['Ram'].str.replace('GB', '').astype(int)
df['Inches'] = pd.to_numeric(df['Inches'], errors='coerce')

# 가성비 필터
budget = df[df['Price_euros'] <= 1000]
top10 = budget[(budget['Ram'] >= 8) & (budget['Inches'] >= 15)].sort_values('Price_euros').head(10)

if top10.empty:
    print("조건에 맞는 노트북이 없습니다!")
else:
    print(f"총 {len(top10)}대 발견! Gemini에게 추천 요청 중...")

    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    가격 1000유로 이하, RAM 8GB 이상, 15인치 이상 노트북 중
    진짜 가성비 TOP 3 추천해줘!
    이유는 간단명료하게!

    {top10[['Company','Product','Cpu','Ram','Price_euros']].to_string(index=False)}
    """

    response = model.generate_content(prompt)
    print("\n" + "="*60)
    print("GEMINI 가성비 TOP 3")
    print("="*60)
    print(response.text)
    print("="*60)

    top10.to_csv('top_value_laptops.csv', index=False, encoding='utf-8-sig')
    print("top_value_laptops.csv 저장 완료! 엑셀로 열어보세요!")