"""
One-time script to save the current strategic targets to the database
Run this after restarting the backend to persist your targets.
"""

from backend.database import SessionLocal, RuntimeConfiguration
from datetime import datetime

# Your strategic targets
targets = {
    "leadtime_target_2026": 110.0,
    "leadtime_target_2027": 90.0,
    "leadtime_target_true_north": 70.0,
    "planning_accuracy_target_2026": 75.0,
    "planning_accuracy_target_2027": 80.0,
    "planning_accuracy_target_true_north": 95.0,
}

db = SessionLocal()
try:
    print("💾 Saving strategic targets to database...")

    for config_key, config_value in targets.items():
        # Check if exists
        config_row = (
            db.query(RuntimeConfiguration)
            .filter(RuntimeConfiguration.config_key == config_key)
            .first()
        )

        if config_row:
            config_row.config_value = config_value
            config_row.updated_at = datetime.now()
            print(f"   Updated {config_key} = {config_value}")
        else:
            config_row = RuntimeConfiguration(
                config_key=config_key,
                config_value=config_value,
            )
            db.add(config_row)
            print(f"   Created {config_key} = {config_value}")

    db.commit()
    print("✅ All strategic targets saved to database!")
    print("\nThese values will now persist across:")
    print("   - Page refreshes")
    print("   - Server restarts")
    print("   - Browser cache clears")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
finally:
    db.close()
