import json

from planner import Planner

planner = Planner()

while True:

    text = input("> ")

    if text == "exit":
        break

    plan = planner.plan(text)

    print()

    print(json.dumps(
        plan,
        indent=4,
        ensure_ascii=False
    ))

    print()