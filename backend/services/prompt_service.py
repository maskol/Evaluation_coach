"""
Prompt Management Service
Handles CRUD operations and versioning for LLM prompts
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil


class PromptService:
    """Service for managing LLM prompts with versioning"""

    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent / "data" / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_file = self.prompts_dir / "prompts.json"
        self.history_dir = self.prompts_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Initialize default prompts if file doesn't exist
        if not self.prompts_file.exists():
            self._initialize_default_prompts()

    def _initialize_default_prompts(self):
        """Initialize with default prompts from current codebase"""
        default_prompts = {
            "coach_system": {
                "id": "coach_system",
                "name": "AI Coach System Prompt",
                "description": "Main system prompt for the AI Coach that defines persona, mission, and output format",
                "prompt": """You are an elite Agile strategy expert and SAFe transformation coach with 15+ years of experience coaching Fortune 500 companies. You have deep expertise in flow metrics, Lean principles, Product Operating Models, and organizational transformation.

YOUR COACHING PERSONAS:
- Strategic Advisor: Guide long-term vision, portfolio strategy, and organizational design.
- Tactical Coach: Help teams improve daily flow, reduce bottlenecks, and run experiments.
- Challenger: Ask tough questions that expose assumptions, tradeoffs, and root causes.

YOUR MISSION:
1. Interpret provided metrics/insights without inventing data.
2. Propose 2-4 concrete, testable experiments/actions.
3. Ask 1-3 challenging questions that provoke reflection.
4. Suggest the next best step in this app (e.g., switch scope, generate insights, check metrics).
5. Reference SAFe/Lean best practices and maturity benchmarks when relevant.

OUTPUT FORMAT (HTML only, no Markdown):
- Start with a 2-3 sentence assessment
- <strong>Proposed Actions:</strong> <ul><li>...</li></ul>
- <strong>Challenging Questions:</strong> <ul><li>...</li></ul>
- <strong>Evidence Used:</strong> (cite key numbers you relied on)
- <strong>Next Step:</strong> (what to do in this app)

SAFe BUSINESS AGILITY MATURITY (use as benchmark):
Level 1 - Initial: Ad-hoc processes, reactive, siloed teams
Level 2 - Managed: Basic Scrum/Kanban, some flow metrics tracked
Level 3 - Defined: SAFe adopted, ARTs coordinated, PI Planning regular
Level 4 - Quantitatively Managed: Data-driven decisions, predictable delivery, flow optimization
Level 5 - Optimizing: Continuous improvement culture, strategic agility, world-class metrics""",
                "version": 1,
                "active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "created_by": "system",
                "tags": ["system", "coach", "main"],
            },
            "insight_analysis": {
                "id": "insight_analysis",
                "name": "Insight Analysis Expert Commentary",
                "description": "Prompt for generating expert commentary on insights and recommendations",
                "prompt": """You are an expert Agile Coach and SAFe consultant with 15+ years of experience coaching Fortune 500 companies. You have deep expertise in flow metrics, lean principles, and organizational transformation.

INSIGHT ANALYSIS:
Title: {insight_title}

Observation: {observation}

Interpretation: {interpretation}

Key Metrics:
{metrics_str}

Root Causes Identified:
{root_causes_str}

Recommended Actions:
{recommendations_str}

As an experienced agile coach, provide a brief (2-3 sentences) expert commentary that:
1. Validates or adds context to the findings from your industry experience
2. Highlights the most critical aspect teams often overlook
3. Provides encouragement or urgency as appropriate

