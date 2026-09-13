"""Approval service: propose -> approve/reject -> transactional apply (Phases 13+16)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    OptimisticLockError,
)
from planos.app.core.logging import get_logger
from planos.app.models import ApprovalRequest, ChangeSet, Plan, PlanVersion, Scenario

logger = get_logger(__name__)


class ApprovalService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def propose_from_scenario(
        self, scenario_id: str, organization_id: str, user_id: str, summary: str = ""
    ) -> tuple[ChangeSet, ApprovalRequest]:
        row = await self.session.execute(
            select(Scenario).where(
                Scenario.id == scenario_id, Scenario.organization_id == organization_id
            )
        )
        scenario = row.scalar_one_or_none()
        if scenario is None:
            raise NotFoundError("Scenario", scenario_id)
        plan_row = await self.session.execute(
            select(Plan).where(
                Plan.id == scenario.base_plan_id, Plan.organization_id == organization_id
            )
        )
        plan = plan_row.scalar_one_or_none()
        if plan is None:
            raise NotFoundError("Plan", scenario.base_plan_id)
        cs = ChangeSet(
            organization_id=organization_id,
            scenario_id=scenario.id,
            plan_id=plan.id,
            expected_plan_version=plan.current_version,
            changes=dict(scenario.changes or {}),
            summary=summary or f"Apply scenario '{scenario.name}' to plan '{plan.name}'",
            status="pending_approval",
            created_by=user_id,
        )
        self.session.add(cs)
        await self.session.flush()
        approval = ApprovalRequest(
            organization_id=organization_id,
            requested_by=user_id,
            action_type="apply_change_set",
            resource_type="change_set",
            resource_id=cs.id,
            details={
                "change_set_id": cs.id,
                "plan_id": plan.id,
                "expected_version": plan.current_version,
            },
            status="pending",
        )
        self.session.add(approval)
        await self.session.commit()
        await self.session.refresh(cs)
        await self.session.refresh(approval)
        logger.info("change_proposed", change_set_id=cs.id, approval_id=approval.id)
        return cs, approval

    async def _get_approval(self, approval_id: str, organization_id: str) -> ApprovalRequest:
        row = await self.session.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
        )
        approval = row.scalar_one_or_none()
        if approval is None:
            raise NotFoundError("Approval", approval_id)
        if approval.organization_id != organization_id:
            raise NotFoundError("Approval", approval_id)
        return approval

    async def decide(
        self,
        approval_id: str,
        organization_id: str,
        user_id: str,
        approve: bool,
        reason: str | None = None,
    ) -> ApprovalRequest:
        approval = await self._get_approval(approval_id, organization_id)
        if approval.status != "pending":
            raise ConflictError(f"Approval is already {approval.status}")
        if approve:
            await self._apply(approval, organization_id, user_id)
            approval.status = "approved"
        else:
            approval.status = "rejected"
            if approval.resource_type == "change_set" and approval.resource_id:
                cs = await self.session.get(ChangeSet, approval.resource_id)
                if cs is not None:
                    cs.status = "rejected"
        approval.approved_by = user_id
        approval.decision_reason = reason
        approval.decided_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(approval)
        return approval

    async def _apply(
        self, approval: ApprovalRequest, organization_id: str, user_id: str
    ) -> ChangeSet:
        """Atomic: re-validate version -> apply -> snapshot -> audit -> close."""
        from planos.app.models import AuditLog

        if approval.resource_type != "change_set" or not approval.resource_id:
            raise ForbiddenError("Only change_set approvals can be applied")
        cs = await self.session.get(ChangeSet, approval.resource_id)
        if cs is None or cs.organization_id != organization_id:
            raise NotFoundError("ChangeSet", cs.id if cs else approval.resource_id)
        plan = await self.session.get(Plan, cs.plan_id)
        if plan is None or plan.organization_id != organization_id:
            raise NotFoundError("Plan", cs.plan_id)
        if plan.current_version != cs.expected_plan_version:
            raise OptimisticLockError(cs.expected_plan_version, plan.current_version)
        try:
            new_version = plan.current_version + 1
            plan.current_version = new_version
            self.session.add(
                PlanVersion(
                    plan_id=plan.id,
                    version=new_version,
                    data={"applied_change_set": cs.id, "changes": cs.changes},
                    created_by=user_id,
                )
            )
            cs.status = "applied"
            self.session.add(
                AuditLog(
                    organization_id=organization_id,
                    user_id=user_id,
                    action="change_set.applied",
                    resource_type="plan",
                    resource_id=plan.id,
                    new_value={"change_set_id": cs.id, "version": new_version},
                )
            )
            await self.session.flush()
        except Exception:
            await self.session.rollback()
            raise
        logger.info("change_applied", change_set_id=cs.id, version=new_version)
        return cs
