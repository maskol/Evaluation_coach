# Excel Import Service for Evaluation Coach
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from api_models import JiraIssueCreate
from sqlalchemy.orm import Session


class ExcelImportService:
    """Service for importing and staging Excel data before database storage"""

    def __init__(self):
        self.staged_data: List[Dict[str, Any]] = []
        self.column_mappings: Dict[str, str] = {
            # Common Excel column names -> Database field mappings
            "Key": "issue_key",
            "Issue Key": "issue_key",
            "ID": "issue_key",
            "Type": "issue_type",
            "T": "issue_type",  # Jira short form
            "Issue Type": "issue_type",
            "Summary": "summary",
            "Title": "summary",
            "Description": "description",
            "Status": "status",
            "Priority": "priority",
            "Team": "team",
            "ART": "art",
            "Portfolio": "portfolio",
            "Project": "portfolio",  # Alternative name
            "Story Points": "story_points",
            "Estimate": "original_estimate",
            "Original Estimate": "original_estimate",
            "Created": "created_date",
            "Created Date": "created_date",
            "Start Date": "created_date",  # Alternative
            "Updated": "updated_date",
            "Updated Date": "updated_date",
            "Resolved": "resolved_date",
            "Resolved Date": "resolved_date",
            "Resolution Date": "resolved_date",
            "Reporter": "reporter",
            "Assignee": "assignee",
            "Labels": "labels",
            "Epic Link": "epic",
            "Epic": "epic",
            "Parent": "parent_key",
            "Domain": "custom_domain",  # Custom field
            "Sprint": "sprint",
            "Component": "components",
            "Components": "components",
        }

    def read_excel_file(
        self, file_path: str, sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        try:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Read first sheet
                df = pd.read_excel(file_path)

            return df
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")

    def detect_issue_type(self, row: pd.Series) -> str:
        """Detect issue type from row data"""
        # Check if Type column exists
        if "Type" in row and pd.notna(row["Type"]):
            return str(row["Type"])
        if "Issue Type" in row and pd.notna(row["Issue Type"]):
            return str(row["Issue Type"])

        # Try to infer from other fields
        summary = str(row.get("Summary", "")).lower()
        if "epic" in summary:
            return "Epic"
        elif "feature" in summary:
            return "Feature"
        elif "story" in summary or "user story" in summary:
            return "Story"
        elif "bug" in summary or "defect" in summary:
            return "Bug"

        return "Story"  # Default

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Convert various date formats to datetime object"""
        if date_value is None or (
            isinstance(date_value, str) and not date_value.strip()
        ):
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()

        if isinstance(date_value, str):
            try:
                # Try parsing ISO format
                return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            except:
                try:
                    # Try pandas parser
                    return pd.to_datetime(date_value).to_pydatetime()
                except:
                    return None

        return None

    def _clean_text(self, text: Any) -> str:
        """Clean text by removing Excel encoding artifacts"""
        if text is None:
            return None

        text_str = str(text)
        # Remove Excel carriage return encoding
        text_str = text_str.replace("_x000D_", "")
        # Remove Confluence/Jira formatting markers
        text_str = text_str.replace("h3. ", "").replace("h2. ", "").replace("h1. ", "")
        # Remove other common artifacts
        text_str = text_str.replace("\r\n", "\n").replace("\r", "\n")
        return text_str.strip()

    def map_excel_row_to_issue(self, row: pd.Series, row_index: int) -> Dict[str, Any]:
        """Map a single Excel row to issue structure"""

        issue_data = {
            "row_number": row_index + 2,  # Excel row (accounting for header)
            "issue_key": None,
            "issue_type": self.detect_issue_type(row),
            "summary": None,
            "description": None,
            "status": "To Do",
            "priority": "Medium",
            "team": None,
            "art": None,
            "portfolio": None,
            "story_points": None,
            "original_estimate": None,
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
            "resolved_date": None,
            "reporter": None,
            "assignee": None,
            "labels": [],
            "epic_link": None,
            "parent_key": None,
            "custom_fields": {},
            "validation_errors": [],
            "validation_warnings": [],
        }

        # Map known columns
        for excel_col, db_field in self.column_mappings.items():
            if excel_col in row and pd.notna(row[excel_col]):
                value = row[excel_col]

                # Handle dates
                if db_field in ["created_date", "updated_date", "resolved_date"]:
                    if isinstance(value, pd.Timestamp):
                        issue_data[db_field] = value.isoformat()
                    elif value:
                        issue_data[db_field] = str(value)

                # Handle lists
                elif db_field == "labels" and value:
                    issue_data[db_field] = [
                        label.strip() for label in str(value).split(",")
                    ]

                # Handle numbers
                elif db_field in ["story_points", "original_estimate"]:
                    try:
                        issue_data[db_field] = float(value) if value else None
                    except:
                        issue_data[db_field] = None

                # Handle strings
                else:
                    issue_data[db_field] = self._clean_text(value) if value else None

        # Store unmapped columns in custom_fields
        for col in row.index:
            if col not in self.column_mappings:
                if pd.notna(row[col]):
                    issue_data["custom_fields"][col] = self._clean_text(row[col])

        # Calculate lead-time if we have created_date and resolved_date
        if issue_data.get("created_date") and issue_data.get("resolved_date"):
            try:
                if isinstance(issue_data["created_date"], str):
                    created = pd.to_datetime(issue_data["created_date"])
                else:
                    created = issue_data["created_date"]

                if isinstance(issue_data["resolved_date"], str):
                    resolved = pd.to_datetime(issue_data["resolved_date"])
                else:
                    resolved = issue_data["resolved_date"]

                lead_time_days = (resolved - created).days
                issue_data["custom_fields"]["lead_time_days"] = lead_time_days
            except:
                pass  # Skip if dates can't be parsed

        # Validation
        if not issue_data["issue_key"]:
            issue_data["validation_errors"].append("Missing Issue Key")

        if not issue_data["summary"]:
            issue_data["validation_errors"].append("Missing Summary")

        if not issue_data["issue_type"]:
            issue_data["validation_warnings"].append("Issue Type was auto-detected")

        return issue_data

    def import_excel_to_staging(
        self, file_path: str, sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Import Excel file and stage data for review"""
        try:
            df = self.read_excel_file(file_path, sheet_name)

            # Clear previous staging
            self.staged_data = []

            # Process each row
            for index, row in df.iterrows():
                # Skip empty rows
                if row.isna().all():
                    continue

                issue_data = self.map_excel_row_to_issue(row, index)
                self.staged_data.append(issue_data)

            # Calculate statistics
            total_issues = len(self.staged_data)
            issues_with_errors = sum(
                1 for item in self.staged_data if item["validation_errors"]
            )
            issues_with_warnings = sum(
                1 for item in self.staged_data if item["validation_warnings"]
            )

            # Group by type
            type_counts = {}
            for item in self.staged_data:
                issue_type = item["issue_type"]
                type_counts[issue_type] = type_counts.get(issue_type, 0) + 1

            return {
                "success": True,
                "total_rows": len(df),
                "total_issues": total_issues,
                "issues_with_errors": issues_with_errors,
                "issues_with_warnings": issues_with_warnings,
                "type_counts": type_counts,
                "column_mappings": self.column_mappings,
                "detected_columns": list(df.columns),
                "message": f"Successfully imported {total_issues} issues for review",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to import Excel file: {str(e)}",
            }

    def get_staged_data(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get staged data with pagination"""
        return self.staged_data[skip : skip + limit]

    def update_staged_issue(
        self, row_number: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a staged issue before committing to database"""
        for item in self.staged_data:
            if item["row_number"] == row_number:
                # Update fields
                for key, value in updates.items():
                    # Handle custom_fields specially - merge rather than replace
                    if key == "custom_fields" and isinstance(value, dict):
                        if "custom_fields" not in item:
                            item["custom_fields"] = {}
                        item["custom_fields"].update(value)
                    # Skip read-only fields
                    elif key not in [
                        "row_number",
                        "validation_errors",
                        "validation_warnings",
                    ]:
                        item[key] = value

                # Re-validate
                item["validation_errors"] = []
                if not item["issue_key"]:
                    item["validation_errors"].append("Missing Issue Key")
                if not item["summary"]:
                    item["validation_errors"].append("Missing Summary")

                return {"success": True, "updated_issue": item}

        return {"success": False, "error": "Issue not found in staging"}

    def delete_staged_issue(self, row_number: int) -> Dict[str, Any]:
        """Remove an issue from staging"""
        self.staged_data = [
            item for item in self.staged_data if item["row_number"] != row_number
        ]
        return {"success": True, "message": "Issue removed from staging"}

    def commit_to_database(
        self, db: Session, selected_rows: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Commit staged data to database"""
        from database import JiraIssue

        # Determine which issues to commit
        if selected_rows:
            issues_to_commit = [
                item for item in self.staged_data if item["row_number"] in selected_rows
            ]
        else:
            # Only commit issues without errors
            issues_to_commit = [
                item for item in self.staged_data if not item["validation_errors"]
            ]

        committed_count = 0
        skipped_count = 0
        errors = []

        for item in issues_to_commit:
            try:
                # Check if issue already exists
                existing = (
                    db.query(JiraIssue)
                    .filter(JiraIssue.issue_key == item["issue_key"])
                    .first()
                )

                if existing:
                    # Update existing
                    for key, value in item.items():
                        if (
                            key
                            not in [
                                "row_number",
                                "validation_errors",
                                "validation_warnings",
                                "custom_fields",
                            ]
                            and value is not None
                        ):
                            setattr(existing, key, value)

                    # Update custom fields
                    if item["custom_fields"]:
                        existing_custom = existing.custom_fields or {}
                        existing_custom.update(item["custom_fields"])
                        existing.custom_fields = existing_custom
                else:
                    # Create new - convert date strings to datetime objects
                    new_issue = JiraIssue(
                        issue_key=item["issue_key"],
                        issue_type=item["issue_type"],
                        summary=item["summary"],
                        description=item["description"],
                        status=item["status"],
                        priority=item["priority"],
                        team=item["team"],
                        art=item["art"],
                        portfolio=item["portfolio"],
                        story_points=item["story_points"],
                        original_estimate=item["original_estimate"],
                        created_date=self._parse_date(item.get("created_date")),
                        updated_date=self._parse_date(item.get("updated_date")),
                        resolved_date=self._parse_date(item.get("resolved_date")),
                        reporter=item["reporter"],
                        assignee=item["assignee"],
                        labels=item["labels"] if item["labels"] else None,
                        epic_link=item["epic_link"],
                        parent_key=item["parent_key"],
                        custom_fields=item["custom_fields"],
                    )
                    db.add(new_issue)

                committed_count += 1

            except Exception as e:
                skipped_count += 1
                errors.append(
                    {
                        "row_number": item["row_number"],
                        "issue_key": item["issue_key"],
                        "error": str(e),
                    }
                )

        try:
            db.commit()

            # Clear committed items from staging
            if selected_rows:
                self.staged_data = [
                    item
                    for item in self.staged_data
                    if item["row_number"] not in selected_rows
                ]
            else:
                self.staged_data = [
                    item for item in self.staged_data if item["validation_errors"]
                ]

            return {
                "success": True,
                "committed": committed_count,
                "skipped": skipped_count,
                "errors": errors,
                "remaining_staged": len(self.staged_data),
                "message": f"Successfully committed {committed_count} issues to database",
            }

        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to commit to database: {str(e)}",
            }

    def export_template(
        self, issue_types: List[str] = ["Epic", "Feature", "Story"]
    ) -> pd.DataFrame:
        """Generate an Excel template for import"""
        template_data = {
            "Issue Key": ["PROJ-1", "PROJ-2", "PROJ-3"],
            "Issue Type": issue_types[:3] if len(issue_types) >= 3 else issue_types,
            "Summary": ["Example Epic", "Example Feature", "Example User Story"],
            "Description": [
                "Epic description",
                "Feature description",
                "Story description",
            ],
            "Status": ["To Do", "To Do", "To Do"],
            "Priority": ["High", "Medium", "Medium"],
            "Team": ["Team Alpha", "Team Alpha", "Team Alpha"],
            "ART": ["Platform", "Platform", "Platform"],
            "Portfolio": [
                "Digital Transformation",
                "Digital Transformation",
                "Digital Transformation",
            ],
            "Story Points": [None, 13, 5],
            "Epic Link": [None, "PROJ-1", "PROJ-2"],
            "Labels": ["strategic", "mvp,priority", "technical"],
        }

        return pd.DataFrame(template_data)


# Global instance
excel_import_service = ExcelImportService()
excel_import_service = ExcelImportService()
