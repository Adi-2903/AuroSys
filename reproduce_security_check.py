from agents import ComplianceAgent
import datetime

def test_compliance_agent():
    agent = ComplianceAgent()
    
    print("Test 1: Normal Case")
    res = agent.check(
        diagnosis={"severity": "Medium"},
        financial={"total_estimate_inr": 5000},
        scheduling={"slot": "2023-11-01 10:00"}
    )
    print(res)
    assert res['status'] == "COMPLIANT"
    
    print("\nTest 2: High Value Transaction")
    res = agent.check(
        diagnosis={"severity": "Medium"},
        financial={"total_estimate_inr": 25000},
        scheduling={"slot": "2023-11-01 10:00"}
    )
    print(res)
    assert res['status'] == "REVIEW_REQUIRED"
    assert "UEBA: High-Value Transaction Flagged" in res['ue_alerts']

    print("\nTest 3: Suspicious Out-of-Hours Booking (Early)")
    res = agent.check(
        diagnosis={"severity": "Medium"},
        financial={"total_estimate_inr": 5000},
        scheduling={"slot": "2023-11-01 08:00"}
    )
    print(res)
    assert res['status'] == "BLOCKED"
    assert "UEBA: Suspicious Out-of-Hours Booking" in res['ue_alerts']

    print("\nTest 4: Suspicious Out-of-Hours Booking (Late)")
    res = agent.check(
        diagnosis={"severity": "Medium"},
        financial={"total_estimate_inr": 5000},
        scheduling={"slot": "2023-11-01 20:00"}
    )
    print(res)
    assert res['status'] == "BLOCKED"
    assert "UEBA: Suspicious Out-of-Hours Booking" in res['ue_alerts']
    
    print("\nTest 5: Critical Severity + High Value (Severity should trigger VIOLATION? Or UEBA flags too?)")
    # Based on code, Severity check is first, but alerts append. Status might be overridden if we are not careful or logic is sequential
    # The current logic:
    # 1. status = COMPLIANT
    # 2. if critical -> status = VIOLATION
    # 3. if high value -> status = REVIEW_REQUIRED (Overwrites VIOLATION? Let's check logic)
    # 4. if bad time -> status = BLOCKED (Overwrites previous)
    # Waiting to see behavior. The user asked to "append" alerts, but set status. 
    # Usually BLOCKED > VIOLATION > REVIEW_REQUIRED > COMPLIANT is a hierarchy, or VIOLATION is top. 
    # The user prompt said:
    # "Add Financial UEBA: ... and set status to 'REVIEW_REQUIRED'."
    # "Add Scheduling UEBA: ... and set status to 'BLOCKED'."
    # It implies strict setting. So if both happen, the last one wins in my simple linear implementation?
    # Or should checks be independent? The prompt implied sequential "Add this... Add that...". 
    # Let's verify what actually happens.
    
    res = agent.check(
        diagnosis={"severity": "Critical"},
        financial={"total_estimate_inr": 25000},
        scheduling={"slot": "2023-11-01 20:00"}
    )
    print(res)
    # With current code:
    # severity -> Status=VIOLATION
    # financial -> Status=REVIEW_REQUIRED
    # scheduling -> Status=BLOCKED
    # So BLOCKED wins. This seems secure aka "Fail Closed".
    
    print("\nTest 6: OTA Case (No Scheduling)")
    res = agent.check(
        diagnosis={"severity": "Medium"},
        financial={"total_estimate_inr": 100},
        scheduling=None
    )
    print(res)
    assert res['status'] == "COMPLIANT"

if __name__ == "__main__":
    test_compliance_agent()
