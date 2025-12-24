"""
Deal expenses calculation service.
Replicates the frontend calculation logic for purchase tax and service costs.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class DealExpensesService:
    """Service for calculating deal expenses including purchase tax and service costs."""

    # Land tax rate (6%)
    LAND_TAX_RATE = 0.06

    # 2025 single home brackets (freeze)
    SINGLE_HOME_BRACKETS = [
        {"limit": 1_978_745, "rate": 0},
        {"limit": 2_347_040, "rate": 0.035},
        {"limit": 6_055_070, "rate": 0.05},
        {"limit": 20_183_565, "rate": 0.08},
        {"limit": float("inf"), "rate": 0.10},
    ]

    # Additional home brackets
    ADDITIONAL_HOME_BRACKETS = [
        {"limit": 6_055_070, "rate": 0.08},
        {"limit": float("inf"), "rate": 0.10},
    ]

    # Oleh (new immigrant) brackets
    OLEH_BRACKETS = [
        {"limit": 1_930_000, "rate": 0.005},
        {"limit": float("inf"), "rate": 0.05},
    ]

    # Disabled/Bereaved cap
    DISABLED_CAP = 2_500_000
    DISABLED_RATE = 0.005

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _apply_brackets(self, value: float, brackets: List[Dict[str, float]]) -> float:
        """Apply tax brackets to a value."""
        tax = 0.0
        prev = 0.0
        for bracket in brackets:
            limit = bracket["limit"]
            rate = bracket["rate"]
            taxable = min(value, limit) - prev
            if taxable > 0:
                tax += taxable * rate
            if value <= limit:
                break
            prev = limit
        return tax

    def _calc_regular(self, value: float, is_first: bool) -> float:
        """Calculate regular purchase tax."""
        brackets = (
            self.SINGLE_HOME_BRACKETS if is_first else self.ADDITIONAL_HOME_BRACKETS
        )
        return self._apply_brackets(value, brackets)

    def _calc_oleh(self, value: float) -> float:
        """Calculate purchase tax for oleh (new immigrant)."""
        return self._apply_brackets(value, self.OLEH_BRACKETS)

    def _calc_disabled(self, value: float, is_first: bool) -> float:
        """Calculate purchase tax for disabled/bereaved."""
        reduced = min(value, self.DISABLED_CAP) * self.DISABLED_RATE
        remaining = (
            self._calc_regular(value - self.DISABLED_CAP, is_first)
            if value > self.DISABLED_CAP
            else 0.0
        )
        return reduced + remaining

    def calculate_purchase_tax(
        self,
        price: float,
        buyers: List[Dict[str, Any]],
        property_type: str = "residential",
    ) -> Dict[str, Any]:
        """
        Calculate purchase tax for all buyers.

        Args:
            price: Property price
            buyers: List of buyer dictionaries with:
                - sharePct: Percentage share (0-100)
                - isFirstHome: Boolean (optional)
                - isReplacementHome: Boolean (optional)
                - oleh: Boolean (optional)
                - disabled: Boolean (optional)
                - bereavedFamily: Boolean (optional)
                - name: String (optional)
            property_type: "residential" or "land"

        Returns:
            Dict with totalTax and breakdown list
        """
        if property_type == "land":
            breakdown = []
            for buyer in buyers:
                share_pct = buyer.get("sharePct", 0)
                portion_price = (price * share_pct) / 100
                tax = portion_price * self.LAND_TAX_RATE
                breakdown.append(
                    {
                        "buyer": buyer,
                        "portionPrice": portion_price,
                        "tax": tax,
                        "track": "land",
                    }
                )
            total_tax = sum(item["tax"] for item in breakdown)
            return {"totalTax": total_tax, "breakdown": breakdown}

        # Residential property
        breakdown = []
        for buyer in buyers:
            share_pct = buyer.get("sharePct", 0)
            portion_price = (price * share_pct) / 100
            is_first = buyer.get("isFirstHome", False) or buyer.get(
                "isReplacementHome", False
            )

            regular = self._calc_regular(portion_price, is_first)
            oleh = (
                self._calc_oleh(portion_price)
                if buyer.get("oleh", False)
                else float("inf")
            )
            disabled = (
                self._calc_disabled(portion_price, is_first)
                if buyer.get("disabled", False)
                else float("inf")
            )
            bereaved = (
                self._calc_disabled(portion_price, is_first)
                if buyer.get("bereavedFamily", False)
                else float("inf")
            )

            tax = min(regular, oleh, disabled, bereaved)

            # Determine track
            if tax == oleh:
                track = "oleh"
            elif tax == disabled:
                track = "disabled"
            elif tax == bereaved:
                track = "bereaved"
            else:
                track = "regular"

            breakdown.append(
                {
                    "buyer": buyer,
                    "portionPrice": portion_price,
                    "tax": tax,
                    "track": track,
                }
            )

        total_tax = sum(item["tax"] for item in breakdown)
        return {"totalTax": total_tax, "breakdown": breakdown}

    def calculate_service_costs(
        self, price: float, services: List[Dict[str, Any]], vat_rate: float
    ) -> Dict[str, Any]:
        """
        Calculate service costs with VAT handling.

        Args:
            price: Property price
            services: List of service dictionaries with:
                - label: Service label
                - percent: Percentage of price (optional)
                - amount: Fixed amount (optional)
                - includesVat: Boolean indicating if VAT is included
            vat_rate: VAT rate (e.g., 0.18 for 18%)

        Returns:
            Dict with total and breakdown list
        """
        breakdown = []
        for service in services:
            cost = 0.0

            # Calculate base cost
            amount = service.get("amount")
            percent = service.get("percent")

            if amount is not None and amount > 0:
                cost = float(amount)
            elif percent is not None and percent > 0:
                cost = (price * percent) / 100

            if cost <= 0:
                continue

            # Apply VAT if not included
            includes_vat = service.get("includesVat", False)
            if not includes_vat:
                cost = cost * (1 + vat_rate)

            breakdown.append({"label": service.get("label", ""), "cost": cost})

        total = sum(item["cost"] for item in breakdown)
        return {"total": total, "breakdown": breakdown}

    def calculate_deal_expenses(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete deal expenses including purchase tax, service costs, and construction costs.

        Args:
            payload: Dictionary containing:
                - price: Property price (required)
                - area: Property area in sqm (optional, for price per sqm calculation)
                - propertyType: "residential" or "land" (default: "residential")
                - buyers: List of buyer dictionaries (required)
                - services: List of service dictionaries (optional)
                - vatRate: VAT rate (default: 0.18)
                - constructionArea: Construction area in sqm (optional, for land)
                - constructionCostPerSqm: Cost per sqm (optional, for land)
                - constructionIncludesVat: Boolean (optional, default: True)

        Returns:
            Dict with complete expense breakdown
        """
        try:
            price = float(payload.get("price", 0))
            area = payload.get("area", 0)
            property_type = payload.get("propertyType", "residential")
            buyers = payload.get("buyers", [])
            services = payload.get("services", [])
            vat_rate = float(payload.get("vatRate", 0.18))

            # Calculate purchase tax
            purchase_tax_result = self.calculate_purchase_tax(
                price, buyers, property_type
            )

            # Calculate service costs
            service_costs_result = self.calculate_service_costs(
                price, services, vat_rate
            )

            # Calculate construction cost (for land)
            construction_cost = 0.0
            if property_type == "land":
                construction_area = payload.get("constructionArea", 0)
                construction_cost_per_sqm = payload.get("constructionCostPerSqm", 0)
                construction_includes_vat = payload.get("constructionIncludesVat", True)

                if construction_area > 0 and construction_cost_per_sqm > 0:
                    base_cost = construction_area * construction_cost_per_sqm
                    if not construction_includes_vat:
                        construction_cost = base_cost * (1 + vat_rate)
                    else:
                        construction_cost = base_cost

            # Calculate totals
            total_tax = purchase_tax_result["totalTax"]
            service_total = service_costs_result["total"]
            total = price + total_tax + service_total + construction_cost

            # Calculate price per sqm
            price_per_sq_before = (price / area) if area > 0 else 0
            price_per_sq_after = (total / area) if area > 0 else 0

            return {
                "totalTax": total_tax,
                "breakdown": purchase_tax_result["breakdown"],
                "serviceTotal": service_total,
                "serviceBreakdown": service_costs_result["breakdown"],
                "constructionCost": construction_cost,
                "total": total,
                "pricePerSqBefore": price_per_sq_before,
                "pricePerSqAfter": price_per_sq_after,
            }

        except Exception as e:
            self.logger.error(f"Error calculating deal expenses: {e}")
            raise
