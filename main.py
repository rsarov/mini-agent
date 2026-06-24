import json

from planner import Planner
from tools import execute_tool

planner = Planner()

while True:

    text = input("> ")

    if text == "exit":
        break

    plan = planner.plan(text)
    result = execute_tool(plan)

    print()

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    ))

    print()
