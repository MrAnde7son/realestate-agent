import os
import json
import shutil
import tempfile

from django.test import TestCase, RequestFactory
from pypdf import PdfReader

from core import views

class HebrewPDFGenerationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tmpdir = tempfile.mkdtemp(prefix="reports_test_")
        views.REPORTS_DIR = self.tmpdir

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_pdf_contains_hebrew_titles(self):
        # Ensure we actually have a Hebrew-capable font
        font_name = views.get_hebrew_font_name()
        self.assertNotEqual(
            font_name, "Helvetica",
            "לא נמצא גופן עברי. הוסף core/fonts/NotoSansHebrew-Regular.ttf "
            "או הגדר REPORT_HEBREW_FONT_PATH ל-TTF שתומך בעברית."
        )

        # Generate report for mock assetId=1
        req = self.factory.post(
            "/api/reports",
            data=json.dumps({"assetId": 1}),
            content_type="application/json",
        )
        resp = views.reports(req)
        self.assertEqual(resp.status_code, 201, resp.content)

        filename = resp.json()["report"]["filename"]
        path = os.path.join(self.tmpdir, filename)
        self.assertTrue(os.path.exists(path), f"ציפינו לקובץ PDF בנתיב {path}")

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
            'דו"ח נכס - ניתוח כללי',
            'תוכניות וזכויות בנייה',
            'מידע סביבתי',
            'מסמכים וסיכום',
            'פרטי הנכס',
            'אנליזה פיננסית',
            'המלצת השקעה',
            'תוכניות מקומיות ומפורטות',
            'זכויות בנייה מפורטות',
            'סיכונים',
            'מסמכים זמינים',
            'פרטי קשר',
        ]
        missing = [t for t in must_have if t not in extracted]
        self.assertFalse(
            missing,
            f"הכותרות העבריות הבאות לא נמצאו בטקסט: {missing}\n"
            f"תחילת הטקסט שהופק: {extracted[:350]!r}"
        )