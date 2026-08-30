"""Authoritative Session Workflow State and Fingerprint Tracker Service for PropIQ.

Tracks explicit module execution statuses (NOT_STARTED, RUNNING, COMPLETED, FAILED, STALE)
and version fingerprints for each active analysis session.
Enforces dependency-aware cache invalidation rules.
"""

from typing import Dict, List, Optional, Any
from app.models import ModuleStatus, PrerequisiteBlockedModel

# In-memory store for session workflow state metadata
# Schema: { session_id: { "statuses": {...}, "fingerprints": {...}, "errors": {...} } }
SESSION_WORKFLOW_STATES: Dict[str, Dict[str, Any]] = {}


class SessionStateService:
    """Service managing authoritative session workflow states and input version fingerprints."""

    def _get_or_create_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get or initialize workflow state structure for session_id."""
        if session_id not in SESSION_WORKFLOW_STATES:
            SESSION_WORKFLOW_STATES[session_id] = {
                "statuses": {
                    "proposals": ModuleStatus.NOT_STARTED.value,
                    "requirements": ModuleStatus.NOT_STARTED.value,
                    "comparison": ModuleStatus.NOT_STARTED.value,
                    "risks_contradictions": ModuleStatus.NOT_STARTED.value,
                    "clarifications": ModuleStatus.NOT_STARTED.value,
                    "ranking": ModuleStatus.NOT_STARTED.value,
                    "recommendation": ModuleStatus.NOT_STARTED.value,
                },
                "fingerprints": {
                    "proposals": None,
                    "requirements": None,
                    "comparison": None,
                    "risks_contradictions": None,
                    "clarifications": None,
                    "ranking": None,
                    "recommendation": None,
                },
                "errors": {},
            }
        return SESSION_WORKFLOW_STATES[session_id]

    def set_module_status(
        self,
        session_id: str,
        module: str,
        status: ModuleStatus,
        fingerprint: Optional[str] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        """Set explicit status and fingerprint for a specific workflow module."""
        state = self._get_or_create_session_state(session_id)
        state["statuses"][module] = status.value
        if fingerprint is not None:
            state["fingerprints"][module] = fingerprint
        if error_msg:
            state["errors"][module] = error_msg
        elif module in state["errors"]:
            del state["errors"][module]

    def get_module_status(self, session_id: str, module: str) -> ModuleStatus:
        """Get current status enum of a specific module."""
        state = self._get_or_create_session_state(session_id)
        raw_val = state["statuses"].get(module, ModuleStatus.NOT_STARTED.value)
        return ModuleStatus(raw_val)

    def get_module_fingerprint(self, session_id: str, module: str) -> Optional[str]:
        """Get stored fingerprint string of a specific module."""
        state = self._get_or_create_session_state(session_id)
        return state["fingerprints"].get(module)

    def get_session_workflow_state(self, session_id: str) -> Dict[str, Any]:
        """Retrieve complete session workflow state summary."""
        state = self._get_or_create_session_state(session_id)
        return {
            "session_id": session_id,
            "statuses": state["statuses"],
            "fingerprints": state["fingerprints"],
            "errors": state["errors"],
        }

    def on_proposals_changed(self, session_id: str, proposal_fp: str) -> None:
        """Invalidate all downstream modules when proposals are uploaded or re-processed."""
        state = self._get_or_create_session_state(session_id)
        state["statuses"]["proposals"] = ModuleStatus.COMPLETED.value
        state["fingerprints"]["proposals"] = proposal_fp

        # All downstream analysis becomes invalid / NOT_STARTED
        for mod in ["comparison", "risks_contradictions", "clarifications", "ranking", "recommendation"]:
            state["statuses"][mod] = ModuleStatus.NOT_STARTED.value
            state["fingerprints"][mod] = None
            if mod in state["errors"]:
                del state["errors"][mod]

    def on_requirements_changed(self, session_id: str, reqs_fp: str) -> None:
        """Dependency-aware invalidation when procurement requirements are saved or edited."""
        state = self._get_or_create_session_state(session_id)
        state["statuses"]["requirements"] = ModuleStatus.COMPLETED.value
        state["fingerprints"]["requirements"] = reqs_fp

        # Downstream dependent modules become STALE if completed, or NOT_STARTED
        dep_modules = ["comparison", "clarifications", "ranking", "recommendation"]
        for mod in dep_modules:
            curr_st = state["statuses"].get(mod)
            if curr_st in [ModuleStatus.COMPLETED.value, ModuleStatus.STALE.value]:
                state["statuses"][mod] = ModuleStatus.STALE.value
            else:
                state["statuses"][mod] = ModuleStatus.NOT_STARTED.value

        # NOTE: risks_contradictions is proposal-based and requirement-independent.
        # It remains COMPLETED if it was completed!

    def check_ranking_prerequisites(
        self,
        session_id: str,
        current_reqs_fp: Optional[str] = None,
        current_comp_fp: Optional[str] = None,
        current_risk_fp: Optional[str] = None,
        current_clrf_fp: Optional[str] = None,
    ) -> Optional[PrerequisiteBlockedModel]:
        """Validate if all ranking prerequisites are explicitly COMPLETED and match current version fingerprints.

        Returns None if allowed, or PrerequisiteBlockedModel if blocked.
        """
        state = self._get_or_create_session_state(session_id)
        statuses = state["statuses"]
        fps = state["fingerprints"]

        prereq_map: Dict[str, ModuleStatus] = {}
        blocking: List[str] = []

        # 1. Proposals
        p_st = ModuleStatus(statuses.get("proposals", ModuleStatus.NOT_STARTED.value))
        prereq_map["proposals"] = p_st
        if p_st != ModuleStatus.COMPLETED:
            blocking.append("proposals")

        # 2. Requirements
        r_st = ModuleStatus(statuses.get("requirements", ModuleStatus.NOT_STARTED.value))
        prereq_map["requirements"] = r_st
        if r_st != ModuleStatus.COMPLETED:
            blocking.append("requirements")
        elif current_reqs_fp and fps.get("requirements") != current_reqs_fp:
            prereq_map["requirements"] = ModuleStatus.STALE
            blocking.append("requirements")

        # 3. Comparison
        c_st = ModuleStatus(statuses.get("comparison", ModuleStatus.NOT_STARTED.value))
        prereq_map["comparison"] = c_st
        if c_st != ModuleStatus.COMPLETED:
            blocking.append("comparison")
        elif current_comp_fp and fps.get("comparison") != current_comp_fp:
            prereq_map["comparison"] = ModuleStatus.STALE
            blocking.append("comparison")

        # 4. Risks & Contradictions (Atomic)
        rk_st = ModuleStatus(statuses.get("risks_contradictions", ModuleStatus.NOT_STARTED.value))
        prereq_map["risks_contradictions"] = rk_st
        if rk_st != ModuleStatus.COMPLETED:
            blocking.append("risks_contradictions")
        elif current_risk_fp and fps.get("risks_contradictions") != current_risk_fp:
            prereq_map["risks_contradictions"] = ModuleStatus.STALE
            blocking.append("risks_contradictions")

        # 5. Clarifications
        cl_st = ModuleStatus(statuses.get("clarifications", ModuleStatus.NOT_STARTED.value))
        prereq_map["clarifications"] = cl_st
        if cl_st != ModuleStatus.COMPLETED:
            blocking.append("clarifications")
        elif current_clrf_fp and fps.get("clarifications") != current_clrf_fp:
            prereq_map["clarifications"] = ModuleStatus.STALE
            blocking.append("clarifications")

        if blocking:
            first_block = blocking[0]
            st_val = prereq_map[first_block].value
            return PrerequisiteBlockedModel(
                ranking_status="BLOCKED",
                prerequisites=prereq_map,
                blocking_prerequisites=blocking,
                detail=f"Vendor Ranking is blocked because '{first_block}' is {st_val}.",
            )

        return None


def get_session_state_service() -> SessionStateService:
    """Singleton getter for SessionStateService."""
    return SessionStateService()
