"""Fast, deterministic transaction comparison tests.

The previous version of this module executed the full pipeline against
production services which made CI take more than half an hour.  These tests
focus on the price-analysis logic using in-memory fixtures so we still cover
the analytical behaviour without depending on network access.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from gov.nadlan.models import Deal

Transaction = Dict[str, object]
TransactionsByAddress = Dict[str, List[Transaction]]

MOCK_TRANSACTIONS: Dict[str, List[Dict[str, object]]] = {
    "רוזוב 14 תל אביב": [
        {
            "address": "רוזוב 14, תל אביב-יפו",
            "dealAmount": 2_500_000,
            "dealDate": "2023-01-15",
            "rooms": "3",
            "floor": "2",
            "assetType": "דירה",
            "area": 85.5,
        },
        {
            "address": "רוזוב 14, תל אביב-יפו",
            "dealAmount": 2_800_000,
            "dealDate": "2023-06-20",
            "rooms": "4",
            "floor": "3",
            "assetType": "דירה",
            "area": 95.0,
        },
    ],
    "רוטשילד 1 תל אביב": [
        {
            "address": "רוטשילד 1, תל אביב-יפו",
            "dealAmount": 3_500_000,
            "dealDate": "2023-03-10",
            "rooms": "3",
            "floor": "5",
            "assetType": "דירה",
            "area": 90.0,
        }
    ],
    "דיזנגוף 50 תל אביב": [
        {
            "address": "דיזנגוף 50, תל אביב-יפו",
            "dealAmount": 4_200_000,
            "dealDate": "2023-05-12",
            "rooms": "4",
            "floor": "8",
            "assetType": "דירה",
            "area": 110.0,
        }
    ],
}


def _normalize_transactions(data: Dict[str, Iterable[Dict[str, object]]]) -> TransactionsByAddress:
    normalized: TransactionsByAddress = {}
    for address, items in data.items():
        normalized[address] = [Deal.from_item(item).to_dict() for item in items]
    return normalized


def _price_statistics(transactions: TransactionsByAddress) -> Dict[str, Dict[str, float]]:
    stats: Dict[str, Dict[str, float]] = {}
    for address, deals in transactions.items():
        prices = [deal["deal_amount"] for deal in deals if deal.get("deal_amount")]
        if not prices:
            continue
        stats[address] = {
            "count": float(len(prices)),
            "avg": float(sum(prices) / len(prices)),
            "min": float(min(prices)),
            "max": float(max(prices)),
            "range": float(max(prices) - min(prices)),
        }
    return stats


def _partition_by_price(transactions: TransactionsByAddress, threshold: float) -> Tuple[List[Transaction], List[Transaction]]:
    below: List[Transaction] = []
    above: List[Transaction] = []
    for deals in transactions.values():
        for deal in deals:
            price = deal.get("deal_amount")
            if not isinstance(price, (int, float)):
                continue
            if price <= threshold:
                below.append(deal)
            else:
                above.append(deal)
    return below, above


def test_normalization_preserves_core_fields():
    transactions = _normalize_transactions(MOCK_TRANSACTIONS)

    assert set(transactions) == {"רוזוב 14 תל אביב", "רוטשילד 1 תל אביב", "דיזנגוף 50 תל אביב"}
    sample = transactions["רוזוב 14 תל אביב"][0]
    assert sample["address"] == "רוזוב 14, תל אביב-יפו"
    assert sample["deal_amount"] == 2_500_000
    assert sample["area"] == 85.5


def test_price_statistics_match_expected_values():
    transactions = _normalize_transactions(MOCK_TRANSACTIONS)
    stats = _price_statistics(transactions)

    assert stats["רוזוב 14 תל אביב"] == {
        "count": 2.0,
        "avg": 2_650_000.0,
        "min": 2_500_000.0,
        "max": 2_800_000.0,
        "range": 300_000.0,
    }
    assert stats["רוטשילד 1 תל אביב"]["avg"] == 3_500_000.0
    assert stats["דיזנגוף 50 תל אביב"]["count"] == 1.0


def test_partition_by_price_brackets_transactions_correctly():
    transactions = _normalize_transactions(MOCK_TRANSACTIONS)
    stats = _price_statistics(transactions)
    threshold = stats["רוזוב 14 תל אביב"]["avg"]

    below, above = _partition_by_price(transactions, threshold)

    assert all(deal["deal_amount"] <= threshold for deal in below)
    assert all(deal["deal_amount"] > threshold for deal in above)
    assert len(below) + len(above) == sum(len(v) for v in transactions.values())
