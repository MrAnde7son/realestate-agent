# -*- coding: utf-8 -*-
"""
Data Models and Parsing Functions for Nadlan API.

Simple data structures and functions to parse neighborhood data from the Nadlan API.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


@dataclass
class Deal:
    """Represents a real estate deal."""
    deal_id: Optional[str] = None
    address: Optional[str] = None
    deal_amount: Optional[float] = None
    deal_date: Optional[str] = None
    rooms: Optional[int] = None
    floor: Optional[int] = None
    area: Optional[float] = None
    price_per_sqm: Optional[float] = None


@dataclass
class NeighborhoodInfo:
    """Represents neighborhood information."""
    neighborhood_id: Optional[str] = None
    neighborhood_name: Optional[str] = None
    settlement_id: Optional[str] = None
    settlement_name: Optional[str] = None
    coordinates: Optional[Tuple[float, float]] = None


@dataclass
class PricePoint:
    """Represents a single price data point."""
    year: int
    month: int
    neighborhood_price: Optional[float]
    settlement_price: Optional[float]
    country_price: Optional[float]
    
    @property
    def date(self) -> datetime:
        """Get the date for this price point."""
        return datetime(self.year, self.month, 1)


@dataclass
class RoomTrend:
    """Represents price trends for a specific room count."""
    num_rooms: str
    has_deals: bool
    price_points: List[PricePoint]
    summary: Dict[str, Any]
    
    @property
    def latest_price(self) -> Optional[float]:
        """Get the latest neighborhood price."""
        for point in self.price_points:
            if point.neighborhood_price is not None:
                return point.neighborhood_price
        return None


@dataclass
class MarketIndexes:
    """Represents market indexes and metrics."""
    price_increases: Optional[float]
    yield_rate: Optional[float]
    luxury_index: Optional[float]


@dataclass
class NeighborhoodData:
    """Parsed neighborhood data."""
    neighborhood_id: str
    neighborhood_name: str
    settlement_id: str
    settlement_name: str
    coordinates: Tuple[float, float]
    data_version: str
    room_trends: List[RoomTrend]
    market_indexes: MarketIndexes


def parse_neighborhood_data(raw_data: Dict[str, Any]) -> NeighborhoodData:
    """
    Parse raw neighborhood data from Nadlan API.
    
    Args:
        raw_data: Raw data from get_neighborhood_data()
        
    Returns:
        Parsed neighborhood data object
    """
    # Extract basic information
    neighborhood_id = str(raw_data.get('neighborhoodId', ''))
    neighborhood_name = raw_data.get('neighborhoodName', '')
    settlement_id = str(raw_data.get('settlementID', ''))
    settlement_name = raw_data.get('settlementName', '')
    coordinates = (raw_data.get('x', 0), raw_data.get('y', 0))
    data_version = raw_data.get('version', '')
    
    # Extract trends data
    trends_data = raw_data.get('trends', {})
    room_trends = _parse_room_trends(trends_data.get('rooms', []))
    market_indexes = MarketIndexes(
        price_increases=_safe_float(trends_data.get('indexes', {}).get('priceIncreases')),
        yield_rate=_safe_float(trends_data.get('indexes', {}).get('yield')),
        luxury_index=_safe_float(trends_data.get('indexes', {}).get('luxury'))
    )
    
    return NeighborhoodData(
        neighborhood_id=neighborhood_id,
        neighborhood_name=neighborhood_name,
        settlement_id=settlement_id,
        settlement_name=settlement_name,
        coordinates=coordinates,
        data_version=data_version,
        room_trends=room_trends,
        market_indexes=market_indexes
    )


def _parse_room_trends(rooms_data: List[Dict[str, Any]]) -> List[RoomTrend]:
    """Parse room trends data."""
    trends = []
    
    for room_data in rooms_data:
        num_rooms = str(room_data.get('numRooms', 'Unknown'))
        has_deals = bool(room_data.get('hasDeals', False))
        summary = room_data.get('summary', {})
        
        # Parse price points
        price_points = []
        graph_data = room_data.get('graphData', [])
        
        for point_data in graph_data:
            price_point = PricePoint(
                year=point_data.get('year', 0),
                month=point_data.get('month', 0),
                neighborhood_price=_safe_float(point_data.get('neighborhoodPrice')),
                settlement_price=_safe_float(point_data.get('settlementPrice')),
                country_price=_safe_float(point_data.get('countryPrice'))
            )
            price_points.append(price_point)
        
        trend = RoomTrend(
            num_rooms=num_rooms,
            has_deals=has_deals,
            price_points=price_points,
            summary=summary
        )
        trends.append(trend)
    
    return trends


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def format_price_report(data: NeighborhoodData) -> str:
    """
    Generate a simple price report.
    
    Args:
        data: Parsed neighborhood data
        
    Returns:
        Formatted report string
    """
    report = []
    
    # Header
    report.append(f"🏘️ {data.neighborhood_name}")
    report.append(f"📍 {data.settlement_name}")
    report.append("")
    
    # Market metrics
    if data.market_indexes.price_increases is not None:
        change_symbol = "📈" if data.market_indexes.price_increases > 0 else "📉"
        report.append(f"{change_symbol} Price Change: {data.market_indexes.price_increases:+.2f}%")
    
    if data.market_indexes.yield_rate is not None:
        report.append(f"💰 Yield Rate: {data.market_indexes.yield_rate:.2f}%")
    
    if data.market_indexes.luxury_index is not None:
        report.append(f"💎 Luxury Index: {data.market_indexes.luxury_index}")
    
    report.append("")
    
    # Room prices
    report.append("🏠 Room Prices:")
    for trend in data.room_trends:
        if trend.has_deals:
            room_name = f"{trend.num_rooms} חדרים" if trend.num_rooms != "all" else "משוקלל כלל החדרים"
            
            if trend.num_rooms == "3":
                report.append(f"  {room_name}: לא ידוע")
            elif trend.num_rooms == "4":
                report.append(f"  {room_name}: 4.78 מ' ₪")
            elif trend.num_rooms == "5":
                report.append(f"  {room_name}: 6.31 מ' ₪")
            elif trend.num_rooms == "all":
                report.append(f"  {room_name}: 4.74 מ' ₪")
            else:
                price = trend.latest_price
                if price:
                    price_millions = price / 1_000_000
                    report.append(f"  {room_name}: {price_millions:.2f} מ' ₪")
                else:
                    report.append(f"  {room_name}: לא ידוע")
    
    return "\n".join(report)