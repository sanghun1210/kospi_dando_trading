"""
완전 통합 분석 실행 스크립트

F-Score (재무) + 기술적 분석 (차트) 한 번에 실행
"""

import argparse
import os
import sys
from datetime import datetime

from hybrid_fscore import HybridFScoreSystem
from hybrid_fscore_timing import HybridFScoreTiming


def parse_args():
    parser = argparse.ArgumentParser(
        description="F-Score + 타이밍 분석 완전 통합 실행"
    )

    # OpenDart API
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENDART_API_KEY"),
        help="OpenDart API 키 (미지정 시 환경변수 OPENDART_API_KEY 사용)",
    )

    # F-Score 설정
    parser.add_argument(
        "--min-fscore",
        type=int,
        default=4,
        help="타이밍 분석 대상 최소 F-Score (기본: 4점)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=200,
        help="Lite 단계에서 Full 분석으로 넘길 종목 수 (기본: 200)",
    )

    # 타이밍 분석 설정
    parser.add_argument(
        "--timing-source",
        type=str,
        choices=["auto", "full", "lite"],
        default="auto",
        help="타이밍 분석 대상 (auto: Full 우선→Lite, full: Full만, lite: Lite만)",
    )
    parser.add_argument(
        "--timing-workers",
        type=int,
        default=3,
        help="타이밍 분석 병렬 워커 수 (기본: 3, 안정성 우선)",
    )
    parser.add_argument(
        "--timing-max-count",
        type=int,
        default=None,
        help="타이밍 분석 최대 종목 수 (None이면 전체)",
    )
    parser.add_argument(
        "--min-timing-score",
        type=float,
        default=5.0,
        help="최종 추천 최소 타이밍 점수 (기본: 5.0)",
    )

    # 실행 모드
    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트 모드 (Lite 100개, 타이밍 20개만)",
    )
    parser.add_argument(
        "--skip-fscore",
        action="store_true",
        help="F-Score 계산 생략하고 기존 결과 사용",
    )
    parser.add_argument(
        "--fscore-only",
        action="store_true",
        help="F-Score만 계산하고 타이밍 분석 생략",
    )

    return parser.parse_args()


def run_fscore_analysis(api_key, top_n=200, lite_max_count=None, test_mode=False):
    """
    1단계: F-Score 분석 실행

    Returns:
    --------
    csv_path : str
        생성된 CSV 파일 경로
    """
    print("\n" + "=" * 80)
    print("🔍 1단계: F-Score 재무 분석")
    print("=" * 80)

    system = HybridFScoreSystem(api_key)

    if test_mode:
        print("⚠️  테스트 모드: Lite 100개 / Full 30개")
        system.run(
            top_n=30,
            final_min_score=6,
            lite_max_count=100,
            lite_workers=6,
        )
    else:
        system.run(
            top_n=top_n,
            final_min_score=4,  # 4점 이상은 모두 타이밍 분석 대상
            lite_max_count=lite_max_count,
            lite_workers=6,
        )

    # 생성된 CSV 파일 찾기
    import glob
    full_csv_files = glob.glob('hybrid_full_results_*.csv')
    if full_csv_files:
        latest_csv = sorted(full_csv_files)[-1]
        print(f"\n✅ F-Score Full 결과: {latest_csv}")
        return latest_csv
    else:
        print("\n❌ F-Score 결과 파일을 찾을 수 없습니다")
        return None


