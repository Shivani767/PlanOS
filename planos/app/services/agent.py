"""Agent service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from planos.app.core.exceptions import NotFoundError, TenantIsolationError
from planos.app.core.logging import get_logger
from planos.app.models import Agent, AgentRun, AgentStep, AgentToolCall

logger = get_logger(__name__)


class AgentService:
    """Service for agent operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_agent(self, agent_type: str, organization_id: str) -> Agent:
        """Get or create an agent for the organization."""
        result = await self.session.execute(
            select(Agent).where(
                Agent.organization_id == organization_id,
                Agent.agent_type == agent_type,
            )
        )
        agent = result.scalar_one_or_none()
        if not agent:
            agent = Agent(
                organization_id=organization_id,
                name=f"{agent_type.title()} Agent",
                agent_type=agent_type,
                config={},
            )
            self.session.add(agent)
            await self.session.commit()
            await self.session.refresh(agent)
        return agent

    async def execute_run(
        self,
        agent_type: str,
        input_text: str,
        organization_id: str,
        user_id: str,
    ) -> AgentRun:
        """Execute an agent run."""
        agent = await self.get_or_create_agent(agent_type, organization_id)

        run = AgentRun(
            organization_id=organization_id,
            agent_id=agent.id,
            user_id=user_id,
            status="running",
            input_text=input_text,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)

        try:
            # Create initial step
            step = AgentStep(
                run_id=run.id,
                step_number=1,
                step_type="reasoning",
                content={"input": input_text},
            )
            self.session.add(step)
            await self.session.commit()

            # For now, return a placeholder response
            # Full agent runtime will be implemented in Phase 3
            run.output_text = f"Agent '{agent_type}' processed: {input_text[:100]}..."
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

            step.content["output"] = run.output_text
            await self.session.commit()

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            logger.error("agent_run_failed", run_id=run.id, error=str(e))

        await self.session.refresh(run)
        return run

    async def get_run(self, run_id: str, organization_id: str) -> AgentRun:
        """Get an agent run by ID."""
        result = await self.session.execute(
            select(AgentRun).where(AgentRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise NotFoundError("AgentRun", run_id)
        if run.organization_id != organization_id:
            raise TenantIsolationError()
        return run
