"""Mock Jenkins data for demo/testing."""

from datetime import datetime, timedelta
from typing import Any


def get_mock_pipelines() -> list[dict[str, Any]]:
    """Get mock pipeline list."""
    now = datetime.now()

    return [
        {
            "name": "provision-environment",
            "status": "SUCCESS",
            "last_run": (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "duration": "12m 34s",
            "build_number": 142,
        },
        {
            "name": "teardown-environment",
            "status": "RUNNING",
            "last_run": now.strftime("%Y-%m-%d %H:%M"),
            "duration": "3m 12s",
            "build_number": 89,
        },
        {
            "name": "backup-check",
            "status": "FAILED",
            "last_run": (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
            "duration": "45m 23s",
            "build_number": 234,
        },
        {
            "name": "monitor-infrastructure",
            "status": "SUCCESS",
            "last_run": (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "duration": "8m 15s",
            "build_number": 156,
        },
        {
            "name": "deploy-staging",
            "status": "SUCCESS",
            "last_run": (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "duration": "25m 47s",
            "build_number": 78,
        },
        {
            "name": "pause-environments",
            "status": "ABORTED",
            "last_run": (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
            "duration": "2m 05s",
            "build_number": 45,
        },
    ]


def get_mock_pipeline_detail(name: str, build_number: int) -> dict[str, Any]:
    """Get mock pipeline details with stages."""
    return {
        "name": name,
        "build_number": build_number,
        "status": "RUNNING",
        "duration_ms": 495000,
        "stages": [
            {
                "name": "Checkout",
                "status": "SUCCESS",
                "duration_ms": 12000,
            },
            {
                "name": "Validate Parameters",
                "status": "SUCCESS",
                "duration_ms": 5000,
            },
            {
                "name": "Deploy Infrastructure",
                "status": "IN_PROGRESS",
                "duration_ms": 465000,
            },
            {
                "name": "Run Tests",
                "status": "NOT_EXECUTED",
                "duration_ms": 0,
            },
            {
                "name": "Notify Completion",
                "status": "NOT_EXECUTED",
                "duration_ms": 0,
            },
        ],
    }


def get_mock_job_info(name: str) -> dict[str, Any]:
    """Get mock job information."""
    return {
        "name": name,
        "description": f"Jenkins pipeline for {name.replace('-', ' ')}",
        "buildable": True,
        "last_build": {
            "number": 142,
            "result": "SUCCESS",
        },
        "parameters": [
            {
                "name": "environment_name",
                "type": "string",
                "description": "Name of the environment",
                "required": True,
            },
            {
                "name": "aws_account_id",
                "type": "string",
                "description": "AWS Account ID (12 digits)",
                "required": True,
            },
            {
                "name": "region",
                "type": "choice",
                "choices": ["us-east-1", "us-west-2", "us-gov-east-1"],
                "default": "us-east-1",
                "required": False,
            },
        ],
    }


def get_mock_build_info(name: str, number: int) -> dict[str, Any]:
    """Get mock build information."""
    return {
        "name": name,
        "number": number,
        "building": True,
        "result": None,
        "duration": 495000,
        "timestamp": 1700000000000,
        "parameters": {
            "environment_name": "staging-test",
            "aws_account_id": "123456789012",
            "region": "us-east-1",
        },
    }


def get_mock_console_log(name: str, number: int) -> list[str]:
    """Get mock console log lines."""
    return [
        f"[Pipeline] Start of Pipeline {name} #{number}",
        "[Pipeline] stage (Checkout)",
        "[Pipeline] git",
        "Cloning repository...",
        "Checked out revision abc123def456",
        "[Pipeline] stage (Validate Parameters)",
        "✓ environment_name: staging-test",
        "✓ aws_account_id: 123456789012",
        "✓ region: us-east-1",
        "[Pipeline] stage (Deploy Infrastructure)",
        "Creating VPC in us-east-1...",
        "VPC created: vpc-0123456789abcdef0",
        "Creating subnets...",
        "Creating security groups...",
        "Deploying EKS cluster...",
        "⟳ Waiting for cluster to be ready (this may take 15-20 minutes)...",
    ]


def get_mock_pending_inputs(name: str, number: int) -> list[dict[str, Any]]:
    """Get mock pending input actions."""
    return [
        {
            "id": "input-1",
            "message": "Approve deployment to production?",
            "parameters": [
                {
                    "name": "approval",
                    "type": "boolean",
                    "description": "Approve this deployment",
                }
            ],
        }
    ]


def get_mock_job_history(name: str, limit: int = 10) -> list[dict[str, Any]]:
    """Get mock job history."""
    now = datetime.now()
    history = []

    results = [
        "SUCCESS",
        "SUCCESS",
        "FAILED",
        "SUCCESS",
        "ABORTED",
        "SUCCESS",
        "SUCCESS",
        "SUCCESS",
        "FAILED",
        "SUCCESS",
    ]

    for i in range(min(limit, 10)):
        build_num = 150 - i
        history.append(
            {
                "number": build_num,
                "result": results[i],
                "duration": f"{5 + i * 2}m {15 + i * 5}s",
                "timestamp": (now - timedelta(hours=i * 3)).strftime("%Y-%m-%d %H:%M"),
            }
        )

    return history


class MockJenkinsClient:
    """Mock Jenkins client for demo mode."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize mock client."""
        pass

    def list_jobs(self) -> list[dict[str, Any]]:
        """List all jobs."""
        return get_mock_pipelines()

    def get_job_info(self, name: str) -> dict[str, Any]:
        """Get job information."""
        return get_mock_job_info(name)

    async def get_build_info(self, name: str, number: int) -> dict[str, Any]:
        """Get build information."""
        return get_mock_build_info(name, number)

    async def get_workflow_info(self, name: str, number: int) -> dict[str, Any]:
        """Get workflow information with stages."""
        return get_mock_pipeline_detail(name, number)

    async def get_build_log(self, name: str, number: int) -> str:
        """Get build console log."""
        return "\n".join(get_mock_console_log(name, number))

    async def get_pending_inputs(self, name: str, number: int) -> list[dict[str, Any]]:
        """Get pending input actions."""
        return get_mock_pending_inputs(name, number)

    def trigger_job(self, name: str, parameters: dict[str, Any] | None = None) -> int:
        """Trigger a job."""
        return 143  # Mock queue item ID

    async def stop_build(self, name: str, number: int) -> None:
        """Stop a build."""
        pass

    async def abort_input(self, name: str, number: int, input_id: str) -> None:
        """Abort input (pause)."""
        pass

    async def submit_input(
        self, name: str, number: int, input_id: str, parameters: dict[str, Any] | None = None
    ) -> None:
        """Submit input (resume)."""
        pass

    async def close(self) -> None:
        """Close client."""
        pass