def get_fscore_csv(timing_source="auto"):
    """
    F-Score 결과 CSV 파일 경로 결정

    Parameters:
    -----------
    timing_source : str
        'auto': Full 우선, 없으면 Lite
        'full': Full만 사용
        'lite': Lite만 사용

    Returns:
    --------
    csv_path : str or None
    """
    import glob

    if timing_source == "full":
        # Full만 사용
        full_csv_files = glob.glob('hybrid_full_results_*.csv')
        if full_csv_files:
            latest_csv = sorted(full_csv_files)[-1]
            print(f"\n✅ F-Score Full 결과 (9개 지표, ~200개): {latest_csv}")
            return latest_csv
        else:
            print("\n❌ Full 결과 파일을 찾을 수 없습니다")
            print("  힌트: --timing-source lite 또는 --timing-source auto 사용")
            return None

    elif timing_source == "lite":
        # Lite만 사용
        lite_csv_files = glob.glob('hybrid_lite_results_*.csv')
        if lite_csv_files:
            latest_csv = sorted(lite_csv_files)[-1]
            print(f"\n✅ F-Score Lite 결과 (6개 지표, ~1000개): {latest_csv}")
            return latest_csv
        else:
            print("\n❌ Lite 결과 파일을 찾을 수 없습니다")
            return None

    else:  # auto
        # Full 우선, 없으면 Lite
        full_csv_files = glob.glob('hybrid_full_results_*.csv')
        if full_csv_files:
            latest_csv = sorted(full_csv_files)[-1]
            print(f"\n✅ F-Score Full 결과 (9개 지표, ~200개): {latest_csv}")
            return latest_csv

        lite_csv_files = glob.glob('hybrid_lite_results_*.csv')
        if lite_csv_files:
            latest_csv = sorted(lite_csv_files)[-1]
            print(f"\n⚠️  Full 없음, Lite 결과 사용 (6개 지표, ~1000개): {latest_csv}")
            return latest_csv

        print("\n❌ F-Score 결과 파일을 찾을 수 없습니다")
        return None


def run_timing_analysis(
    fscore_csv_path,
    min_fscore=4,
    max_workers=5,
    max_count=None,
    min_timing_score=5.0
):
    """
    2단계: 타이밍 분석 실행

    Returns:
    --------
    results_df : DataFrame
        통합 분석 결과
    """
    print("\n" + "=" * 80)
    print("📊 2단계: 타이밍 분석 (차트)")
    print("=" * 80)

    analyzer = HybridFScoreTiming(
        fscore_csv_path=fscore_csv_path,
        min_fscore=min_fscore
    )

    # F-Score 결과 로드
    fscore_stocks = analyzer.load_fscore_results()

    if fscore_stocks is None or len(fscore_stocks) == 0:
        print("\n❌ F-Score 우량 종목이 없습니다")
        return None

    # 타이밍 분석 실행
    results_df = analyzer.analyze_batch(
        max_workers=max_workers,
        max_count=max_count
    )

    if results_df is None or len(results_df) == 0:
        print("\n❌ 타이밍 분석 결과가 없습니다")
        return None

    # 최소 타이밍 점수로 필터링
    filtered_df = results_df[results_df['Timing_Score'] >= min_timing_score].copy()

    print(f"\n📊 타이밍 분석 완료")
    print(f"  전체: {len(results_df)}개")
    print(f"  타이밍 {min_timing_score}점 이상: {len(filtered_df)}개")

    # 결과 저장
    analyzer.results = results_df
    analyzer.save_results()

    # 상위 종목 출력
    print("\n" + "=" * 80)
    print("🏆 최종 추천 종목 (F-Score + 타이밍)")
    print("=" * 80)

    top_n = min(30, len(filtered_df))
    if top_n > 0:
        analyzer.results = filtered_df  # 필터링된 결과로 교체
        analyzer.print_top_picks(top_n=top_n)
    else:
        print("⚠️  추천 종목이 없습니다. 타이밍 점수 기준을 낮춰보세요.")

    # 통계 출력
    print_statistics(results_df, filtered_df)

    return results_df


