"""quick_text_probe_parallel JSONL 파편을 읽어 학습용 샘플 카탈로그를 생성한다."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Union

import pandas as pd

# quick_text_probe_parallel 디렉터리의 JSONL 파일을 기본 소스로 사용한다.
# env(RECOMMENDER_DATA_DIR) > back/recommender/data/... > back/crawd/workflowP/craw/data/...
_ENV_DATA_DIR = os.getenv("RECOMMENDER_DATA_DIR")
_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data" / "quick_text_probe_parallel"
_CRAWD_DATA_DIR = (
    Path(__file__).resolve().parents[2] / "crawd" / "workflowP" / "craw" / "data" / "quick_text_probe_parallel"
)
DATA_DIR = (
    Path(_ENV_DATA_DIR)
    if _ENV_DATA_DIR
    else _DEFAULT_DATA_DIR
    if _DEFAULT_DATA_DIR.exists()
    else _CRAWD_DATA_DIR
)


def _parse_price(value) -> int:
    """숫자·쉼표 외 문자를 제거해 정수 가격으로 변환한다."""
    digits = re.sub(r"[^\d]", "", str(value) if value is not None else "")
    return int(digits) if digits else 0


def _parse_rating(prod: Dict) -> float:
    """가중 평점 → 일반 평점 순서로 가져오되, 없으면 0.0으로 채운다."""
    for key in ("rating_weighted", "rating"):
        val = prod.get(key)
        if val is None or val == "":
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return 0.0


def _parse_popularity(prod: Dict) -> int:
    """리뷰 수를 우선 인기 지표로 사용하고, 없으면 0을 반환한다."""
    count = prod.get("review_count")
    try:
        return int(count) if count is not None else 0
    except (TypeError, ValueError):
        return 0


def _split_tags(raw: str) -> List[str]:
    """제품 태그 문자열을 개략적인 토큰 리스트로 분리한다."""
    if not raw:
        return []
    return [part.strip() for part in re.split(r"[\\n/]+", str(raw)) if part.strip()]


def _iter_products(target_dir: Path) -> Iterable[Dict]:
    """모든 JSONL 파트를 스트리밍하며 상품 행 딕셔너리를 생성한다."""
    parts = sorted(target_dir.glob("part_*.jsonl"))
    if not parts:
        raise FileNotFoundError(f"JSONL 파트 파일을 찾을 수 없습니다: {target_dir}")
    pid = 1
    for part_path in parts:
        with part_path.open(encoding="utf-8") as fp:
            for line in fp:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if not payload.get("ok", True):
                    continue
                categories = [p for p in payload.get("path", []) if p]
                link = payload.get("link", "")
                for prod in payload.get("products", []):
                    yield {
                        "product_id": pid,
                        "title": prod.get("prod_name", "").strip(),
                        "price": _parse_price(prod.get("price")),
                        "rating": _parse_rating(prod),
                        "popularity": _parse_popularity(prod),
                        "tags": _split_tags(prod.get("tags", "")),
                        "category_path": categories,
                        "image": prod.get("image", ""),
                        "link": link,
                    }
                    pid += 1


def sample_data(path: Union[str, Path, None] = None) -> pd.DataFrame:
    """
    quick_text_probe_parallel 데이터에서 상품 목록을 구성해 반환한다.

    - 기본 경로는 ./data/quick_text_probe_parallel 이며, part_*.jsonl을 전부 읽는다.
    - JSON 파일 경로가 들어오면 기존 방식처럼 단일 파일을 읽는 폴백을 유지한다.
    """
    target = Path(path) if path else DATA_DIR
    if not target.exists():
        for fallback in (_DEFAULT_DATA_DIR, _CRAWD_DATA_DIR):
            if fallback.exists():
                target = fallback
                break
    if target.is_file():
        return pd.read_json(target)
    if not target.exists():
        raise FileNotFoundError(f"샘플 카탈로그 소스를 찾을 수 없습니다: {target}")
    rows = list(_iter_products(target))
    if not rows:
        raise ValueError("읽어들인 상품이 없습니다. 데이터 파일을 확인하세요.")
    df = pd.DataFrame(rows)
    # 텍스트 전처리 단계에서 기대하는 컬럼 형태를 맞춘다.
    df["price"] = df["price"].fillna(0).astype(int)
    df["rating"] = df["rating"].fillna(0.0).astype(float)
    df["popularity"] = df["popularity"].fillna(0).astype(int)
    return df
