import json
import os
from datetime import datetime
from tools.trello import create_failure_card

class Reporter:
    def __init__(self):
        pass

    def report(self, results):
        """
        Generates final structured report (JSON) + readable format,
        and triggers Trello integration if failed.
        """
        print("[REPORT] Generating final test report...")
        
        passed_count = sum(1 for r in results if r["status"] == "passed")
        failed_count = sum(1 for r in results if r["status"] == "failed")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "results": results
        }
        
        # Save JSON
        os.makedirs("output", exist_ok=True)
        report_path = f"output/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4)
            
        print(f"[REPORT] Report saved to {report_path}")
        print(f"--- SUMMARY ---")
        print(f"Total: {len(results)} | Passed: {passed_count} | Failed: {failed_count}")
        
        # For failed tests, trigger Trello
        for res in results:
            if res["status"] == "failed":
                create_failure_card(
                    test_id=res["test_case"].get("id"),
                    error_details=res.get("error"),
                    screenshot_path=res.get("screenshot")
                )
                
        return summary
