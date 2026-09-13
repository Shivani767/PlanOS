"""Custom exceptions for PlanOS."""

from __future__ import annotations

from typing import Optional


class PlanOSError(Exception):
    """Base exception for PlanOS."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(PlanOSError):
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(msg, code=f"{resource.upper()}_NOT_FOUND")


class UnauthorizedError(PlanOSError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenError(PlanOSError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, code="FORBIDDEN")


class ValidationError(PlanOSError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, code="VALIDATION_ERROR")


class ConflictError(PlanOSError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, code="CONFLICT")


class OptimisticLockError(ConflictError):
    def __init__(self, expected: int, actual: int):
        super().__init__(
            f"Version conflict: expected v{expected}, found v{actual}. "
            "Resource was modified by another request."
        )


class TenantIsolationError(ForbiddenError):
    def __init__(self):
        super().__init__("Cross-tenant access denied")


class PolicyDeniedError(ForbiddenError):
    def __init__(self, reason: str, requires_approval: bool = False):
        self.requires_approval = requires_approval
        code = "APPROVAL_REQUIRED" if requires_approval else "POLICY_DENIED"
        super().__init__(reason)
        self.code = code


class IdempotencyError(PlanOSError):
    def __init__(self, message: str = "Idempotency key conflict"):
        super().__init__(message, code="IDEMPOTENCY_CONFLICT")
