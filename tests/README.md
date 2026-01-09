# Test Scripts

This directory contains test scripts and utility tools for the Evaluation Coach application.

## Test Scripts

### Little's Law Analysis Tests
- **`test_littles_law_quality.py`** - Automated quality validation for Little's Law insights
  - Tests RAG enhancement
  - Validates scenario modeling, stage breakdown, and flow control rules
  - Run: `python tests/test_littles_law_quality.py`

- **`test_littles_law_agent.py`** - Unit tests for Little's Law analyzer node
  - Tests agent graph integration
  - Validates metric calculations
  - Run: `python tests/test_littles_law_agent.py`

- **`test_littles_law_insight.py`** - Integration tests for Little's Law insights
  - End-to-end insight generation testing
  - Run: `python tests/test_littles_law_insight.py`

### Feature Tests
- **`test_insights.py`** - General insights generation tests
- **`test_rag.py`** - RAG (Retrieval Augmented Generation) functionality tests
- **`test_strategic_targets.py`** - Strategic targets persistence and validation tests
- **`test_summary_data.py`** - Summary data aggregation tests

## Utility Scripts

- **`debug_bottleneck_data.py`** - Debug tool for bottleneck analysis data
- **`example_leadtime_usage.py`** - Example code for using the leadtime client
- **`save_targets_to_db.py`** - Utility to save strategic targets to database
- **`verify_fix.py`** - Verification script for bug fixes

## Running Tests

### Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Ensure backend is running
cd backend
uvicorn main:app --reload --port 8850
```

### Run Individual Tests
```bash
# From project root
python tests/test_littles_law_quality.py
python tests/test_insights.py
# etc.
```

### Run All Tests
```bash
# Future: pytest integration
pytest tests/
```

## Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `test_<feature_name>.py`
3. Document purpose in this README
4. Ensure tests are independent and can run in isolation

## Notes

- Some tests require the DL Webb API running at `http://localhost:8000`
- Tests use the development database `evaluation_coach.db`
- Log files are written to project root (cleaned up automatically)
