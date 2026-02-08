import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LlmClient:
    use_real: bool
    model: Optional[str]
    _client: Optional[Any] = None

    def generate(
        self,
        agent_id: str,
        system_prompt: str,
        user_prompt: str,
        csv_data: Dict[str, Any],
    ) -> str:
        if self.use_real:
            return self._generate_real(system_prompt, user_prompt)
        return self._generate_mock(agent_id, csv_data)

    def _generate_real(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        return response.output_text.strip()

    def _generate_mock(self, agent_id: str, csv_data: Dict[str, Any]) -> str:
        if agent_id == "orchestrator":
            payload = {
                "assignments": [
                    {
                        "agent_id": "model_builder",
                        "task": (
                            "Use inputs.csv and all table CSVs to produce "
                            "inputs and tables without adding new names."
                        ),
                    },
                    {
                        "agent_id": "formula_calculation",
                        "task": (
                            "Use formulas.csv to produce calculations and "
                            "reference only known inputs or tables."
                        ),
                    },
                ],
                "notes": "Keep outputs strictly JSON.",
            }
        elif agent_id == "model_builder":
            payload = {
                "inputs": [
                    {"name": item["name"], "value": item["value"]}
                    for item in csv_data.get("inputs", [])
                ],
                "tables": [
                    {
                        "name": item["name"],
                        "columns": item["columns"],
                        "rows": item["rows"],
                    }
                    for item in csv_data.get("tables", [])
                ],
            }
        elif agent_id == "formula_calculation":
            known_names = [item["name"] for item in csv_data.get("inputs", [])] + [
                item["name"] for item in csv_data.get("tables", [])
            ]
            payload = {
                "calculations": [
                    {
                        "name": formula.get("name")
                        or f'{formula.get("source_sheet")}_{formula.get("cell")}',
                        "expression": formula["formula"],
                        "references": extract_references(
                            formula["formula"], known_names
                        ),
                    }
                    for formula in csv_data.get("formulas", [])
                ]
            }
        else:
            payload = {}
        return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)


def build_llm_client() -> LlmClient:
    use_real = env_flag("USE_REAL_LLM")
    if use_real:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY must be set when USE_REAL_LLM=true")
        model = os.getenv("LLM_MODEL")
        if not model:
            raise RuntimeError("LLM_MODEL must be set when USE_REAL_LLM=true")
        from openai import OpenAI

        return LlmClient(use_real=True, model=model, _client=OpenAI())
    return LlmClient(use_real=False, model=None)


def env_flag(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "y"}


def extract_references(expression: str, known_names: List[str]) -> List[str]:
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression or "")
    references: List[str] = []
    seen = set()
    for token in tokens:
        if token in known_names and token not in seen:
            references.append(token)
            seen.add(token)
    return references
