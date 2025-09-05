import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from .models import Asset, Report
from .pdf_generator import HebrewPDFGenerator
from .constants import DEFAULT_REPORT_SECTIONS

logger = logging.getLogger(__name__)


class ReportService:
    """Service class for handling report operations."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.reports_dir = os.environ.get(
            'REPORTS_DIR',
            str((base_dir.parent / 'realestate-broker-ui' / 'public' / 'reports').resolve())
        )
        logger.info("Reports directory set to %s", self.reports_dir)
        self.pdf_generator = HebrewPDFGenerator(base_dir)
    
    def create_report(self, asset_id: int, sections: Optional[List[str]] = None) -> Optional[Report]:
        """Create a new report for an asset."""
        asset: Optional[Asset]
        try:
            asset = Asset.objects.get(id=asset_id)
        except Asset.DoesNotExist:
            asset = None
            logger.warning("Asset %s not found, generating placeholder report", asset_id)

        try:
            listing = self.pdf_generator.create_asset_listing(asset)
            report = Report.objects.create(
                asset=asset,
                report_type='asset',
                status='generating',
                filename='',
                file_path='',
                title=listing['address'],
                description=f'Asset report for {listing["address"]}',
                pages=1,
                sections=sections or DEFAULT_REPORT_SECTIONS,
            )

            filename = f"r{report.id}.pdf"
            os.makedirs(self.reports_dir, exist_ok=True)
            file_path = os.path.join(self.reports_dir, filename)

            report.filename = filename
            report.file_path = file_path
            report.save()

            logger.info("Created report %s for asset %s at %s", report.id, asset_id, file_path)
            return report
        except Exception:
            logger.exception("Error creating report for asset %s", asset_id)
            return None
    
    def generate_pdf(self, report: Report) -> bool:
        """Generate the PDF file for a report."""
        try:
            success = self.pdf_generator.generate_report(
                asset=report.asset,
                report=report,
                file_path=report.file_path,
                sections=report.sections or DEFAULT_REPORT_SECTIONS,
                use_template=False,
            )
            if success:
                logger.info("Generated PDF for report %s", report.id)
            else:
                logger.error("PDF generation reported failure for report %s", report.id)
            return success
        except Exception as e:
            logger.exception("Error generating PDF for report %s", report.id)
            report.mark_failed(str(e))
            return False
    
    def get_reports_list(self) -> list:
        """Get list of all reports."""
        reports_list = []
        for report in Report.objects.all().order_by('-generated_at'):
            reports_list.append({
                'id': report.id,
                'assetId': report.asset.id if report.asset else None,
                'address': report.title or 'N/A',
                'filename': report.filename,
                'createdAt': report.generated_at.isoformat(),
                'status': report.status,
                'pages': report.pages,
                'fileSize': report.file_size,
            })
        return reports_list
    
    def delete_report(self, report_id: int) -> bool:
        """Delete a specific report."""
        try:
            report = Report.objects.get(id=report_id)
            return report.delete_report()
        except Report.DoesNotExist:
            logger.warning("Report %s not found", report_id)
            return False
        except Exception:
            logger.exception("Error deleting report %s", report_id)
            return False
    
    def get_report_by_id(self, report_id: int) -> Optional[Report]:
        """Get a report by ID."""
        try:
            return Report.objects.get(id=report_id)
        except Report.DoesNotExist:
            return None
    
    def get_report_by_filename(self, filename: str) -> Optional[Report]:
        """Get a report by filename."""
        try:
            return Report.objects.get(filename=filename)
        except Report.DoesNotExist:
            return None
