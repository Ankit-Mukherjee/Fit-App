import os
import uuid
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()


def _get_headers() -> Dict[str, str]:
    api_key = os.environ.get("LANGFLOW_API_KEY")
    if not api_key:
        raise ValueError("LANGFLOW_API_KEY environment variable is not set.")
    return {"x-api-key": api_key}


def _call_flow(flow_path: str, tweaks: Dict[str, Any]) -> Dict[str, Any]:
    base_url = os.environ.get("LANGFLOW_BASE_URL", "http://localhost:7860")
    url = f"{base_url.rstrip('/')}/api/v1/run/{flow_path}"

    payload: Dict[str, Any] = {
        "output_type": "text",
        "input_type": "text",
        "tweaks": tweaks,
        "session_id": str(uuid.uuid4()),
    }

    response = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def _extract_text(response_payload: Dict[str, Any]) -> str:
    try:
        return response_payload["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected response structure: {exc}") from exc


def get_workout_recommendation(profile: str, question: str) -> str:
    response_payload = _call_flow(
        "ask-ai-v2-1",
        tweaks={
            "TextInput-TnbDG": {"input_value": profile},
            "TextInput-Pt27D": {"input_value": question},
        },
    )
    return _extract_text(response_payload)


def get_macro_plan(goal: str, profile: str) -> str:
    response_payload = _call_flow(
        "03ffb633-f1e5-42d6-84c9-e02b4cee1f41",
        tweaks={
            "TextInput-heTA9": {"input_value": goal},
            "TextInput-5TY21": {"input_value": profile},
        },
    )
    return _extract_text(response_payload)


def main() -> None:
    load_dotenv()

    try:
        workout = get_workout_recommendation(
            profile="male, 75kg, 175cm, very active, goals: build muscle",
            question="What is a good bicep workout?",
        )
        print("Workout Recommendation:\n", workout)

        macros = get_macro_plan(goal="goals", profile="male, 75kg, 175cm, very active, goals: build muscle")
        print("\nMacro Plan:\n", macros)

    except ValueError as err:
        print(f"Error: {err}")
    except requests.HTTPError as err:
        print(f"API error: {err}")
    except requests.RequestException as err:
        print(f"Network error: {err}")


if __name__ == "__main__":
    main()