Keep it conversational, actionable, and grounded in real-world experience. Do not repeat the observation or recommendations - add NEW insights from your expertise.""",
                "version": 1,
                "active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "created_by": "system",
                "tags": ["analysis", "insights", "expert"],
            },
            "insight_system": {
                "id": "insight_system",
                "name": "Insight Generation System Prompt",
                "description": "System prompt for insight generation with expert guidance",
                "prompt": """You are an expert Agile Coach and SAFe consultant with extensive experience in enterprise agile transformations. You provide practical, experience-based guidance.""",
                "version": 1,
                "active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "created_by": "system",
                "tags": ["system", "insights", "brief"],
            },
        }

        self._save_prompts(default_prompts)

    def _save_prompts(self, prompts: Dict[str, Any]):
        """Save prompts to file"""
        with open(self.prompts_file, "w") as f:
            json.dump(prompts, f, indent=2)

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from file"""
        if not self.prompts_file.exists():
            return {}
        with open(self.prompts_file, "r") as f:
            return json.load(f)

    def _save_version_history(self, prompt_id: str, prompt_data: Dict[str, Any]):
        """Save a version to history"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        version = prompt_data.get("version", 1)
        history_file = self.history_dir / f"{prompt_id}_v{version}_{timestamp}.json"

        with open(history_file, "w") as f:
            json.dump(prompt_data, f, indent=2)

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts"""
        prompts = self._load_prompts()
        return list(prompts.values())

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific prompt by ID"""
        prompts = self._load_prompts()
        return prompts.get(prompt_id)

    def get_active_prompt(self, prompt_id: str) -> Optional[str]:
        """Get the active prompt text for a given ID"""
        prompt_data = self.get_prompt(prompt_id)
        if prompt_data and prompt_data.get("active"):
            return prompt_data.get("prompt")
        return None

    def create_prompt(
        self,
        prompt_id: str,
        name: str,
        description: str,
        prompt: str,
        tags: Optional[List[str]] = None,
        created_by: str = "user",
    ) -> Dict[str, Any]:
        """Create a new prompt"""
        prompts = self._load_prompts()

        if prompt_id in prompts:
            raise ValueError(f"Prompt with ID '{prompt_id}' already exists")

        new_prompt = {
            "id": prompt_id,
            "name": name,
            "description": description,
            "prompt": prompt,
            "version": 1,
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": created_by,
            "tags": tags or [],
        }

        prompts[prompt_id] = new_prompt
        self._save_prompts(prompts)
        self._save_version_history(prompt_id, new_prompt)

        return new_prompt

    def update_prompt(
        self,
        prompt_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        updated_by: str = "user",
    ) -> Dict[str, Any]:
        """Update an existing prompt (creates new version)"""
        prompts = self._load_prompts()

        if prompt_id not in prompts:
            raise ValueError(f"Prompt with ID '{prompt_id}' not found")

        current = prompts[prompt_id]

        # Save current version to history before updating
        self._save_version_history(prompt_id, current)

        # Update fields
        if name is not None:
            current["name"] = name
        if description is not None:
            current["description"] = description
        if prompt is not None:
            current["prompt"] = prompt
            current["version"] = current.get("version", 1) + 1
        if tags is not None:
            current["tags"] = tags

        current["updated_at"] = datetime.utcnow().isoformat()
        current["updated_by"] = updated_by

        prompts[prompt_id] = current
        self._save_prompts(prompts)

        return current

    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt"""
        prompts = self._load_prompts()

        if prompt_id not in prompts:
            return False

        # Save to history before deleting
        self._save_version_history(prompt_id, prompts[prompt_id])

        del prompts[prompt_id]
        self._save_prompts(prompts)

        return True

    def toggle_active(self, prompt_id: str) -> Dict[str, Any]:
        """Toggle active status of a prompt"""
        prompts = self._load_prompts()

        if prompt_id not in prompts:
            raise ValueError(f"Prompt with ID '{prompt_id}' not found")

        prompts[prompt_id]["active"] = not prompts[prompt_id].get("active", True)
        prompts[prompt_id]["updated_at"] = datetime.utcnow().isoformat()

        self._save_prompts(prompts)

        return prompts[prompt_id]

    def get_prompt_history(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get version history for a prompt"""
        history_files = sorted(
            self.history_dir.glob(f"{prompt_id}_v*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        history = []
        for file in history_files:
            with open(file, "r") as f:
                history.append(json.load(f))

        return history

    def restore_version(self, prompt_id: str, version: int) -> Dict[str, Any]:
        """Restore a specific version of a prompt"""
        history = self.get_prompt_history(prompt_id)

        # Find the version in history
        version_data = None
        for hist in history:
            if hist.get("version") == version:
                version_data = hist
                break

        if not version_data:
            raise ValueError(f"Version {version} not found for prompt '{prompt_id}'")

        # Update to this version (will create a new version)
        return self.update_prompt(
            prompt_id=prompt_id,
            name=version_data.get("name"),
            description=version_data.get("description"),
            prompt=version_data.get("prompt"),
            tags=version_data.get("tags"),
            updated_by=f"restored_from_v{version}",
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about prompts"""
        prompts = self._load_prompts()

        active_count = sum(1 for p in prompts.values() if p.get("active"))
        total_versions = 0

        for prompt_id in prompts.keys():
            history = self.get_prompt_history(prompt_id)
            total_versions += len(history)

        return {
            "total_prompts": len(prompts),
            "active_prompts": active_count,
            "inactive_prompts": len(prompts) - active_count,
            "total_versions": total_versions,
        }


# Singleton instance
prompt_service = PromptService()
