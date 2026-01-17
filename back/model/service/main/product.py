from typing import List, Dict

from typing import Dict, List

from model.recommender import run_recommender


def _format_price(raw_cost) -> str:
    if raw_cost is None:
        return ""
    if isinstance(raw_cost, str):
        return raw_cost
    try:
        return f"{int(raw_cost):,}원"
    except (ValueError, TypeError):
        return str(raw_cost)


def get_gifts_by_keyword(keyword: str) -> List[Dict[str, str]]:
    keyword = (keyword or "").strip()
    if not keyword:
        return []

    try:
        # 동일한 추천 품질을 위해 Top-K를 50으로 고정
        fusion = run_recommender(keyword, top_k=50, hard_budget=False)
    except Exception as exc:  # pragma: no cover - 진단용 출력
        print(f"[⚠️] 로컬 선물 추천 로딩 실패: {exc}")
        return []

    items = fusion.get("results") if isinstance(fusion, dict) else None
    if not isinstance(items, list):
        return []

    gifts: List[Dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        gifts.append(
            {
                "name": str(item.get("name") or ""),
                "price": _format_price(item.get("cost")),
                "image_url": item.get("image_url") or "",
                "category_path": item.get("category_path") or "",
                "tags": item.get("tags") or "",
                "link": item.get("link") or "",
            }
        )
        if len(gifts) >= 30:
            break

    return gifts
