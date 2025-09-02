import os
import json
import shutil
import tempfile

from django.test import TestCase, RequestFactory
from PyPDF2 import PdfReader

from core import views
from core.models import Report, Asset

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
            status='ready',
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

    def test_pdf_contains_hebrew_titles(self):
        # Ensure we actually have a Hebrew-capable font
        self.assertNotEqual(
            views.report_service.pdf_generator.report_font, "Helvetica",
            "Hebrew font not found. Add core/fonts/NotoSansHebrew-Regular.ttf "
            "or set REPORT_HEBREW_FONT_PATH to a TTF that supports Hebrew."
        )

        # Generate report for the asset inserted into the test database
        req = self.factory.post(
            "/api/reports",
            data=json.dumps({"assetId": self.asset.id}),
            content_type="application/json",
        )
        resp = views.reports(req)
        self.assertEqual(resp.status_code, 201, resp.content)

        filename = json.loads(resp.content)["report"]["filename"]
        path = os.path.join(self.tmpdir, filename)
        self.assertTrue(os.path.exists(path), f"Expected PDF file at path {path}")

        # Verify the Report model points to the correct URL and path
        report = Report.objects.get(filename=filename)
        self.assertEqual(report.file_path, path)
        self.assertEqual(report.file_url, f"/reports/{filename}")
        self.assertEqual(report.asset_id, self.asset.id)

        # Extract text and verify Hebrew section titles exist
        reader = PdfReader(path)
        extracted = ""
        for page in reader.pages:
            try:
                extracted += page.extract_text() or ""
            except Exception:
                pass

        # Look for all-Hebrew titles
        must_have = [
            'דו"ח נכס',
            'פרטי הנכס',
            'אנליזה פיננסית',
            'תוכניות וזכויות בנייה',
            'מידע סביבתי וסיכונים',
            'מסמכים וזיהוי איש קשר',
            'סיכונים',
            'פרטי קשר',
        ]
        missing = [t for t in must_have if t not in extracted]
        self.assertFalse(
            missing,
            f"The following Hebrew titles were not found in the text: {missing}\n"
            f"Beginning of extracted text: {extracted[:350]!r}"
        )

        # Ensure asset-specific data from the database made it into the PDF
        self.assertIn('רחוב הרצל', extracted)
        
        # Additional validation: Check that Hebrew text is properly rendered
        # If the font is working, Hebrew text should appear as readable text, not as individual characters
        hebrew_address = 'רחוב הרצל 123, תל אביב'
        if hebrew_address in extracted:
            print(f"✓ Hebrew address found in PDF: {hebrew_address}")
        else:
            # Check if it's rendered as individual characters (font issue)
            individual_chars = ' '.join(hebrew_address)
            if individual_chars in extracted:
                print(f"⚠ Hebrew text rendered as individual characters (font issue): {individual_chars}")
            else:
                print(f"✗ Hebrew address not found in PDF. Extracted text preview: {extracted[:200]}")

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
        self.assertEqual(report.file_url, f"/reports/{filename}")
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
