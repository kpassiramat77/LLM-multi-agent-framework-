import argparse
import os
import sys
from datetime import datetime, timezone

from prompt_lab.assembler import assemble_model
from prompt_lab.csv_artifacts import convert_workbook_to_csvs
from prompt_lab.csv_loader import load_csv_artifacts, load_csv_texts
from prompt_lab.llm_client import build_llm_client
from prompt_lab.prompts import build_agent_prompts
from prompt_lab.sample_workbook import ensure_sample_workbook
from prompt_lab.scorecard import build_scorecard, format_scorecard
from prompt_lab.utils import ensure_dir, write_json_file
from prompt_lab.validation import validate_fragment_output, validate_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generic prompt lab for Excel to CSV to model JSON"
    )
    parser.add_argument(
        "--workbook",
        default=os.path.join("data", "sample_workbook.xlsx"),
        help="Path to the workbook file",
    )
    parser.add_argument(
        "--output-dir",
        default="out",
        help="Directory for run outputs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    workbook_path = ensure_sample_workbook(args.workbook)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = os.path.join(args.output_dir, "artifacts", run_id)
    csv_manifest = convert_workbook_to_csvs(workbook_path, artifacts_dir)
    csv_texts = load_csv_texts(csv_manifest)
    csv_data = load_csv_artifacts(csv_manifest)

    prompts = build_agent_prompts(csv_texts)
    llm_client = build_llm_client()

    agent_outputs = {}
    for agent_id, prompt in prompts.items():
        raw_output = llm_client.generate(
            agent_id=agent_id,
            system_prompt=prompt["system"],
            user_prompt=prompt["user"],
            csv_data=csv_data,
        )
        validation = validate_fragment_output(
            raw_output, catalog=csv_data, agent_id=agent_id
        )
        agent_outputs[agent_id] = {
            "prompt": prompt,
            "raw_output": raw_output,
            "parsed": validation["parsed"],
            "validation": validation["report"],
        }

    fragments = [
        payload["parsed"]
        for payload in agent_outputs.values()
        if payload["parsed"]
        and payload["validation"].get("json_only")
        and payload["validation"].get("schema_valid")
        and payload["validation"].get("references_valid")
    ]
    assembled_model = assemble_model(fragments)
    model_validation = validate_model(assembled_model, catalog=csv_data)

    scorecard = build_scorecard(
        catalog=csv_data,
        agent_outputs=agent_outputs,
        model_validation=model_validation,
    )

    ensure_dir(args.output_dir)
    output_path = os.path.join(args.output_dir, f"run_{run_id}.json")

    write_json_file(
        output_path,
        {
            "metadata": {
                "run_id": run_id,
                "workbook_path": workbook_path,
                "artifacts_dir": artifacts_dir,
                "use_real_llm": llm_client.use_real,
                "llm_model": llm_client.model,
            },
            "csv_manifest": csv_manifest,
            "csv_texts": csv_texts,
            "csv_data": csv_data,
            "agents": agent_outputs,
            "assembled_model": assembled_model,
            "validation": {
                "agents": {
                    agent_id: payload["validation"]
                    for agent_id, payload in agent_outputs.items()
                },
                "model": model_validation,
            },
        },
    )

    print(format_scorecard(scorecard, output_path))

    if not scorecard["all_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
