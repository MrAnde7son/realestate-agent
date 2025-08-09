import argparse
import logging
import os
from .tel_aviv_gis import query_tel_aviv_permits


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Tel Aviv GIS permits and optionally download PDFs")
    parser.add_argument("--address-where", dest="address_where", default="t_rechov LIKE '%הגולן%' AND ms_bayit = 1", help="SQL WHERE clause for address geocoding (layer 0)")
    parser.add_argument("--permit-where", dest="permit_where", default=os.getenv("PERMIT_WHERE", "1=1"), help="SQL WHERE clause for permits (layer 772)")
    parser.add_argument("--distance", dest="distance_meters", type=int, default=2000, help="Buffer distance in meters for geometry filter")
    parser.add_argument("--save-dir", dest="save_dir", default="permits", help="Directory to save permit PDFs (omit to skip downloads)")
    parser.add_argument("--log-level", dest="log_level", default=os.getenv("LOG_LEVEL", "INFO"), help="Logging level (DEBUG, INFO, WARNING, ERROR)")

    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    features = query_tel_aviv_permits(
        address_where=args.address_where,
        permit_where=args.permit_where,
        distance_meters=args.distance_meters,
        save_dir=args.save_dir,
    )

    print(f"Found {len(features)} features")


if __name__ == "__main__":
    main() 