import os
import json
import shutil
import tempfile

from django.test import TestCase, RequestFactory
from PyPDF2 import PdfReader

from core import views
from core.models import Report, Asset
from core.constants import DEFAULT_REPORT_SECTIONS, SECTION_TITLES_HE

class HebrewPDFGenerationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tmpdir = tempfile.mkdtemp(prefix="reports_test_")
        views.report_service.reports_dir = self.tmpdir

        # Insert a mock asset into the database so the endpoint can fetch real
        # data instead of relying solely on in-memory mocks.
        self.asset = Asset.objects.create(
            scope_type='address',
            city='תל אביב',
            neighborhood='מרכז העיר',
            street='הרצל',
            number=123,
            status='done',
            normalized_address='רחוב הרצל 123, תל אביב',
            meta={
                'address': 'רחוב הרצל 123, תל אביב',
                'city': 'תל אביב',
                'neighborhood': 'מרכז העיר',
                'type': 'דירה',
                'price': 2850000,
                'bedrooms': 3,
                'bathrooms': 2,
                'netSqm': 85,
                'area': 85,
                'pricePerSqm': 33529,
                'remainingRightsSqm': 45,
                'program': 'תמ״א 38',
                'lastPermitQ': 'Q2/24',
                'noiseLevel': 2,
                'competition1km': 'בינוני',
                'zoning': 'מגורים א׳',
                'priceGapPct': -5.2,
                'expectedPriceRange': '2.7M - 3.0M',
                'modelPrice': 3000000,
                'confidencePct': 85,
                'capRatePct': 3.2,
                'rentEstimate': 9500,
                'riskFlags': [],
                'features': ['מעלית', 'חניה', 'מרפסת', 'משופצת'],
                'contactInfo': {
                    'agent': 'יוסי כהן',
                    'phone': '050-1234567',
                    'email': 'yossi@example.com'
                },
                'documents': [
                    {'name': 'נסח טאבו', 'type': 'tabu'},
                    {'name': 'תשריט בית משותף', 'type': 'condo_plan'},
                    {'name': 'היתר בנייה', 'type': 'permit'},
                    {'name': 'זכויות בנייה', 'type': 'rights'},
                    {'name': 'שומת מכרעת', 'type': 'appraisal_decisive'},
                    {'name': 'שומת רמ״י', 'type': 'appraisal_rmi'},
                ],
            },
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_report_includes_expected_sections(self):
        req = self.factory.post(
            "/api/reports",
            data=json.dumps({"assetId": self.asset.id}),
            content_type="application/json",
        )
        resp = views.reports(req)
        self.assertEqual(resp.status_code, 201, resp.content)
        filename = json.loads(resp.content)["report"]["filename"]
        path = os.path.join(self.tmpdir, filename)
        report = Report.objects.get(filename=filename)
        self.assertEqual(report.sections, DEFAULT_REPORT_SECTIONS)

        reader = PdfReader(path)
        self.assertGreaterEqual(len(reader.pages), 1)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        for title in [
            "פרטי הנכס",
            "אנליזה פיננסית",
            "תוכניות וזכויות בנייה",
            "מידע סביבתי וסיכונים",
            "מסמכים וזיהוי איש קשר",
        ]:
            self.assertIn(title, text)
        # Ensure custom sections only include requested content
        req = self.factory.post(
            "/api/reports",
            data=json.dumps({"assetId": self.asset.id, "sections": ["summary", "plans"]}),
            content_type="application/json",
        )
        resp = views.reports(req)
        self.assertEqual(resp.status_code, 201, resp.content)
        filename = json.loads(resp.content)["report"]["filename"]
        path = os.path.join(self.tmpdir, filename)
        report = Report.objects.get(filename=filename)
        self.assertEqual(report.sections, ["summary", "plans"])
        reader = PdfReader(path)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("פרטי הנכס", text)
        self.assertIn("תוכניות וזכויות בנייה", text)
        self.assertNotIn("מידע סביבתי וסיכונים", text)
        self.assertNotIn("מסמכים וזיהוי איש קשר", text)

    def test_empty_sections_rejected(self):
        req = self.factory.post(
            "/api/reports",
            data=json.dumps({"assetId": self.asset.id, "sections": []}),
            content_type="application/json",
        )
        resp = views.reports(req)
        self.assertEqual(resp.status_code, 400)

    def test_unknown_asset_id_generates_placeholder_report(self):
        """Ensure report generation succeeds even for unknown asset IDs."""
        req = self.factory.post(
            "/api/reports",
            data=json.dumps({"assetId": 999}),
            content_type="application/json",
        )
        resp = views.reports(req)
        self.assertEqual(resp.status_code, 201, resp.content)

        data = json.loads(resp.content)
        filename = data["report"]["filename"]
        path = os.path.join(self.tmpdir, filename)
        self.assertTrue(os.path.exists(path), f"Expected PDF file at path {path}")

        report = Report.objects.get(filename=filename)
        self.assertEqual(report.file_url, f"/api/reports/file/{filename}")
        self.assertIsNone(report.asset_id)

    def test_hebrew_font_registration(self):
        """Test that Hebrew font is properly registered and available."""
        # Create a PDF generator instance to test font registration
        from core.pdf_generator import HebrewPDFGenerator
        from pathlib import Path
        
        base_dir = Path(__file__).resolve().parent.parent.parent / 'backend-django'
        pdf_generator = HebrewPDFGenerator(base_dir)
        
        # Check if the Hebrew font is registered
        self.assertNotEqual(
            pdf_generator.report_font, "Helvetica",
            "Hebrew font should be registered and report_font should not be Helvetica"
        )
        
        # Check if the font file exists
        self.assertTrue(
            os.path.exists(pdf_generator.font_path),
            f"Hebrew font file should exist at {pdf_generator.font_path}"
        )
        
        # Print current font status for debugging
        print(f"Current REPORT_FONT: {pdf_generator.report_font}")
        print(f"Font file exists: {os.path.exists(pdf_generator.font_path)}")
        print(f"Font file path: {pdf_generator.font_path}")
