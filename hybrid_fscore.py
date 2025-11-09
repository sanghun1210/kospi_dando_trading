"""
Hybrid F-Score 시스템

2단계 효율적 분석:
1단계: Lite F-Score (6/9) → 전체 2,631개 (4.5분)
2단계: Full F-Score (9/9) → 상위 200개 (7분)

총 소요 시간: 약 11.5분
"""

import pandas as pd
from datetime import datetime
from parallel_fscore import ParallelFScoreSelector
from parallel_fscore_full import ParallelFullFScoreSelector
from sector_utils import DEFAULT_SECTOR, get_sector_lookup
from opendart_client import OpenDartClient


class HybridFScoreSystem:
    """Hybrid F-Score 분석 시스템"""

    def __init__(self, opendart_api_key):
        """
        Parameters:
        -----------
        opendart_api_key : str
            OpenDart API 인증키
        """
        self.opendart_api_key = opendart_api_key
        self.dart_client = OpenDartClient(opendart_api_key)

    def run(
        self,
        top_n=200,
        final_min_score=7,
        lite_max_count=None,
        lite_workers=6,
    ):
        """
        Hybrid 분석 실행

        Parameters:
        -----------
        top_n : int
            1단계에서 선정할 상위 종목 수 (기본: 200)
        final_min_score : int
            최종 필터링 최소 점수 (기본: 7점)
        lite_max_count : int
            Lite F-Score 테스트용 최대 종목 수 (None=전체)

        Returns:
        --------
        df_final : DataFrame
            최종 분석 결과
        """
        print("="*60)
        print("🚀 Hybrid F-Score 분석 시스템")
        print("="*60)
        print(f"전략: Lite (전체) → Full (상위 {top_n}개)")
        print("="*60)

        # ========================================
        # 1단계: Lite F-Score (6/9) - 전체 스캔
        # ========================================
        print(f"\n{'='*60}")
        print(f"1️⃣ 1단계: Lite F-Score (6/9) 전체 스캔")
        print(f"{'='*60}\n")

        lite_selector = ParallelFScoreSelector(
            use_existing_data=True,
            max_workers=lite_workers,
            opendart_client=self.dart_client,
        )

        # 종목 리스트 가져오기
        ticker_list = lite_selector.get_ticker_list()

        # 전체 Lite F-Score 계산
        lite_results = lite_selector.calculate_fscores_parallel(ticker_list, max_count=lite_max_count)

        if len(lite_results) == 0:
            print("⚠️  Lite F-Score 결과가 없습니다.")
            return None

        df_lite = pd.DataFrame(lite_results)
        df_lite = self._apply_sector_adjustments(df_lite)

        sort_columns = ['score']
        if 'adjusted_score' in df_lite.columns:
            sort_columns = ['adjusted_score', 'score']

        df_lite_ranked = df_lite.sort_values(sort_columns, ascending=False).reset_index(drop=True)

        print(f"\n📊 Lite F-Score 결과:")
        print(f"  - 총 분석: {len(df_lite)}개")
        print(f"  - 평균 점수: {df_lite['score'].mean():.2f}점")

        # 점수 분포
        score_dist = df_lite['score'].value_counts().sort_index(ascending=False)
        print(f"\n  점수 분포:")
        for score, count in score_dist.items():
            print(f"    {score}점: {count}개")

        # 상위 N개 선정
        df_top = df_lite_ranked.head(top_n).copy()
        top_codes = df_top['code'].tolist()
        top_names = df_top['name'].tolist()
        sector_meta = df_top.set_index('code')[['sector', 'sector_relative_strength', 'adjusted_score']].to_dict('index')

        print(f"\n  ✅ 상위 {len(df_top)}개 종목 선정")
        print(f"     (점수 범위: {df_top['score'].min()}~{df_top['score'].max()}점)")

        # Lite 결과 저장
        today = datetime.now().strftime('%Y%m%d')
        lite_filename = f'hybrid_lite_results_{today}.csv'
        lite_selector.save_results(df_lite_ranked, lite_filename)

        # ========================================
        # 2단계: Full F-Score (9/9) - 상위만
        # ========================================
        print(f"\n{'='*60}")
        print(f"2️⃣ 2단계: Full F-Score (9/9) 정밀 분석")
        print(f"{'='*60}\n")

        full_selector = ParallelFullFScoreSelector(
            opendart_api_key=self.opendart_api_key,
            use_existing_data=False,  # ticker_list 직접 제공
            max_workers=10
        )

        # 상위 종목만 Full F-Score 계산
        top_ticker_list = list(zip(top_codes, top_names))
        full_results = full_selector.calculate_fscores_parallel(top_ticker_list, max_count=None)

        if len(full_results) == 0:
            print("⚠️  Full F-Score 결과가 없습니다.")
            return df_lite_ranked

        # 최종 결과
        df_full = pd.DataFrame(full_results)
        df_full = self._attach_sector_context(df_full, sector_meta)
        df_full_ranked = df_full.sort_values(
            ['score', 'sector_relative_strength'],
            ascending=False
        ).reset_index(drop=True)

        print(f"\n📊 Full F-Score 결과:")
        print(f"  - 총 분석: {len(df_full)}개")
        print(f"  - 평균 점수: {df_full['score'].mean():.2f}점")

        # 점수 분포
        score_dist_full = df_full['score'].value_counts().sort_index(ascending=False)
        print(f"\n  점수 분포:")
        for score, count in score_dist_full.items():
            print(f"    {score}점: {count}개")

        # 최종 필터링
        df_final = df_full_ranked[df_full_ranked['score'] >= final_min_score].copy()
        print(f"\n  ✅ {final_min_score}점 이상: {len(df_final)}개")

        if 'sector' in df_final.columns:
            sector_counts = df_final['sector'].value_counts().head(10)
            print("\n  📌 섹터 상위 분포:")
            for sector, count in sector_counts.items():
                print(f"    - {sector}: {count}개")

        # Full 결과 저장
        full_filename = f'hybrid_full_results_{today}.csv'
        full_selector.save_results(df_full_ranked, full_filename)

        # ========================================
        # 최종 요약
        # ========================================
        print(f"\n{'='*60}")
        print(f"✅ Hybrid 분석 완료")
        print(f"{'='*60}\n")

        print(f"📊 최종 추천 종목: {len(df_final)}개\n")

        # 상위 20개 출력
        print(f"🏆 상위 20개 종목:")
        print(f"{'='*60}")
        for idx, row in df_final.head(20).iterrows():
            lite_score = row['details'].get('lite_score', 0)
            additional_score = row['details'].get('additional_score', 0)
            print(f"{idx+1}. {row['name']} ({row['code']})")
            sector_str = row.get('sector', DEFAULT_SECTOR)
            srs = row.get('sector_relative_strength', 0.0)
            print(f"   Full: {row['score']}/9 ⭐ (Lite: {lite_score}/6 + OpenDart: {additional_score}/3)")
            print(f"   Sector: {sector_str} | 상대강도 +{srs:.2f}")

        print(f"{'='*60}\n")

        # HTML 리포트 생성
        full_selector.generate_email_report(df_final, top_n=30)

        return df_final

    def _apply_sector_adjustments(self, df_lite: pd.DataFrame) -> pd.DataFrame:
        """섹터별 기준선을 반영해 Lite 단계 점수를 보정한다."""
        if df_lite.empty:
            return df_lite

        df = df_lite.copy()

        try:
            sector_lookup = get_sector_lookup()
        except Exception:
            sector_lookup = {}

        df['sector'] = df['code'].astype(str).str.zfill(6).map(sector_lookup).fillna(DEFAULT_SECTOR)

        metric_defs = [
            ('roa_current', True),
            ('operating_margin_current', True),
            ('asset_turnover_current', True),
            ('debt_ratio_current', False),
        ]

        for metric_key, _ in metric_defs:
            df[metric_key] = df['details'].apply(
                lambda detail: detail.get(metric_key) if isinstance(detail, dict) else None
            )

        bonus_cols = []
        for metric_key, higher_better in metric_defs:
            sector_median = df.groupby('sector')[metric_key].transform('median')
            if higher_better:
                beats = df[metric_key] > sector_median
            else:
                beats = df[metric_key] < sector_median

            col_name = f"{metric_key}_beats_sector"
            df[col_name] = beats
            bonus_cols.append(col_name)

        if bonus_cols:
            bonus_frame = df[bonus_cols].astype(float)
            df['sector_relative_strength'] = bonus_frame.mean(axis=1, skipna=True).fillna(0.0)
            df['adjusted_score'] = df['score'] + df['sector_relative_strength']
        else:
            df['sector_relative_strength'] = 0.0
            df['adjusted_score'] = df['score']

        unique_sectors = df['sector'].nunique()
        print(f"\n📌 섹터 상대평가 적용 완료 ({unique_sectors}개 섹터)")

        return df

    def _attach_sector_context(self, df_full: pd.DataFrame, sector_meta):
        """Full 단계 결과에 Lite 단계 섹터 정보를 병합한다."""
        if df_full.empty:
            return df_full

        if not sector_meta:
            df_full['sector'] = DEFAULT_SECTOR
            df_full['sector_relative_strength'] = 0.0
            df_full['lite_adjusted_score'] = None
            return df_full

        df_full['sector'] = df_full['code'].map(lambda c: sector_meta.get(c, {}).get('sector', DEFAULT_SECTOR))
        df_full['sector_relative_strength'] = df_full['code'].map(
            lambda c: sector_meta.get(c, {}).get('sector_relative_strength', 0.0)
        ).fillna(0.0)
        df_full['lite_adjusted_score'] = df_full['code'].map(
            lambda c: sector_meta.get(c, {}).get('adjusted_score')
        )

        return df_full


def main(test_mode=True):
    """
    메인 실행

    Parameters:
    -----------
    test_mode : bool
        테스트 모드 여부 (True: 소규모, False: 전체)
    """
    api_key = "0893a49ad29a0b7fc3b47bf0a26fa580a1c10808"

    system = HybridFScoreSystem(api_key)

    if test_mode:
        print("\n⚠️  테스트 모드 활성화")
        print("   - Lite: 상위 100개만")
        print("   - Full: 상위 30개만\n")

        df_final = system.run(
            top_n=30,  # 상위 30개만 Full 분석
            final_min_score=6,  # 6점 이상
            lite_max_count=100  # Lite도 100개만
        )
    else:
        # 전체 실행
        df_final = system.run(
            top_n=200,  # 상위 200개 Full 분석
            final_min_score=7,  # 7점 이상 최종 선정
            lite_max_count=None  # Lite 전체
        )

    if df_final is not None:
        print(f"\n✅ 모든 작업 완료!")
        print(f"   최종 {len(df_final)}개 우량 종목 발굴")
    else:
        print(f"\n⚠️  분석 실패")


if __name__ == "__main__":
    main()
