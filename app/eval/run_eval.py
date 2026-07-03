import asyncio
import json
from pathlib import Path

from app.eval.rubric import score
from app.orchestration.planner import RuleBasedClassifier


async def main() -> None:
    path = Path(__file__).with_name("sample_requests.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    classifier = RuleBasedClassifier()
    results = [score(await classifier.classify(row["request"]), row) for row in rows]
    passed = sum(all(item.values()) for item in results)
    print(json.dumps({"cases": len(rows), "fully_passing": passed, "results": results}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

