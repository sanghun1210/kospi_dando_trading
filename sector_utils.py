"""
섹터(업종) 관련 유틸리티

pykrx 데이터를 활용해 종목-섹터 매핑을 제공하고,
데이터가 없을 때는 안전하게 빈 매핑을 반환한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Iterable, Optional

import pandas as pd

try:
    from pykrx import stock
except Exception:  # pragma: no cover - pykrx가 없는 환경에서도 임포트 에러 방지
    stock = None


DEFAULT_SECTOR = "UNKNOWN"


def _normalize_code(code: str) -> str:
    if code is None:
        return ""
    return str(code).zfill(6)


def _fetch_sector_frame(target_date: datetime, market: str) -> pd.DataFrame:
    if stock is None:
        return pd.DataFrame()

    try:
        df = stock.get_market_sector_classifications(target_date, market)
    except Exception:
        return pd.DataFrame()

    required_cols = {"ISU_SRT_CD", "IDX_IND_NM"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.DataFrame()

    df = df[list(required_cols)].rename(
        columns={"ISU_SRT_CD": "code", "IDX_IND_NM": "sector"}
    )
    df["code"] = df["code"].apply(_normalize_code)
    df["sector"] = df["sector"].astype(str).str.strip()
    return df.drop_duplicates(subset="code")


@lru_cache(maxsize=1)
def get_sector_lookup(max_days: int = 5) -> Dict[str, str]:
    """
    최근 거래일 기준으로 pykrx 업종 분류 데이터를 조회해 종목 코드를 섹터명에 매핑한다.

    네트워크/시장 휴장 등으로 특정 일자 조회가 실패할 수 있으므로
    최근 max_days일까지 순차적으로 조회하여 데이터를 확보한다.
    """
    frames = []
    today = datetime.now()

    for offset in range(max_days):
        target_date = today - timedelta(days=offset)
        for market in ("KOSPI", "KOSDAQ"):
            frame = _fetch_sector_frame(target_date, market)
            if not frame.empty:
                frames.append(frame)

        if frames:
            break

    if not frames:
        return {}

    sector_df = pd.concat(frames, ignore_index=True)
    sector_df = sector_df.drop_duplicates(subset="code", keep="first")
    return dict(zip(sector_df["code"], sector_df["sector"]))


def map_sectors(codes: Iterable[str], lookup: Optional[Dict[str, str]] = None) -> pd.Series:
    """
    종목 코드 시퀀스를 받아 섹터명을 Series로 반환한다.
    """
    if lookup is None:
        lookup = get_sector_lookup()

    return pd.Series(
        [_normalize_code(code) for code in codes],
        name="code",
    ).map(lookup).fillna(DEFAULT_SECTOR)
