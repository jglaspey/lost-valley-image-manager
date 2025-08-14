#!/usr/bin/env python3
"""
Reprocess previously failed images using the pipeline config.

Usage:
  python scripts/reprocess_failed.py [--limit N] [--config PATH]

Defaults:
  --config defaults to config/config.yaml
  --limit defaults to processing all failed images
"""

import argparse
from image_processor.core.config import Config
from image_processor.vision.service import VisionAnalysisService


def main():
    parser = argparse.ArgumentParser(description="Reprocess failed images")
    parser.add_argument("--limit", type=int, default=None, help="Max failed images to reprocess")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to config YAML")
    args = parser.parse_args()

    config = Config.from_file(args.config)
    config.validate(check_credentials=True)

    svc = VisionAnalysisService(config)
    print("Reprocessing failed images...")
    result = svc.reprocess_failed_files(limit=args.limit)
    print("Reprocessing complete!")
    print(f"  Processed: {result['processed']}")
    print(f"  Failed:    {result['failed']}")
    print(f"  Skipped:   {result.get('skipped', 0)}")


if __name__ == "__main__":
    main()


