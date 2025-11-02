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
    if not base_url:
        raise ValueError("LANGFLOW_BASE_URL environment variable is not set.")
    
    url = f"{base_url.rstrip('/')}/api/v1/run/{flow_path}"

    payload: Dict[str, Any] = {
        "output_type": "text",
        "input_type": "text",
        "tweaks": tweaks,
        "session_id": str(uuid.uuid4()),
    }

    print(f"Calling LangFlow API at {url}")
    print(f"Payload: {payload}")
    print(f"Headers: {_get_headers()}")

    try:
        response = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"LangFlow Response: {result}")
        return result
    except requests.RequestException as e:
        print(f"Error calling LangFlow API: {e}")
        print(f"URL: {url}")
        print(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
        print(f"Response body: {getattr(e.response, 'text', 'N/A')}")
        raise ValueError(f"LangFlow API error: {str(e)}")


def _extract_text(response_payload: Dict[str, Any]) -> str:
    try:
        if isinstance(response_payload, dict):
            # Print full response for debugging
            print(f"Full LangFlow response payload: {response_payload}")
            
            # First try the new API format
            if "result" in response_payload:
                result = str(response_payload["result"])
                print(f"Found result in new format: {result}")
                return result
                
            # Then try the old format
            try:
                result = response_payload["outputs"][0]["outputs"][0]["results"]["text"]["data"]["text"]
                print(f"Found result in old format: {result}")
                return str(result)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Failed to extract in old format: {e}")
                
            # Try other possible formats
            if "response" in response_payload:
                return str(response_payload["response"])
            if "text" in response_payload:
                return str(response_payload["text"])
                
        return str(response_payload)
    except Exception as exc:
        print(f"Error extracting text: {exc}")
        print(f"Response payload type: {type(response_payload)}")
        print(f"Response payload: {response_payload}")
        raise ValueError(f"Could not extract text from response: {exc}. Full response: {response_payload}") from exc


def get_workout_recommendation(profile: str, question: str) -> str:
    try:
        print(f"Getting workout recommendation for:")
        print(f"Profile: {profile}")
        print(f"Question: {question}")

        response_payload = _call_flow(
            "ask-ai-v2-1",
            tweaks={
                "TextInput-TnbDG": {"input_value": profile},
                "TextInput-Pt27D": {"input_value": question},
            },
        )
        
        # Try to extract the text from the response
        try:
            result = _extract_text(response_payload)
            print(f"Successfully got workout recommendation: {result[:100]}...")  # Print first 100 chars
            return result
        except Exception as text_error:
            print(f"Error extracting text from response: {text_error}")
            print(f"Raw response payload: {response_payload}")
            raise
    except Exception as e:
        print(f"Error getting workout recommendation: {str(e)}")
        print(f"Profile provided: {profile}")
        print(f"Question asked: {question}")
        raise ValueError(f"Failed to get workout recommendation: {str(e)}")


def get_macro_plan(goal: str, profile: str) -> str:
    response_payload = _call_flow(
        "03ffb633-f1e5-42d6-84c9-e02b4cee1f41",  # Correct flow ID for macro plan
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