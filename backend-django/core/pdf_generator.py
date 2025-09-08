import os
import time
from pathlib import Path
from typing import Optional, List

from django.template.loader import render_to_string
from weasyprint import HTML
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

from .models import Asset, Report, SourceRecord
from .listing_builder import build_listing
from .constants import SECTION_TITLES_HE


class HebrewPDFGenerator:
    """Handles PDF generation with Hebrew RTL support and proper layout."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.font_path = str(
            (base_dir / "core" / "fonts" / "NotoSansHebrew-Regular.ttf").resolve()
        )
        self.report_font = self._setup_hebrew_font()

    def _setup_hebrew_font(self) -> str:
        """Setup Hebrew font for PDF generation."""
        try:
            if os.path.exists(self.font_path):
                pdfmetrics.registerFont(TTFont("HebrewFont", self.font_path))
                print(f"Successfully registered Hebrew font: {self.font_path}")
                return "HebrewFont"
            else:
                print(f"Hebrew font not found at: {self.font_path}")
                return "Helvetica"
        except Exception as e:
            print(f"Failed to register Hebrew font: {e}")
            return "Helvetica"

    def reverse_hebrew_text(self, text: str) -> str:
        """Reverse Hebrew text for RTL display."""
        if not text:
            return text
        # For Hebrew RTL, reverse word order, not characters
        words = text.split()
        return " ".join(words[::-1])

    def safe_get(self, data: dict, key: str, default=0):
        """Safely get a value from data with a default fallback."""
        value = data.get(key, default)
        return default if value is None else value

    def draw_hebrew_text(
        self, canvas_obj, text: str, x: int, y: int, font_size: int = 12
    ):
        """Draw Hebrew text with proper RTL positioning."""
        canvas_obj.setFont(self.report_font, font_size)
        canvas_obj.drawString(x, y, text)

    def draw_hebrew_label(
        self, canvas_obj, label: str, value, x: int, y: int, font_size: int = 12
    ):
        """Draw a Hebrew label with its value."""
        if self.report_font == "HebrewFont":
            reversed_label = self.reverse_hebrew_text(label)
            canvas_obj.drawString(x, y, f"{reversed_label}: {value}")
        else:
            canvas_obj.drawString(x, y, f"{label}: {value}")

    def create_asset_listing(self, asset: Optional[Asset]) -> dict:
        """Create a listing dictionary from an Asset model using canonical builder."""
        if not asset:
            # Generate a minimal placeholder listing so report creation succeeds
            # for unknown asset IDs. The rest of the fields can remain empty and
            # will be filled with defaults by the PDF generator.
            return {"address": "Unknown asset"}
        srcs = SourceRecord.objects.filter(asset_id=asset.id).order_by("-fetched_at")
        return build_listing(asset, srcs)

    def draw_page_header(self, canvas_obj, title: str, y_position: int = 760):
        """Draw a centered page header."""
        if self.report_font == "HebrewFont":
            canvas_obj.drawCentredString(
                300, y_position, self.reverse_hebrew_text(title)
            )
        else:
            canvas_obj.drawCentredString(300, y_position, title)

    def draw_section_header(
        self, canvas_obj, header: str, x: int, y: int, font_size: int = 14
    ):
        """Draw a section header."""
        if self.report_font == "HebrewFont":
            canvas_obj.drawString(x, y, self.reverse_hebrew_text(header))
        else:
            canvas_obj.drawString(x, y, header)

    def _generate_report_canvas(
        self,
        asset: Optional[Asset],
        report: Report,
        file_path: str,
        sections: List[str],
    ) -> bool:
        """Generate the PDF report using ReportLab primitives for selected sections."""
        start_time = time.time()

        try:
            # Create listing data
            listing = self.create_asset_listing(asset)

            # Debug output
            print(f"Debug - Listing data: {listing}")
            print(f"Debug - Address: {listing.get('address', 'NOT_FOUND')}")
            print(f"Debug - City: {listing.get('city', 'NOT_FOUND')}")

            # Create PDF canvas
            c = canvas.Canvas(file_path, pagesize=A4)

            # Generate pages based on selected sections
            for section in sections:
                if section == "summary":
                    self._generate_page_1_general_analysis(c, listing)
                elif section == "permits":
                    self._generate_stub_page(c, SECTION_TITLES_HE["permits"])
                elif section == "plans":
                    self._generate_page_2_building_plans(c, listing)
                elif section == "environment":
                    self._generate_page_3_environmental_info(c, listing)
                elif section == "comparables":
                    self._generate_stub_page(c, SECTION_TITLES_HE["comparables"])
                elif section == "mortgage":
                    self._generate_stub_page(c, SECTION_TITLES_HE["mortgage"])
                elif section == "appendix":
                    self._generate_page_4_documents_summary(
                        c, listing, SECTION_TITLES_HE["appendix"]
                    )

            # Save PDF
            c.save()

            # Update report status
            generation_time = time.time() - start_time
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            pages = len(PdfReader(file_path).pages)
            report.mark_completed(
                file_size=file_size, pages=pages, generation_time=generation_time
            )
            return True

        except Exception as e:
            report.mark_failed(str(e))
            print(f"PDF generation failed: {e}")
            return False

    def _generate_report_from_template(
        self,
        asset: Optional[Asset],
        report: Report,
        file_path: str,
        sections: List[str],
    ) -> bool:
        """Generate the PDF report using the HTML template and WeasyPrint."""
        start_time = time.time()
        try:
            listing = self.create_asset_listing(asset)
            context = {
                "listing": listing,
                "font_path": Path(self.font_path).as_uri(),
                "overall_score": listing.get("confidencePct", 0),
                "extra_rights_pct": (
                    int(
                        (listing.get("remainingRightsSqm", 0) / listing.get("area", 1))
                        * 100
                    )
                    if listing.get("area") and listing.get("area", 0) > 0
                    else 0
                ),
                "rights_value_k": (
                    int(
                        (
                            listing.get("remainingRightsSqm", 0)
                            * listing.get("pricePerSqm", 0)
                        )
                        / 1000
                    )
                    if listing.get("remainingRightsSqm") and listing.get("pricePerSqm")
                    else 0
                ),
                "sections": sections,
            }

            html_string = render_to_string("report_asset.html", context)
            # Use the static files directory as base_url for WeasyPrint to resolve static assets
            static_dir = self.base_dir / "core" / "static"
            HTML(string=html_string, base_url=str(static_dir)).write_pdf(file_path)

            generation_time = time.time() - start_time
            pages = len(PdfReader(file_path).pages)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            report.mark_completed(
                file_size=file_size, pages=pages, generation_time=generation_time
            )
            return True
        except Exception as e:
            report.mark_failed(str(e))
            print(f"PDF generation failed: {e}")
            return False

    def generate_report(
        self,
        asset: Optional[Asset],
        report: Report,
        file_path: str,
        sections: List[str],
        use_template: bool = True,
    ) -> bool:
        """Generate a report using either the HTML template or the legacy canvas method."""
        if use_template:
            return self._generate_report_from_template(
                asset, report, file_path, sections
            )
        return self._generate_report_canvas(asset, report, file_path, sections)

    def _generate_stub_page(self, c, header: str):
        """Generate a simple page with just a header."""
        self.draw_page_header(c, header)
        c.showPage()

    def _generate_page_1_general_analysis(self, c, listing: dict):
        """Generate Summary page."""
        # Page header
        self.draw_page_header(c, SECTION_TITLES_HE["summary"])

        c.setFont(self.report_font, 12)
        y = 720

        # Asset Details Section
        self.draw_section_header(
            c, "פרטי הנכס", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        c.setFont(self.report_font, 12)

        # Asset details
        self._draw_asset_details(c, listing, y)
        y -= 40

        # Financial Analysis
        self.draw_section_header(
            c, "אנליזה פיננסית", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        self._draw_financial_analysis(c, listing, y)
        y -= 40

        # Investment Recommendation
        self.draw_section_header(
            c, "המלצת השקעה", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        self._draw_investment_recommendation(c, listing, y)

        c.showPage()

    def _draw_asset_details(self, c, listing: dict, y: int):
        """Draw asset details section."""
        x = 450 if self.report_font == "HebrewFont" else 50

        self.draw_hebrew_label(c, "כתובת", listing.get("address", ""), x, y)
        y -= 20
        self.draw_hebrew_label(c, "עיר", listing.get("city", ""), x, y)
        y -= 20
        self.draw_hebrew_label(c, "שכונה", listing.get("neighborhood", ""), x, y)
        y -= 20
        self.draw_hebrew_label(c, "סוג", listing.get("type", ""), x, y)
        y -= 20

        # Price and specifications
        self.draw_hebrew_label(
            c, "מחיר", f"₪{int(self.safe_get(listing, 'price', 0)):,}", x, y
        )
        y -= 20
        self.draw_hebrew_label(c, "חדרים", self.safe_get(listing, "bedrooms", 0), x, y)
        y -= 20
        self.draw_hebrew_label(
            c, "חדרי רחצה", self.safe_get(listing, "bathrooms", 0), x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c, "שטח", f"{self.safe_get(listing, 'netSqm', 0)} מ\"ר", x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c, 'מחיר למ"ר', f"₪{self.safe_get(listing, 'pricePerSqm', 0):,}", x, y
        )

    def _draw_financial_analysis(self, c, listing: dict, y: int):
        """Draw financial analysis section."""
        x = 450 if self.report_font == "HebrewFont" else 50

        self.draw_hebrew_label(
            c, "מחיר מודל", f"₪{self.safe_get(listing, 'modelPrice', 0):,}", x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c, "פער מחיר", f"{self.safe_get(listing, 'priceGapPct', 0)}%", x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c, "הערכת שכירות", f"₪{self.safe_get(listing, 'rentEstimate', 0):,}", x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c, "תשואה שנתית", f"{self.safe_get(listing, 'capRatePct', 0)}%", x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c,
            "תחרות",
            f"(1 ק\"מ): {self.safe_get(listing, 'competition1km', 'N/A')}",
            x,
            y,
        )

    def _draw_investment_recommendation(self, c, listing: dict, y: int):
        """Draw investment recommendation section."""
        x = 450 if self.report_font == "HebrewFont" else 50

        # Calculate overall score
        confidence = self.safe_get(listing, "confidencePct", 0)
        cap_rate = self.safe_get(listing, "capRatePct", 0)
        price_gap = self.safe_get(listing, "priceGapPct", 0)

        overall_score = round(
            (
                confidence
                + (cap_rate * 20)
                + (price_gap < 0 and 100 + price_gap or 100 - price_gap)
            )
            / 3
        )

        self.draw_hebrew_label(c, "ציון כללי", f"{overall_score}/100", x, y)
        y -= 20

        # Recommendation
        if price_gap < -10:
            hebrew_recommendation = "נכס במחיר אטרקטיבי מתחת לשוק"
        elif price_gap > 10:
            hebrew_recommendation = "נכס יקר יחסית לשוק"
        else:
            hebrew_recommendation = "נכס במחיר הוגן בשוק"

        self.draw_hebrew_label(c, "המלצה", hebrew_recommendation, x, y)

    def _generate_page_2_building_plans(self, c, listing: dict):
        """Generate Plans page."""
        self.draw_page_header(c, SECTION_TITLES_HE["plans"])

        c.setFont(self.report_font, 12)
        y = 720

        # Local Plans Section
        self.draw_section_header(
            c,
            "תוכניות מקומיות ומפורטות",
            450 if self.report_font == "HebrewFont" else 50,
            y,
        )
        y -= 25
        self._draw_building_plans_details(c, listing, y)
        y -= 40

        # Rights Summary
        self.draw_section_header(
            c,
            "זכויות בנייה מפורטות",
            450 if self.report_font == "HebrewFont" else 50,
            y,
        )
        y -= 25
        self._draw_rights_summary(c, listing, y)

        c.showPage()

    def _draw_building_plans_details(self, c, listing: dict, y: int):
        """Draw building plans details."""
        x = 450 if self.report_font == "HebrewFont" else 50

        self.draw_hebrew_label(c, "תוכנית נוכחית", listing.get("program", ""), x, y)
        y -= 20
        self.draw_hebrew_label(c, "ייעוד קרקע", listing.get("zoning", ""), x, y)
        y -= 20
        self.draw_hebrew_label(
            c, "זכויות נוספות", f"+{listing.get('remainingRightsSqm', 0)} מ\"ר", x, y
        )
        y -= 20
        self.draw_hebrew_label(
            c, "זכויות בנייה עיקריות", f"{listing.get('netSqm', 0)} מ\"ר", x, y
        )

    def _draw_rights_summary(self, c, listing: dict, y: int):
        """Draw building rights summary."""
        x = 450 if self.report_font == "HebrewFont" else 50

        self.draw_hebrew_label(
            c, "זכויות נוספות", f"{listing.get('remainingRightsSqm', 0)} מ\"ר", x, y
        )
        y -= 20

        # Calculate additional rights percentage
        additional_rights_pct = 0
        if listing.get("netSqm") and listing.get("netSqm", 0) > 0:
            additional_rights_pct = round(
                (listing.get("remainingRightsSqm", 0) / listing.get("netSqm", 1)) * 100
            )
        self.draw_hebrew_label(
            c, "אחוז זכויות נוספות", f"{additional_rights_pct}%", x, y
        )
        y -= 20

        # Calculate rights value
        rights_value = 0
        if listing.get("pricePerSqm") and listing.get("remainingRightsSqm"):
            rights_value = round(
                (
                    listing.get("pricePerSqm", 0)
                    * listing.get("remainingRightsSqm", 0)
                    * 0.7
                )
                / 1000
            )
        self.draw_hebrew_label(c, "ערך זכויות משוער", f"₪{rights_value}K", x, y)

    def _generate_page_3_environmental_info(self, c, listing: dict):
        """Generate Environment page."""
        self.draw_page_header(c, SECTION_TITLES_HE["environment"])

        c.setFont(self.report_font, 12)
        y = 720

        # Environmental Data Section
        self.draw_section_header(
            c, "מידע סביבתי", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        self._draw_environmental_data(c, listing, y)
        y -= 40

        # Risk Factors Section
        self.draw_section_header(
            c, "סיכונים", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        self._draw_risk_factors(c, listing, y)

        c.showPage()

    def _draw_environmental_data(self, c, listing: dict, y: int):
        """Draw environmental data."""
        x = 450 if self.report_font == "HebrewFont" else 50

        self.draw_hebrew_label(c, "רמת רעש", f"{listing.get('noiseLevel', 0)}/5", x, y)
        y -= 20
        self.draw_hebrew_label(c, "שטחים ציבוריים", "≤300מ: כן", x, y)
        y -= 20
        self.draw_hebrew_label(c, "מרחק אנטנה", "150מ", x, y)

    def _draw_risk_factors(self, c, listing: dict, y: int):
        """Draw risk factors."""
        x = 450 if self.report_font == "HebrewFont" else 50

        if listing.get("riskFlags") and len(listing.get("riskFlags", [])) > 0:
            for flag in listing.get("riskFlags", []):
                c.drawString(x, y, f"• {flag}")
                y -= 20
        else:
            if self.report_font == "HebrewFont":
                c.drawString(x, y, self.reverse_hebrew_text("אין סיכונים מיוחדים"))
            else:
                c.drawString(x, y, "No special risks")

    def _generate_page_4_documents_summary(
        self, c, listing: dict, header: str = SECTION_TITLES_HE["appendix"]
    ):
        """Generate Appendix page."""
        self.draw_page_header(c, header)

        c.setFont(self.report_font, 12)
        y = 720

        # Available Documents Section
        self.draw_section_header(
            c, "מסמכים זמינים", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        self._draw_documents_list(c, listing, y)
        y -= 50

        # Contact Information Section
        self.draw_section_header(
            c, "פרטי קשר", 450 if self.report_font == "HebrewFont" else 50, y
        )
        y -= 25
        self._draw_contact_info(c, listing, y)

    def _draw_documents_list(self, c, listing: dict, y: int):
        """Draw documents list."""
        x = 450 if self.report_font == "HebrewFont" else 50

        if listing.get("documents") and len(listing.get("documents", [])) > 0:
            for doc in listing.get("documents", []):
                c.drawString(x, y, f"• {doc['name']}")
                y -= 20
        else:
            if self.report_font == "HebrewFont":
                c.drawString(x, y, self.reverse_hebrew_text("אין מסמכים זמינים"))
            else:
                c.drawString(x, y, "No documents available")

    def _draw_contact_info(self, c, listing: dict, y: int):
        """Draw contact information."""
        x = 450 if self.report_font == "HebrewFont" else 50

        if listing.get("contactInfo"):
            self.draw_hebrew_label(
                c, "סוכן", listing.get("contactInfo", {}).get("agent", ""), x, y
            )
            y -= 20
            self.draw_hebrew_label(
                c, "טלפון", listing.get("contactInfo", {}).get("phone", ""), x, y
            )
            y -= 20
            self.draw_hebrew_label(
                c, "אימייל", listing.get("contactInfo", {}).get("email", ""), x, y
            )
