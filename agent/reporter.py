import json
import os
import hashlib
from datetime import datetime
from tools.trello import create_failure_card


class Reporter:
    def __init__(self):
        pass

    def report(self, results, url: str = None):
        """
        Generates final structured report (JSON) for the session.
        """
        print("[REPORT] Generating final test report...")
        
        passed_count = sum(1 for r in results if r.get("status") in ("passed", "completed"))
        failed_count = sum(1 for r in results if r.get("status") == "failed")
        
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
            json.dump(summary, f, indent=4, ensure_ascii=False)
            
        print(f"[REPORT] Report saved to {report_path}")
        print(f"--- SUMMARY ---")
        print(f"Total: {len(results)} | Passed: {passed_count} | Failed: {failed_count}")

        for res in results:
            if res.get("status") == "failed":
                create_failure_card(
                    test_id=res.get("test_id", "UNKNOWN"),
                    error_details=res.get("error"),
                    screenshot_path=res.get("screenshot")
                )

        return summary