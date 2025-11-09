"""
Hybrid F-Score 실행 스크립트

명령행 인자를 통해 테스트/전체 모드를 전환하고,
환경변수 또는 인자로 전달된 OpenDart API 키로 시스템을 실행한다.
"""

import argparse
import os
import sys

from hybrid_fscore import HybridFScoreSystem


def parse_args():
    parser = argparse.ArgumentParser(description="Run Hybrid F-Score pipeline")
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENDART_API_KEY"),
        help="OpenDart API 키 (미지정 시 환경변수 OPENDART_API_KEY 사용)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=200,
        help="Lite 단계에서 Full 분석으로 넘길 종목 수",
    )
    parser.add_argument(
        "--final-min-score",
        type=int,
        default=7,
        help="최종 추천 최소 Full F-Score",
    )
    parser.add_argument(
        "--lite-max-count",
        type=int,
        default=None,
        help="Lite 단계 최대 처리 종목 수 (테스트용)",
    )
    parser.add_argument(
        "--lite-workers",
        type=int,
        default=6,
        help="Lite 단계 병렬 워커 수 (FnGuide 차단 방지용)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="빠른 검증을 위한 테스트 모드 (Lite 100개, Full 30개)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.api_key is None:
        print("⚠️  OpenDart API 키가 필요합니다. --api-key 또는 OPENDART_API_KEY를 설정하세요.")
        sys.exit(1)

    system = HybridFScoreSystem(args.api_key)

    if args.test:
        print("⚠️  테스트 모드 실행 (Lite 100개 / Full 30개 / 최종 6점 이상)")
        system.run(
            top_n=30,
            final_min_score=6,
            lite_max_count=100,
            lite_workers=args.lite_workers,
        )
    else:
        system.run(
            top_n=args.top_n,
            final_min_score=args.final_min_score,
            lite_max_count=args.lite_max_count,
            lite_workers=args.lite_workers,
        )


if __name__ == "__main__":
    main()
