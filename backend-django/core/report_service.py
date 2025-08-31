import os
from pathlib import Path
from typing import Optional, Dict, Any
from .models import Asset, Report
from .pdf_generator import HebrewPDFGenerator


class ReportService:
    """Service class for handling report operations."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.reports_dir = os.environ.get(
            'REPORTS_DIR',
            str((base_dir.parent / 'realestate-broker-ui' / 'public' / 'reports').resolve())
        )
        self.pdf_generator = HebrewPDFGenerator(base_dir)
    
    def create_report(self, asset_id: int) -> Optional[Report]:
        """Create a new report for an asset."""
        try:
            # Get the asset
            asset = Asset.objects.get(id=asset_id)
            
            # Create report record
            listing = self.pdf_generator.create_asset_listing(asset)
            report = Report.objects.create(
                asset=asset,
                report_type='asset',
                status='generating',
                filename='',
                file_path='',
                title=listing['address'],
                description=f'Asset report for {listing["address"]}',
                pages=4,
            )
            
            # Generate filename and file path
            filename = f"r{report.id}.pdf"
            os.makedirs(self.reports_dir, exist_ok=True)
            file_path = os.path.join(self.reports_dir, filename)
            
            # Update report with file information
            report.filename = filename
            report.file_path = file_path
            report.save()
            
            return report
            
        except Asset.DoesNotExist:
            print(f"Asset {asset_id} not found")
            return None
        except Exception as e:
            print(f"Error creating report: {e}")
            return None
    
    def generate_pdf(self, report: Report) -> bool:
        """Generate the PDF file for a report."""
        try:
            if not report.asset:
                print(f"Report {report.id} has no linked asset")
                return False
            
            # Generate PDF using the generator
            success = self.pdf_generator.generate_report(
                asset=report.asset,
                report=report,
                file_path=report.file_path
            )
            
            return success
            
        except Exception as e:
            print(f"Error generating PDF for report {report.id}: {e}")
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
            print(f"Report {report_id} not found")
            return False
        except Exception as e:
            print(f"Error deleting report {report_id}: {e}")
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
