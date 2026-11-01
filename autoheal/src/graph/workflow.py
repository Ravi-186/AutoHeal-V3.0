from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from src.correlation.engine import Incident
import datetime

class WorkflowState(TypedDict, total=False):
    device_id: str
    current_time: datetime.datetime
    incident: Optional[Incident]
    action_taken: Optional[str]
    is_verified: bool
    retry_count: int
    audit_trail: list

class AutoHealGraph:
    """Manages the LangGraph Detect -> Respond -> Verify loop with enterprise audit tracing."""
    def __init__(self, detect_agent, response_agent, verify_agent, max_retries=2):
        self.detect_agent = detect_agent
        self.response_agent = response_agent
        self.verify_agent = verify_agent
        self.max_retries = max_retries
        self.graph = self._build_graph()
        
    def _build_graph(self):
        workflow = StateGraph(WorkflowState)
        
        # Define Nodes
        workflow.add_node("detect", self.node_detect)
        workflow.add_node("respond", self.node_respond)
        workflow.add_node("verify", self.node_verify)
        
        # Define Edges
        workflow.set_entry_point("detect")
        
        # Conditional Edge after detect
        workflow.add_conditional_edges(
            "detect",
            self.should_respond,
            {
                "yes": "respond",
                "no": END
            }
        )
        
        # Unconditional Edge from respond to verify
        workflow.add_edge("respond", "verify")
        
        # Conditional Edge after verify
        workflow.add_conditional_edges(
            "verify",
            self.should_retry,
            {
                "retry": "respond",
                "success": END,
                "max_retries_reached": END
            }
        )
        
        return workflow.compile()
        
    # --- Node Functions ---
    def node_detect(self, state: WorkflowState):
        trail = list(state.get("audit_trail", []))
        ts = state['current_time'].strftime('%H:%M:%S')
        print(f"\n[LangGraph] NODE: Detect - Checking {state['device_id']}...")
        incident = self.detect_agent.run(state['device_id'], state['current_time'], window_minutes=1)
        
        if incident:
            trail.append({
                "node": "Detection Agent",
                "timestamp": ts,
                "status": "THREAT_CONFIRMED",
                "details": f"Anomaly identified via ML Ensemble. MITRE: {incident.mitre_tactic}. {incident.reason}",
                "severity": incident.severity
            })
        else:
            trail.append({
                "node": "Detection Agent",
                "timestamp": ts,
                "status": "NORMAL",
                "details": "Telemetry within nominal baseline. No IOCs flagged.",
                "severity": "LOW"
            })
            
        return {"incident": incident, "audit_trail": trail}
        
    def node_respond(self, state: WorkflowState):
        trail = list(state.get("audit_trail", []))
        ts = state['current_time'].strftime('%H:%M:%S')
        attempt = state.get('retry_count', 0) + 1
        print(f"\n[LangGraph] NODE: Respond - Handling incident on {state['device_id']} (Attempt {attempt})...")
        action = self.response_agent.run(state['incident'])
        
        trail.append({
            "node": "Response Agent",
            "timestamp": ts,
            "status": "ACTION_ENFORCED",
            "details": f"SOAR containment executed: {action} (Policy Level {attempt}). Device quarantined from critical zones.",
            "action": action,
            "attempt": attempt
        })
        return {"action_taken": action, "retry_count": attempt, "audit_trail": trail}
        
    def node_verify(self, state: WorkflowState):
        trail = list(state.get("audit_trail", []))
        # Advance time by 5 minutes to simulate waiting for new logs to gather
        new_time = state['current_time'] + datetime.timedelta(minutes=5)
        ts = new_time.strftime('%H:%M:%S')
        print(f"\n[LangGraph] NODE: Verify - Checking if {state['action_taken']} stopped the attack...")
        
        is_fixed = self.verify_agent.run(state['device_id'], state['action_taken'], new_time, window_minutes=1)
        
        trail.append({
            "node": "Verification Agent",
            "timestamp": ts,
            "status": "VERIFIED_NEUTRALIZED" if is_fixed else "VERIFICATION_FAILED_ESCALATING",
            "details": f"Post-mitigation check for '{state['action_taken']}': {'Attack halted successfully. Threat eliminated.' if is_fixed else 'Attack telemetry still detected! Triggering automated escalation policy.'}",
            "is_verified": is_fixed
        })
        return {"is_verified": is_fixed, "current_time": new_time, "audit_trail": trail}
        
    # --- Edge Logic Functions ---
    def should_respond(self, state: WorkflowState):
        if state.get("incident"):
            return "yes"
        return "no"
        
    def should_retry(self, state: WorkflowState):
        if state.get("is_verified", False):
            print("[LangGraph] EDGE: Verification successful. Ending workflow.")
            return "success"
        elif state.get("retry_count", 0) >= self.max_retries:
            print(f"[LangGraph] EDGE: Verification failed. Max retries ({self.max_retries}) reached. Ending workflow.")
            return "max_retries_reached"
        else:
            print("[LangGraph] EDGE: Verification failed. Retrying response (Escalation).")
            return "retry"

