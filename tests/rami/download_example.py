#!/usr/bin/env python3
"""Example of how to download documents using RamiClient."""

import sys
from pathlib import Path

# Import test utilities to set up Python path (works in all environments)
try:
    import tests.utils.test_utils  # noqa: F401 # Sets up Python path automatically
except ImportError:
    # Fallback: if test_utils can't be imported, set up path manually
    # This handles the case when running the script directly
    current_file = Path(__file__).resolve()
    current_dir = current_file.parent
    max_levels = 5

    for _ in range(max_levels):
        has_config = any(
            (current_dir / marker).exists()
            for marker in ["pyproject.toml", "requirements.txt", "setup.py"]
        )
        has_packages = any(
            (current_dir / pkg).exists() and (current_dir / pkg).is_dir()
            for pkg in ["rami", "gov", "yad2", "gis", "orchestration"]
        )

        if has_config and has_packages:
            project_root = str(current_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                print(f"✅ Added project root to path (fallback): {project_root}")
            break

        parent = current_dir.parent
        if parent == current_dir:
            break
        current_dir = parent

from gov.rami.rami_client import RamiClient


def download_tel_aviv_plans_example():
    """Example: Download documents for Tel Aviv plans."""

    # Create client
    client = RamiClient()

    # Search for Tel Aviv plans
    search_params = {
        "planNumber": "",
        "city": 5000,  # Tel Aviv city code
        "block": "",
        "parcel": "",
        "statuses": None,
        "planTypes": [72, 21, 1, 8, 9, 10],  # Subset of plan types
        "fromStatusDate": None,
        "toStatusDate": None,
        "planTypesUsed": False,
    }

    print("🔍 Searching for Tel Aviv plans...")
    try:
        # Fetch plans
        df = client.fetch_plans(search_params)
        print(f"✅ Found {len(df)} plans")

        if len(df) == 0:
            print("No plans found")
            return

        # Show first few plans
        print("\n📋 First 5 plans:")
        for i, plan in df.head(5).iterrows():
            print(
                f"  {i + 1}. {plan['planNumber']} - {plan['cityText']} ({plan['status']})"
            )

        # Convert to list for downloading
        plans = df.head(3).to_dict("records")  # First 3 plans only

        print(f"\n📥 Downloading documents for {len(plans)} plans...")

        # Download only regulations (takanon) to start small
        results = client.download_multiple_plans_documents(
            plans,
            base_dir="tel_aviv_plans",
            doc_types=["takanon"],  # Only regulations
            overwrite=False,
        )

        print("\n📊 Download completed!")
        print(f"   Plans processed: {results['total_plans']}")
        print(f"   Files downloaded: {results['total_files_downloaded']}")
        print(f"   Files failed: {results['total_files_failed']}")

        # Show what was downloaded
        if results["total_files_downloaded"] > 0:
            print("\n📁 Check the 'tel_aviv_plans' directory for downloaded files")

    except Exception as e:
        print(f"❌ Error: {e}")


def download_specific_plan_example():
    """Example: Download all document types for a specific plan."""

    client = RamiClient()

    # Example plan data (you would get this from fetch_plans)
    specific_plan = {
        "planNumber": 'תמ"א 10/ג/12',
        "planId": 5050330,
        "cityText": "בני ברק",
        "documentsSet": {
            "takanon": {
                "path": "/IturTabotData/takanonim/telmer/5050330.pdf",
                "info": "תקנון סרוק",
            },
            "tasritim": [
                {
                    "path": "/IturTabotData\\tabot\\telmer\\5050330\\5050330_מצב מאושר-גיליון 1.pdf",
                    "info": "5050330_מצב מאושר-גיליון 1",
                }
            ],
            "mmg": {
                "path": "/IturTabotData\\download\\telmer\\5050330.zip",
                "info": "הורדת קבצי ממג 1 MB",
            },
        },
    }

    print(f"🏗️  Downloading all documents for plan: {specific_plan['planNumber']}")

    # Download all document types
    results = client.download_plan_documents(
        specific_plan,
        base_dir="specific_plan",
        doc_types=None,  # All types: takanon, tasrit, nispach, mmg
        overwrite=True,
    )

    print(f"✅ Downloaded {len(results['success'])} files")
    if results["failed"]:
        print(f"❌ Failed to download {len(results['failed'])} files")


def available_document_types_example():
    """Show what types of documents are available."""

    print("📄 Available document types:")
    print("  • takanon - תקנון (Regulations)")
    print("  • tasrit - תשריט (Drawings/Blueprints)")
    print("  • nispach - נספח (Appendices)")
    print('  • mmg - ממ"ג (MMG files)')
    print()
    print(
        "💡 You can download specific types by passing doc_types=['takanon', 'tasrit']"
    )


if __name__ == "__main__":
    print("🏙️  RAMI Client Document Download Examples\n")

    available_document_types_example()

    print("=" * 50)
    download_tel_aviv_plans_example()

    print("\n" + "=" * 50)
    download_specific_plan_example()
