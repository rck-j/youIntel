from __future__ import annotations

from pathlib import Path


class PromptService:
    """Loads prompt templates from the prompts directory."""

    def __init__(self, prompts_dir: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[3]
        self.prompts_dir = Path(prompts_dir) if prompts_dir else base_dir / "prompts"

    def load_prompt(self, file_name: str) -> str:
        prompt_path = self.prompts_dir / file_name
        return prompt_path.read_text(encoding="utf-8").strip()
