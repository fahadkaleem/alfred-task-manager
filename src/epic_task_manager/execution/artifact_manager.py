# Standard library imports
import json
import logging
from pathlib import Path
import re
from typing import Any

from jinja2 import Environment
from pydantic import BaseModel
from tabulate import tabulate

# Third-party imports
import yaml

# Local application imports
from epic_task_manager.config.settings import settings
from epic_task_manager.constants import (
    ARCHIVE_DIR_NAME,
    ARTIFACT_FILENAME,
    PHASE_NUMBERS,
)
from epic_task_manager.execution.constants import (
    ARCHIVE_FILENAME_FORMAT,
)
from epic_task_manager.execution.exceptions import ArtifactNotFoundError, InvalidArtifactError


class ArtifactManager:
    """Handles reading and writing the structured markdown artifacts."""

    def get_task_dir(self, task_id: str) -> Path:
        """Get task directory in the workspace."""
        return settings.workspace_dir / task_id

    def get_artifact_path(self, task_id: str) -> Path:
        return self.get_task_dir(task_id) / ARTIFACT_FILENAME

    def get_archive_path(self, task_id: str, phase_name: str, version: int) -> Path:
        archive_dir = self.get_task_dir(task_id) / ARCHIVE_DIR_NAME
        phase_number = PHASE_NUMBERS.get(phase_name, version)
        return archive_dir / ARCHIVE_FILENAME_FORMAT.format(phase_number=phase_number, phase_name=phase_name)

    def get_json_archive_path(self, task_id: str, phase_name: str) -> Path:
        """Gets the path for a JSON artifact in the archive."""
        archive_dir = self.get_task_dir(task_id) / ARCHIVE_DIR_NAME
        phase_number = PHASE_NUMBERS.get(phase_name, 1)
        # Use the same base name as the markdown artifact, but with a .json extension
        filename = ARCHIVE_FILENAME_FORMAT.format(phase_number=phase_number, phase_name=phase_name).replace(".md", ".json")
        return archive_dir / filename

    def create_task_structure(self, task_id: str) -> None:
        """Creates the necessary directories for a new task."""
        task_dir = self.get_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / ARCHIVE_DIR_NAME).mkdir(exist_ok=True)

    def write_artifact(self, task_id: str, artifact_content: str) -> None:
        """Writes content to the live task artifact file."""
        artifact_path = self.get_artifact_path(task_id)
        artifact_path.write_text(artifact_content, encoding="utf-8")

    def read_artifact(self, task_id: str) -> str | None:
        """Reads the content of the live task artifact file."""
        artifact_path = self.get_artifact_path(task_id)
        if artifact_path.exists():
            return artifact_path.read_text(encoding="utf-8")
        return None

    def append_to_artifact(self, task_id: str, content: str) -> None:
        """
        Appends content to the live task artifact file with proper separation.

        Creates the file if it doesn't exist. Uses markdown horizontal rule (---)
        as separator between existing and new content.

        Args:
            task_id: Task identifier
            content: Content to append

        Raises:
            ValueError: If task_id or content is empty
        """
        # Validate inputs
        if not task_id or not task_id.strip():
            raise ValueError("Task ID cannot be empty")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        # Ensure task directory exists
        task_dir = self.get_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = self.get_artifact_path(task_id)

        # Read existing content if file exists
        existing_content = ""
        if artifact_path.exists():
            existing_content = artifact_path.read_text(encoding="utf-8")

        # Determine if separator is needed
        separator = ""
        if existing_content.strip():
            separator = "\n\n---\n"

        # Combine content
        new_content = existing_content + separator + content

        # Write atomically
        artifact_path.write_text(new_content, encoding="utf-8")

    def archive_artifact(self, task_id: str, phase_name: str, json_data: BaseModel | None = None) -> None:
        """Copies the live artifact to the archive and optionally saves a JSON version."""
        live_artifact = self.get_artifact_path(task_id)
        if not live_artifact.exists():
            # If there's no scratchpad but we have JSON, we should still proceed
            if json_data is None:
                return

        archive_dir = self.get_task_dir(task_id) / ARCHIVE_DIR_NAME
        archive_dir.mkdir(exist_ok=True)

        # 1. Archive the human-readable markdown artifact as before
        if live_artifact.exists():
            phase_number = PHASE_NUMBERS.get(phase_name, 1)
            archive_path = archive_dir / ARCHIVE_FILENAME_FORMAT.format(phase_number=phase_number, phase_name=phase_name)
            archive_path.write_text(live_artifact.read_text(encoding="utf-8"))

        # 2. Archive the machine-readable JSON data if provided
        if json_data:
            json_archive_path = self.get_json_archive_path(task_id, phase_name)
            # Use model_dump_json for direct serialization from a Pydantic model
            json_archive_path.write_text(json_data.model_dump_json(indent=2), encoding="utf-8")

    def read_json_artifact(self, task_id: str, phase_name: str) -> dict:
        """Reads and parses a JSON artifact from the archive."""
        json_path = self.get_json_archive_path(task_id, phase_name)
        if not json_path.exists():
            raise ArtifactNotFoundError(f"JSON artifact for phase '{phase_name}' not found.")
        try:
            with json_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidArtifactError(f"Failed to parse JSON artifact for phase '{phase_name}': {e}")

    def build_structured_artifact(self, template: str, data: dict[str, Any]) -> str:
        """Builds a complete markdown artifact from a template and data."""
        self._prepare_metadata(data)
        self._format_structured_fields(data)

        jinja_env = Environment(autoescape=False)

        # Add custom filter for markdown escaping
        def markdown_escape(text):
            """Escapes markdown special characters that can break preview."""
            if not isinstance(text, str):
                text = str(text)
            # Escape backslash sequences that can break markdown
            text = text.replace("\\n", "\n")  # Convert literal \n to actual newlines
            return text.replace("\\t", "\t")  # Convert literal \t to actual tabs

        jinja_env.filters["markdown_escape"] = markdown_escape
        jinja_template = jinja_env.from_string(template)
        return jinja_template.render(**data)

    def _prepare_metadata(self, data: dict[str, Any]) -> None:
        """Prepares metadata for the artifact."""
        metadata_dict = data.get("metadata", {})

        for key, value in metadata_dict.items():
            if key not in data:
                data[key] = value

        metadata_str = yaml.dump(metadata_dict, default_flow_style=False, sort_keys=False).rstrip("\n")
        data["metadata"] = metadata_str

    # --- New Formatting Helpers ---
    def _format_list_as_numbered_list(self, items: list) -> str:
        """Formats a simple list into a markdown numbered list."""
        if not items:
            return "N/A"
        return "\n".join([f"{i + 1}. {item}" for i, item in enumerate(items)])

    def _format_list_as_table(self, items: list[dict], headers: dict) -> str:
        """Formats a list of dictionaries into a markdown table using tabulate."""
        if not items:
            return "N/A"

        if not all(isinstance(i, dict) for i in items):
            return yaml.dump(items, default_flow_style=False, sort_keys=False)

        # Check if any cell content is very long (more than 100 chars)
        has_long_content = any(len(str(item.get(key_map, ""))) > 100 for item in items for key_map in headers.values())

        # For tables with long content, use a more readable format
        if has_long_content:
            formatted_items = []
            for idx, item in enumerate(items, 1):
                item_parts = [f"**{idx}. Entry**"]
                for header, key_map in headers.items():
                    value = item.get(key_map, "N/A")
                    # Wrap long values
                    if isinstance(value, str) and len(value) > 80:
                        # Add proper indentation for multi-line values
                        value = value.replace("\n", "\n   ")
                    item_parts.append(f"- **{header}:** {value}")
                formatted_items.append("\n".join(item_parts))
            return "\n".join(formatted_items)

        # For regular tables, use tabulate
        rows = [[item.get(key_map) for key_map in headers.values()] for item in items]
        return tabulate(rows, headers=headers.keys(), tablefmt="github")

    def _format_execution_steps(self, items: list[dict]) -> str:
        """Formats execution steps into subheadings and code blocks."""
        if not items:
            return "N/A"
        formatted_items = []
        for item in items:
            prompt_id = item.get("prompt_id", "N/A")
            prompt_text = item.get("prompt_text", "No prompt text.")
            formatted_items.append(f"#### {prompt_id}\n```\n{prompt_text}\n```")
        return "\n".join(formatted_items)

    def _format_code_modifications(self, items: list[dict]) -> str:
        """Formats code modifications into file sections and code blocks."""
        if not items:
            return "N/A"
        formatted_items = []
        for item in items:
            file_path = item.get("file_path", "N/A")
            code_block = item.get("code_block", "No code provided.")
            description = item.get("description", "No description provided.")
            formatted_items.append(f"### File: `{file_path}`\n- **Description:** {description}\n- **Code:**\n```\n{code_block}\n```")
        return "\n".join(formatted_items)

    def _format_numbered_text(self, text: str) -> str:
        """Formats text containing numbered patterns (e.g. '1. Item 2. Item') into proper numbered lists."""
        if not text or not isinstance(text, str):
            return text

        import re

        # First, normalize all numbered list formats to use "1." instead of "1)"
        text = re.sub(r"(\d+)\)", r"\1.", text)

        # Pattern to detect numbered lists in text: "1. Something 2. Something else"
        # Use a more robust approach: split by numbered patterns and reconstruct
        numbered_pattern = r"\s*(\d+)\.\s+"

        # Split the text by numbered patterns but keep the numbers
        parts = re.split(numbered_pattern, text.strip())

        if len(parts) >= 5:  # At least intro + num1 + content1 + num2 + content2
            formatted_items = []
            # Skip the intro text (parts[0]) and process pairs (number, content)
            for i in range(1, len(parts), 2):
                if i + 1 < len(parts):
                    num = parts[i]
                    content = parts[i + 1].strip()
                    # Clean up content by removing trailing punctuation before next number
                    content = re.sub(r"\s+$", "", content)
                    if content:
                        formatted_items.append(f"{num}. {content}")

            if len(formatted_items) >= 2:  # Only format if we have at least 2 valid items
                # If there's intro text, include it with a line break
                if parts[0].strip():
                    return parts[0].strip() + "\n\n" + "\n".join(formatted_items)
                # Use single line breaks between items for proper markdown formatting
                return "\n".join(formatted_items)

        return text

    def _format_structured_fields(self, data: dict[str, Any]) -> None:
        """Formats various structured fields into human-readable markdown using a dispatch table."""
        # Configuration for list fields
        list_formatter_config = {
            # Simple Lists -> Numbered List
            "acceptance_criteria": (self._format_list_as_numbered_list, None),
            "acceptance_criteria_met": (self._format_list_as_numbered_list, None),
            "key_components": (self._format_list_as_numbered_list, None),
            "dependencies": (self._format_list_as_numbered_list, None),
            # List of Dicts -> Markdown Table
            "files_modified": (self._format_list_as_table, {"File": "file", "Changes": "changes"}),
            "file_breakdown": (self._format_list_as_table, {"File Path": "file_path", "Action": "action", "Change Summary": "change_summary"}),
            # Custom Formatters for Complex Structures
            "execution_prompts": (self._format_execution_steps, None),
            "execution_steps": (self._format_execution_steps, None),  # Same format as execution_prompts
            "code_modifications": (self._format_code_modifications, None),
        }

        # Configuration for string fields that may contain numbered content
        string_formatter_config = {
            "detailed_design": self._format_numbered_text,
            "architectural_decisions": self._format_numbered_text,
            "risk_analysis": self._format_numbered_text,
        }

        # Process list fields
        for field, (formatter, config) in list_formatter_config.items():
            if field in data and isinstance(data[field], list):
                if config:
                    data[field] = formatter(data[field], config)
                else:
                    data[field] = formatter(data[field])

        # Process string fields that may contain numbered content
        for field, formatter in string_formatter_config.items():
            if field in data and isinstance(data[field], str):
                data[field] = formatter(data[field])

    def parse_artifact(self, artifact_content: str) -> tuple[dict[str, Any], str]:
        """Parses a markdown artifact into metadata and main content."""
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", artifact_content, re.DOTALL)
        if not match:
            return {}, artifact_content

        metadata_str, main_content = match.groups()

        try:
            metadata = yaml.safe_load(metadata_str)
            return metadata or {}, main_content.strip()
        except yaml.YAMLError as e:
            logging.warning(f"Failed to parse YAML metadata in artifact: {e}")
            return {}, artifact_content
