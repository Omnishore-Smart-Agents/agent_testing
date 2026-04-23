import json
import os
import hashlib
from datetime import datetime
from tools.trello import create_failure_card


class Reporter:
    def __init__(self):
        pass

    def report(self, results, url: str = None):
        print("[REPORT] Generating test report...")
        passed_count = sum(1 for r in results if r["status"] == "passed")
        failed_count = sum(1 for r in results if r["status"] == "failed")

        summary = {
            "timestamp": datetime.now().isoformat(),
            "target_url": url,
            "total_tests": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "results": results
        }

        os.makedirs("output", exist_ok=True)

        if url:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            report_path = f"output/report_{url_hash}.json"
        else:
            report_path = "output/report.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4)

        latest_path = "output/report_latest.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4)

        print(f"[REPORT] Report saved to {report_path}")
        print(f"--- SUMMARY ---")
        print(f"Total: {len(results)} | Passed: {passed_count} | Failed: {failed_count}")

        for res in results:
            if res["status"] == "failed":
                screenshots = res.get("screenshots", [])
                screenshot_path = screenshots[-1]["path"] if screenshots else None
                create_failure_card(
                    test_id=res["test_case"].get("id"),
                    error_details=res.get("error"),
                    screenshot_path=screenshot_path
                )

        return summary