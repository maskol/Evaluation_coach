#!/usr/bin/env python3
"""
Test script to verify PI calculation from resolved_date for Done features
"""

import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from database import SessionLocal, RuntimeConfiguration
import json


def calculate_pi_from_date(resolved_date: str) -> str:
    """Calculate PI based on resolved date using PI configurations."""
    try:
        resolved_dt = datetime.strptime(resolved_date, "%Y-%m-%d")

        # Get PI configurations from database
        db = SessionLocal()
        config_entry = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == "pi_configurations")
            .first()
        )

        if config_entry and config_entry.config_value:
            pi_configurations = json.loads(config_entry.config_value)

            # Find which PI the resolved date falls into
            for pi_config in pi_configurations:
                start_date = datetime.strptime(pi_config["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(pi_config["end_date"], "%Y-%m-%d")

                if start_date <= resolved_dt <= end_date:
                    db.close()
                    return pi_config.get("pi")

        db.close()
        return "No PI found"

    except Exception as e:
        return f"Error: {e}"


def main():
    print("=" * 80)
    print("PI Calculation Test from Resolved Date")
    print("=" * 80)
    print()

    # Test case: FTART-979 resolved on 2026-01-07 should be in 26Q1
    test_cases = [
        ("2026-01-07", "26Q1", "FTART-979 example"),
        ("2025-12-15", "25Q4", "Late 25Q4"),
        ("2025-10-01", "25Q4", "Early 25Q4"),
        ("2026-04-15", "26Q2", "Mid 26Q2"),
    ]

    print("Testing PI calculation from resolved dates:")
    print()

    for resolved_date, expected_pi, description in test_cases:
        calculated_pi = calculate_pi_from_date(resolved_date)
        status = "✅" if calculated_pi == expected_pi else "❌"
        print(f"{status} {description}")
        print(f"   Resolved: {resolved_date}")
        print(f"   Expected PI: {expected_pi}")
        print(f"   Calculated PI: {calculated_pi}")
        print()


if __name__ == "__main__":
    main()
