import json

from llm import ask_llm
from prompts import SYSTEM_PROMPT


class Planner:

    def plan(self, request: str):
        response = ask_llm(
            SYSTEM_PROMPT,
            request
        )

        return json.loads(response)
