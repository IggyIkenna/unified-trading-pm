"""Epic/Task/Subtask models for service epics."""

from __future__ import annotations

from typing import cast

ServiceDict = dict[str, object]

__all__ = ["ServiceDict", "Subtask", "Task", "Epic"]

# Epic/Task/Subtask Structure
# ============================================================================


class Subtask:
    """Atomic work unit."""

    def __init__(
        self,
        title: str,
        description: str,
        complexity: str,  # LOW, MEDIUM, HIGH
        priority: str,  # P0-critical, P1-high, P2-medium, P3-low
        hours: float,
        checklist_item_id: str | None = None,  # e.g., DATA-04
        codex_refs: list[str] | None = None,
    ) -> None:
        self.title = title
        self.description = description
        self.complexity = complexity
        self.priority = priority
        self.hours = hours
        self.checklist_item_id = checklist_item_id
        self.codex_refs = codex_refs or []

    def _format_subtask_header(self, parent_task_number: int, epic_number: int) -> list[str]:
        """Format header section of subtask body."""
        return [
            f"**Parent Task:** #{parent_task_number}",
            f"**Parent Epic:** #{epic_number}",
            f"**Complexity:** {self.complexity}",
            f"**Priority:** {self.priority}",
            f"**Estimated Hours:** {self.hours}",
            "",
            "## Description",
            self.description,
        ]

    def _format_subtask_checklist_and_codex(self) -> list[str]:
        """Format checklist item and codex refs sections."""
        parts: list[str] = []
        if self.checklist_item_id:
            parts.extend(["", f"**Checklist Item:** {self.checklist_item_id}"])
        if self.codex_refs:
            parts.extend(["", "## Codex References"])
            for ref in self.codex_refs:
                parts.append(f"- `{ref}`")
        return parts

    def _format_subtask_success_criteria(self) -> list[str]:
        """Format success criteria section."""
        parts: list[str] = [
            "",
            "## Success Criteria",
            "- [ ] Implementation complete",
            "- [ ] Tests pass (>80% coverage)",
            "- [ ] Quality gates pass",
            "- [ ] PR merged",
        ]
        if self.checklist_item_id:
            parts.append(f"- [ ] Checklist item {self.checklist_item_id} updated to 'done'")
        parts.extend(["", f"<!-- subtask-ref: {self.checklist_item_id or self.title} -->"])
        return parts

    def to_github_issue_body(self, parent_task_number: int, epic_number: int) -> str:
        """Format subtask as GitHub issue body."""
        body_parts: list[str] = []
        body_parts.extend(self._format_subtask_header(parent_task_number, epic_number))
        body_parts.extend(self._format_subtask_checklist_and_codex())
        body_parts.extend(self._format_subtask_success_criteria())
        return "\n".join(body_parts)


class Task:
    """Logical work grouping."""

    def __init__(
        self,
        title: str,
        description: str,
        priority: str,
        mode: str | None = None,  # batch, live, or None
        subtasks: list[Subtask] | None = None,
    ) -> None:
        self.title = title
        self.description = description
        self.priority = priority
        self.mode = mode
        self.subtasks = subtasks or []

    def total_hours(self) -> float:
        """Calculate total hours for all subtasks."""
        return sum(s.hours for s in self.subtasks)

    def to_github_issue_body(self, epic_number: int) -> str:
        """Format task as GitHub issue body."""
        body_parts: list[str] = [
            f"**Parent Epic:** #{epic_number}",
            f"**Priority:** {self.priority}",
        ]

        if self.mode:
            body_parts.append(f"**Mode:** {self.mode}")

        body_parts.extend(
            [
                f"**Total Hours:** {self.total_hours():.1f}h",
                "",
                "## Description",
                self.description,
                "",
                "## Subtasks",
                "",
            ]
        )

        for i, subtask in enumerate(self.subtasks, 1):
            body_parts.append(f"{i}. **{subtask.title}** ({subtask.complexity}, {subtask.hours}h)")

        body_parts.extend(
            [
                "",
                f"<!-- task-ref: {self.title} -->",
            ]
        )

        return "\n".join(body_parts)


class Epic:
    """Service-level epic."""

    def __init__(
        self,
        service: ServiceDict,
        tasks: list[Task] | None = None,
        milestone: str | None = None,
    ) -> None:
        self.service = service
        self.service_name = str(service.get("service", ""))
        self.tasks = tasks or []
        self.milestone = milestone or str(service.get("milestone", "Backlog"))

    def total_hours(self) -> float:
        """Calculate total hours for all tasks."""
        return sum(t.total_hours() for t in self.tasks)

    def to_github_issue_body(self) -> str:
        """Format epic as GitHub issue body."""
        service_type = str(self.service.get("type", "unknown"))
        layer = str(self.service.get("layer", "N/A"))
        raw_venues = self.service.get("venues") or []
        venues_list: list[str] = cast(list[str], raw_venues) if isinstance(raw_venues, list) else []
        venues = ", ".join(venues_list)
        raw_assets = self.service.get("asset_classes") or []
        assets_list: list[str] = cast(list[str], raw_assets) if isinstance(raw_assets, list) else []
        asset_classes = ", ".join(assets_list)

        body_parts: list[str] = [
            f"**Service:** `{self.service_name}`",
            f"**Type:** {service_type}",
            f"**Layer:** {layer}",
            f"**Milestone:** {self.milestone}",
            f"**Total Hours:** {self.total_hours():.1f}h",
            "",
        ]

        if venues:
            body_parts.append(f"**Venues:** {venues}")
        if asset_classes:
            body_parts.append(f"**Asset Classes:** {asset_classes}")

        body_parts.extend(
            [
                "",
                "## Tasks",
                "",
            ]
        )

        for i, task in enumerate(self.tasks, 1):
            mode_label = f" ({task.mode})" if task.mode else ""
            body_parts.append(f"{i}. **{task.title}**{mode_label} - {task.total_hours():.1f}h")

        body_parts.extend(
            [
                "",
                f"<!-- epic-ref: {self.service_name} -->",
            ]
        )

        return "\n".join(body_parts)


# ============================================================================