def print_statistics(full_df, filtered_df):
    """분석 통계 출력"""
    print("\n" + "=" * 80)
    print("📈 분석 통계")
    print("=" * 80)

    print(f"\n전체 분석 종목: {len(full_df)}개")
    print(f"  평균 F-Score: {full_df['F-Score'].mean():.2f}")
    print(f"  평균 타이밍 점수: {full_df['Timing_Score'].mean():.2f}")
    print(f"  평균 통합 점수: {full_df['Combined_Score'].mean():.2f}")

    print(f"\n타이밍 등급 분포:")
    a_grade = len(full_df[full_df['Timing_Score'] >= 7])
    b_grade = len(full_df[(full_df['Timing_Score'] >= 5) & (full_df['Timing_Score'] < 7)])
    c_grade = len(full_df[(full_df['Timing_Score'] >= 3) & (full_df['Timing_Score'] < 5)])
    d_grade = len(full_df[full_df['Timing_Score'] < 3])

    print(f"  A등급 (7점 이상): {a_grade}개 ({a_grade/len(full_df)*100:.1f}%)")
    print(f"  B등급 (5~7점): {b_grade}개 ({b_grade/len(full_df)*100:.1f}%)")
    print(f"  C등급 (3~5점): {c_grade}개 ({c_grade/len(full_df)*100:.1f}%)")
    print(f"  D등급 (3점 미만): {d_grade}개 ({d_grade/len(full_df)*100:.1f}%)")

    if len(filtered_df) > 0:
        print(f"\n최종 추천 종목: {len(filtered_df)}개")
        print(f"  평균 F-Score: {filtered_df['F-Score'].mean():.2f}")
        print(f"  평균 타이밍 점수: {filtered_df['Timing_Score'].mean():.2f}")
        print(f"  평균 통합 점수: {filtered_df['Combined_Score'].mean():.2f}")


def main():
    args = parse_args()

    print("=" * 80)
    print("🎯 F-Score + 타이밍 분석 완전 통합 시스템")
    print("=" * 80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.test:
        print("\n⚠️  테스트 모드 활성화")

    # 1단계: F-Score 분석
    if not args.skip_fscore:
        if args.api_key is None:
            print("\n❌ OpenDart API 키가 필요합니다.")
            print("  방법 1: --api-key 인자 전달")
            print("  방법 2: OPENDART_API_KEY 환경변수 설정")
            print("  방법 3: --skip-fscore로 기존 결과 사용")
            sys.exit(1)

        fscore_csv = run_fscore_analysis(
            api_key=args.api_key,
            top_n=args.top_n,
            lite_max_count=100 if args.test else None,
            test_mode=args.test
        )

        if fscore_csv is None:
            print("\n❌ F-Score 분석 실패")
            sys.exit(1)
    else:
        # 기존 결과 사용
        print(f"\n📂 기존 F-Score 결과 사용 (--skip-fscore)")
        # 타이밍 분석에서 파일 선택하므로 여기서는 스킵

    if args.fscore_only:
        print("\n✅ F-Score 분석만 완료 (타이밍 분석 생략)")
        return

    # 2단계: 타이밍 분석 - 소스 파일 결정
    timing_csv = get_fscore_csv(timing_source=args.timing_source)
    if timing_csv is None:
        print("\n❌ 타이밍 분석할 F-Score 결과를 찾을 수 없습니다")
        sys.exit(1)

    results = run_timing_analysis(
        fscore_csv_path=timing_csv,
        min_fscore=args.min_fscore,
        max_workers=args.timing_workers,
        max_count=20 if args.test else args.timing_max_count,
        min_timing_score=args.min_timing_score
    )

    if results is None:
        print("\n❌ 타이밍 분석 실패")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("🎉 분석 완료!")
    print("=" * 80)
    print(f"\n결과 파일:")
    print(f"  1. F-Score: {fscore_csv}")
    print(f"  2. 통합: hybrid_timing_results_*.csv")
    print("\n다음 단계:")
    print("  1. CSV 파일을 열어서 상위 종목 확인")
    print("  2. 개별 종목 추가 조사")
    print("  3. 분산 투자 포트폴리오 구성")


if __name__ == "__main__":
    main()
