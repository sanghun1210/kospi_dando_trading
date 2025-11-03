"""
F-Score 결과 분석 스크립트
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # GUI 없이 그래프 생성
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'  # Mac
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 데이터 로드
df = pd.read_csv('fscore_parallel_results_20251101.csv')

print("="*60)
print("📊 F-Score 결과 종합 분석")
print("="*60)

# 1. 전체 통계
print(f"\n1️⃣ 전체 통계")
print(f"  - 총 종목 수: {len(df)}개")
print(f"  - 평균 점수: {df['score'].mean():.2f}점")
print(f"  - 중앙값: {df['score'].median():.0f}점")

# 2. 점수별 분포
print(f"\n2️⃣ 점수별 분포")
score_dist = df['score'].value_counts().sort_index(ascending=False)
for score, count in score_dist.items():
    pct = count / len(df) * 100
    print(f"  {score}점: {count}개 ({pct:.1f}%)")

# 3. 6점 만점 종목 분석
print(f"\n3️⃣ 6점 만점 종목 분석 (74개)")
perfect_scores = df[df['score'] == 6].copy()

# ROA 증가율 분석
perfect_scores['roa_change'] = perfect_scores['roa_current'] - perfect_scores['roa_previous']
print(f"\n  ROA 증가 통계:")
print(f"  - 평균 증가: {perfect_scores['roa_change'].mean():.2f}%p")
print(f"  - 중앙값: {perfect_scores['roa_change'].median():.2f}%p")
print(f"  - 최대 증가: {perfect_scores['roa_change'].max():.2f}%p")

# ROA 증가율 Top 5
print(f"\n  ROA 증가율 Top 5:")
top_roa = perfect_scores.nlargest(5, 'roa_change')[['name', 'code', 'roa_previous', 'roa_current', 'roa_change']]
for idx, row in top_roa.iterrows():
    print(f"    {row['name']} ({row['code']}): {row['roa_previous']:.2f}% → {row['roa_current']:.2f}% (+{row['roa_change']:.2f}%p)")

# 부채비율 감소 분석
perfect_scores['debt_change'] = perfect_scores['debt_ratio_previous'] - perfect_scores['debt_ratio_current']
print(f"\n  부채비율 감소 통계:")
print(f"  - 평균 감소: {perfect_scores['debt_change'].mean():.2f}%p")
print(f"  - 최대 감소: {perfect_scores['debt_change'].max():.2f}%p")

# 영업이익률 증가 분석
perfect_scores['margin_change'] = perfect_scores['operating_margin_current'] - perfect_scores['operating_margin_previous']
print(f"\n  영업이익률 증가 통계:")
print(f"  - 평균 증가: {perfect_scores['margin_change'].mean():.2f}%p")

# 영업이익률 증가 Top 5
print(f"\n  영업이익률 증가 Top 5:")
top_margin = perfect_scores.nlargest(5, 'margin_change')[['name', 'code', 'operating_margin_previous', 'operating_margin_current', 'margin_change']]
for idx, row in top_margin.iterrows():
    print(f"    {row['name']} ({row['code']}): {row['operating_margin_previous']:.2f}% → {row['operating_margin_current']:.2f}% (+{row['margin_change']:.2f}%p)")

# 4. 대형주 vs 중소형주
print(f"\n4️⃣ 주목할 만한 대형주 (6점 만점)")
# 임의로 유명 기업들 찾기
famous_companies = ['삼성', 'LG', '현대', 'SK', '롯데', '포스코', 'KT']
notable = perfect_scores[perfect_scores['name'].str.contains('|'.join(famous_companies), na=False)]
if len(notable) > 0:
    print(f"  발견된 대형주 ({len(notable)}개):")
    for idx, row in notable.iterrows():
        print(f"    - {row['name']} ({row['code']})")
else:
    print("  없음")

# 5. 섹터별 분석 (종목명 기준 추정)
print(f"\n5️⃣ 업종별 분포 (종목명 기반 추정)")
keywords = {
    '바이오/제약': ['바이오', '팜', '제약', '메디', '헬스'],
    '반도체/IT': ['반도체', '일렉', '테크', '시스템', '전자'],
    '소재/화학': ['케미', '화학', '소재', '머트리얼'],
    '에너지': ['에너지', '전력', '가스'],
    '유통/식품': ['식품', '에프앤비', '마트', '유통'],
}

for sector, words in keywords.items():
    pattern = '|'.join(words)
    count = len(perfect_scores[perfect_scores['name'].str.contains(pattern, na=False, case=False)])
    if count > 0:
        print(f"  {sector}: {count}개")

# 6. 적자→흑자 전환 종목
print(f"\n6️⃣ 턴어라운드 종목 (적자→흑자)")
turnaround = perfect_scores[perfect_scores['roa_previous'] < 0]
if len(turnaround) > 0:
    print(f"  발견된 턴어라운드 종목 ({len(turnaround)}개):")
    for idx, row in turnaround.iterrows():
        print(f"    - {row['name']} ({row['code']}): {row['roa_previous']:.2f}% → {row['roa_current']:.2f}%")

# 7. 그래프 생성
print(f"\n7️⃣ 시각화 그래프 생성 중...")

# 7-1. 점수 분포 그래프
plt.figure(figsize=(10, 6))
score_dist.plot(kind='bar', color=['#2ecc71', '#3498db', '#f39c12'])
plt.title('F-Score 점수별 분포', fontsize=16, fontweight='bold')
plt.xlabel('점수', fontsize=12)
plt.ylabel('종목 수', fontsize=12)
plt.xticks(rotation=0)
plt.grid(axis='y', alpha=0.3)
for i, v in enumerate(score_dist.values):
    plt.text(i, v + 5, str(v), ha='center', va='bottom', fontweight='bold')
plt.tight_layout()
plt.savefig('fscore_distribution.png', dpi=150)
print("  ✅ fscore_distribution.png 저장 완료")

# 7-2. 6점 만점 종목 ROA 변화
plt.figure(figsize=(12, 8))
top_20_roa = perfect_scores.nlargest(20, 'roa_change')
x = range(len(top_20_roa))
plt.barh(x, top_20_roa['roa_change'], color='#2ecc71')
plt.yticks(x, top_20_roa['name'])
plt.xlabel('ROA 증가율 (%p)', fontsize=12)
plt.title('6점 만점 종목 - ROA 증가율 Top 20', fontsize=16, fontweight='bold')
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('fscore_roa_change.png', dpi=150)
print("  ✅ fscore_roa_change.png 저장 완료")

# 8. 최종 추천 종목 (6점 + ROA 증가율 높음)
print(f"\n8️⃣ 최종 추천 종목 Top 10")
print("  (6점 만점 + ROA 증가율 기준)")
recommendations = perfect_scores.nlargest(10, 'roa_change')[['name', 'code', 'roa_change', 'debt_ratio_current', 'operating_margin_current']]
print(f"\n  {'순위':<4} {'종목명':<20} {'종목코드':<10} {'ROA증가':<10} {'부채비율':<10} {'영업이익률'}")
print("  " + "-"*75)
for i, (idx, row) in enumerate(recommendations.iterrows(), 1):
    print(f"  {i:<4} {row['name']:<20} {row['code']:<10} +{row['roa_change']:>6.2f}%p  {row['debt_ratio_current']:>6.2f}%  {row['operating_margin_current']:>8.2f}%")

print("\n" + "="*60)
print("✅ 분석 완료!")
print("="*60)
