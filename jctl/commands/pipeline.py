"""Pipeline management commands."""

from __future__ import annotations

import asyncio
import sys

import click
from rich.console import Console

from jctl.constants import (
    EXIT_JENKINS_API_ERROR,
    EXIT_USER_CANCELLED,
)
from jctl.utils.completion import complete_job_name
from jctl.utils.jenkins_client_factory import get_jenkins_client
from jctl.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def pipeline() -> None:
    """Manage Jenkins pipelines."""
    pass


@pipeline.command("list")
@click.option("--filter", "-f", help="Filter pipelines by pattern")
@click.option("--folder", help="Filter by folder (e.g., 'deploy' or 'deploy/staging')")
@click.option(
    "--status",
    type=click.Choice(["SUCCESS", "FAILED", "FAILURE", "RUNNING", "ABORTED"]),
    help="Filter by last build status. FAILED is accepted as an alias for FAILURE.",
)
@click.option("--limit", "-n", type=int, default=50, help="Number of pipelines to show")
@click.pass_context
def list_pipelines(
    ctx: click.Context, filter: str | None, folder: str | None, status: str | None, limit: int
) -> None:
    """List available pipelines."""
    from jctl.utils.output import OutputFormatter, format_duration

    output_format = ctx.obj.get("output", "table")
    formatter = OutputFormatter(console)

    # Jenkins reports a build's `result` as FAILURE; the original
    # `--status FAILED` choice never matched anything because the
    # comparison was literal. Accept either name from the user.
    if status == "FAILED":
        status = "FAILURE"

    # Get authenticated client
    client = get_jenkins_client(ctx)

    # Fetch jobs from Jenkins
    async def fetch_jobs() -> list[dict]:
        try:
            with console.status("[cyan]Fetching pipelines from Jenkins...[/cyan]"):
                jobs = await client.get_jobs(folder=folder)
                return jobs
        except Exception as e:
            console.print(f"[red]Error fetching pipelines:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    jobs = asyncio.run(fetch_jobs())

    # Convert Jenkins jobs to pipeline format. We attach `_ts` (the
    # lastBuild epoch ms) on each row solely as a sort key — stripped
    # before rendering so it doesn't show up in tables/JSON.
    import datetime

    pipelines = []
    for job in jobs:
        job_full_name = job.get("fullName", job["name"])

        if filter and filter.lower() not in job_full_name.lower():
            continue

        last_build = job.get("lastBuild")
        if last_build:
            build_number = last_build.get("number", 0)
            result = last_build.get("result", "RUNNING")
            job_status = "RUNNING" if result is None else result

            if status and job_status != status:
                continue

            duration = last_build.get("duration", 0)
            duration_str = format_duration(duration) if duration > 0 else "Running"

            timestamp = last_build.get("timestamp", 0)
            last_run = (
                datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M")
                if timestamp
                else "Never"
            )

            pipelines.append(
                {
                    "name": job_full_name,
                    "status": job_status,
                    "last_run": last_run,
                    "duration": duration_str,
                    "build_number": build_number,
                    "_ts": int(timestamp or 0),
                }
            )
        else:
            # No builds yet — only show when not filtering by status.
            if not status:
                pipelines.append(
                    {
                        "name": job_full_name,
                        "status": "NO_BUILDS",
                        "last_run": "Never",
                        "duration": "-",
                        "build_number": 0,
                        "_ts": 0,
                    }
                )

    # Sort: most recently built first; NO_BUILDS rows (ts==0) fall to the
    # bottom. Tie-break alphabetically so the order is stable across runs.
    pipelines.sort(key=lambda p: (-p["_ts"], p["name"]))

    # Apply limit after sorting so the user gets the freshest N rows.
    pipelines = pipelines[:limit]

    # Strip the internal sort key from each row before rendering.
    for p in pipelines:
        p.pop("_ts", None)

    if output_format == "table":
        console.print(f"[cyan]Found {len(pipelines)} pipeline(s)[/cyan]\n")
        if pipelines:
            formatter.format(pipelines, output_format)
        else:
            console.print("[yellow]No pipelines found matching criteria[/yellow]")
    else:
        # json/yaml/plain: stdout stays machine-readable; the count goes to
        # stderr so it doesn't break a downstream parser.
        from rich.console import Console

        Console(stderr=True).print(f"[cyan]Found {len(pipelines)} pipeline(s)[/cyan]")
        formatter.format(pipelines, output_format)


@pipeline.command()
@click.argument("job_name", shell_complete=complete_job_name)
@click.argument("build_number", type=int, required=False)
@click.pass_context
def describe(ctx: click.Context, job_name: str, build_number: int | None) -> None:
    """Show detailed pipeline status with stage information.

    BUILD_NUMBER is optional — if omitted, the latest build is auto-resolved
    via `lastBuild`.
    """
    from rich.table import Table

    from jctl.utils.output import OutputFormatter, format_duration

    output_format = ctx.obj.get("output", "table")
    client = get_jenkins_client(ctx)

    async def run() -> tuple[int, dict, dict | None]:
        try:
            resolved_build = build_number
            if resolved_build is None:
                with console.status(f"[cyan]Getting latest build for {job_name}...[/cyan]"):
                    jobs = await client.get_jobs()
                    job = next((j for j in jobs if j.get("fullName") == job_name), None)
                    if not job:
                        console.print(f"[red]Error:[/red] Pipeline '{job_name}' not found")
                        sys.exit(EXIT_JENKINS_API_ERROR)
                    last_build = job.get("lastBuild")
                    latest = last_build.get("number") if last_build else None
                    if not latest:
                        console.print(f"[red]Error:[/red] No builds found for '{job_name}'")
                        sys.exit(EXIT_JENKINS_API_ERROR)
                    resolved_build = int(latest)
                    console.print(f"[dim]Using latest build #{resolved_build}[/dim]\n")

            with console.status(
                f"[cyan]Fetching build info for {job_name} #{resolved_build}...[/cyan]"
            ):
                build_info = await client.get_build_info(job_name, resolved_build)
                try:
                    workflow_info: dict | None = await client.get_workflow_info(
                        job_name, resolved_build
                    )
                except Exception as e:
                    logger.debug(
                        f"Workflow API not available for {job_name} #{resolved_build}: {e}"
                    )
                    workflow_info = None
            return resolved_build, build_info, workflow_info
        except SystemExit:
            raise
        except Exception as e:
            console.print(f"[red]Error fetching build info:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    build_number, build_info, workflow_info = asyncio.run(run())

    # Machine-readable formats: emit structured data and return.
    if output_format in ("json", "yaml", "plain"):
        payload: dict = {
            "job": job_name,
            "build_number": build_number,
            "result": build_info.get("result"),
            "duration_ms": build_info.get("duration", 0),
            "timestamp": build_info.get("timestamp"),
            "url": build_info.get("url"),
        }
        if workflow_info and "stages" in workflow_info:
            payload["stages"] = [
                {
                    "name": s.get("name"),
                    "status": s.get("status"),
                    "duration_ms": s.get("durationMillis", 0),
                }
                for s in workflow_info["stages"]
            ]
        OutputFormatter(console).format(payload, output_format)
        return

    console.print(f"\n[bold cyan]{job_name}[/bold cyan] [dim]#{build_number}[/dim]\n")

    # Map Jenkins status
    result = build_info.get("result")
    if result is None:
        status_display = "[yellow]⟳ RUNNING[/yellow]"
    elif result == "SUCCESS":
        status_display = "[green]✓ SUCCESS[/green]"
    elif result == "FAILURE":
        status_display = "[red]✗ FAILED[/red]"
    elif result == "ABORTED":
        status_display = "[yellow]⊗ ABORTED[/yellow]"
    else:
        status_display = f"[dim]{result}[/dim]"

    # Show stages if available
    if workflow_info and "stages" in workflow_info:
        table = Table(show_header=True, title="Pipeline Stages")
        table.add_column("Stage", style="cyan", no_wrap=True)
        # `min_width=14` keeps "✓ SUCCESS" / "⊗ ABORTED" on one line — Rich
        # auto-sized to the 6-char header before, wrapping the colored
        # body to "SUCCE…" on a continuation row.
        table.add_column("Status", justify="center", min_width=14, no_wrap=True)
        table.add_column("Duration", justify="right", no_wrap=True)

        status_styles = {
            "SUCCESS": "[green]✓ SUCCESS[/green]",
            "FAILED": "[red]✗ FAILED[/red]",
            "IN_PROGRESS": "[yellow]⟳ RUNNING[/yellow]",
            "NOT_EXECUTED": "[dim]⋯ PENDING[/dim]",
            "PAUSED_PENDING_INPUT": "[blue]⏸ PAUSED[/blue]",
            "ABORTED": "[yellow]⊗ ABORTED[/yellow]",
        }

        for stage in workflow_info["stages"]:
            stage_status = stage.get("status", "UNKNOWN")
            status_display_stage = status_styles.get(stage_status, f"[dim]{stage_status}[/dim]")
            duration_ms = stage.get("durationMillis", 0)
            duration = format_duration(duration_ms) if duration_ms > 0 else "-"

            table.add_row(stage["name"], status_display_stage, duration)

        console.print(table)
        console.print()

    # Overall status
    console.print(f"[bold]Overall Status:[/bold] {status_display}")

    # Duration
    duration_ms = build_info.get("duration", 0)
    if duration_ms > 0:
        console.print(f"[bold]Total Duration:[/bold] {format_duration(duration_ms)}")
    else:
        console.print("[bold]Total Duration:[/bold] Running")

    # Additional info
    console.print(f"[bold]Result:[/bold] {result or 'In Progress'}")

    # Timestamp
    timestamp = build_info.get("timestamp", 0)
    if timestamp:
        import datetime

        started_at = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"[bold]Started At:[/bold] {started_at}")

    console.print()


@pipeline.command()
@click.argument("job_name", shell_complete=complete_job_name)
@click.argument("build_number", type=int, required=False)
@click.option("--follow", "-f", is_flag=True, help="Stream logs in real-time")
@click.pass_context
def logs(ctx: click.Context, job_name: str, build_number: int | None, follow: bool) -> None:
    """View or stream pipeline logs.

    Examples:
        jctl pipeline logs deploy/release-pipeline 123
        jctl pipeline logs deploy/release-pipeline --follow
    """
    # Get authenticated client
    client = get_jenkins_client(ctx)

    async def resolve_build() -> int:
        try:
            if build_number is not None:
                return build_number
            with console.status(f"[cyan]Getting latest build for {job_name}...[/cyan]"):
                jobs = await client.get_jobs()
                job = next((j for j in jobs if j.get("fullName") == job_name), None)
                if not job:
                    console.print(f"[red]Error:[/red] Pipeline '{job_name}' not found")
                    sys.exit(EXIT_JENKINS_API_ERROR)
                last_build = job.get("lastBuild")
                if not last_build:
                    console.print(f"[red]Error:[/red] No builds found for '{job_name}'")
                    sys.exit(EXIT_JENKINS_API_ERROR)
                latest = last_build.get("number")
                if not latest:
                    console.print("[red]Error:[/red] Could not get latest build number")
                    sys.exit(EXIT_JENKINS_API_ERROR)
                console.print(f"[dim]Using latest build #{latest}[/dim]\n")
                return int(latest)
        except SystemExit:
            raise
        except Exception as e:
            console.print(f"[red]Error getting build info:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    async def stream_logs(build_num: int) -> None:
        """Stream logs in real-time."""
        console.print(f"[cyan]Streaming logs for:[/cyan] {job_name} #{build_num}\n")
        console.print("[dim]Press Ctrl+C to stop streaming[/dim]\n")

        def print_line(line: str) -> None:
            console.print(line, highlight=False)

        try:
            await client.stream_build_log(job_name, build_num, print_line)
            console.print("\n[green]✓[/green] Pipeline completed")
        except KeyboardInterrupt:
            console.print("\n[yellow]Streaming stopped by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error streaming logs:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    async def fetch_logs(build_num: int) -> None:
        """Fetch complete logs."""
        try:
            with console.status(f"[cyan]Fetching logs for {job_name} #{build_num}...[/cyan]"):
                log_text = await client.get_build_log(job_name, build_num)

            output_format = ctx.obj.get("output", "table")
            if output_format in ("json", "yaml"):
                from jctl.utils.output import OutputFormatter

                OutputFormatter(console).format(
                    {"job": job_name, "build_number": build_num, "log": log_text},
                    output_format,
                )
                return
            if output_format == "plain":
                # plain == raw log text, no header decoration
                print(log_text, end="")
                return

            console.print(f"[cyan]Logs for:[/cyan] {job_name} #{build_num}\n")
            console.print(log_text, highlight=False)

        except Exception as e:
            console.print(f"[red]Error fetching logs:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    # Single asyncio.run() — splitting "resolve build" and "fetch log" across
    # two asyncio.run() calls closes the loop the httpx.AsyncClient was bound
    # to, so the second call dies with "Event loop is closed".
    async def main() -> None:
        build_num = await resolve_build()
        if follow:
            await stream_logs(build_num)
        else:
            await fetch_logs(build_num)

    asyncio.run(main())


@pipeline.command()
@click.argument("job_name", shell_complete=complete_job_name)
@click.option("--param", "-p", multiple=True, help="Pipeline parameters (key=value)")
@click.option("--wait", is_flag=True, help="Wait for pipeline completion")
@click.option("--notify", is_flag=True, help="Send notification on completion")
@click.pass_context
def run(
    ctx: click.Context, job_name: str, param: tuple[str, ...], wait: bool, notify: bool
) -> None:
    """Execute a pipeline with parameters.

    Examples:
        jctl pipeline run deploy/release-pipeline -p environment=dev -p version=1.2.3
        jctl pipeline run deploy/release-pipeline -p environment=staging --wait
    """
    params = dict(p.split("=", 1) for p in param) if param else {}

    console.print(f"[cyan]Running pipeline:[/cyan] {job_name}")

    if params:
        console.print("[cyan]Parameters:[/cyan]")
        for key, value in params.items():
            console.print(f"  {key} = {value}")

    # Get authenticated client
    client = get_jenkins_client(ctx)

    async def run_pipeline() -> None:
        try:
            with console.status("[cyan]Triggering pipeline...[/cyan]"):
                queue_item_id = client.trigger_job(job_name, params if params else None)

            console.print("\n[green]✓[/green] Pipeline triggered successfully")
            console.print(f"[dim]Queue item ID: {queue_item_id}[/dim]")

            if wait or notify:
                console.print("\n[cyan]Waiting for pipeline to start...[/cyan]")

                # Poll queue item to get build number
                build_number = None

                max_wait = 60  # Wait up to 60 seconds for job to start

                for _ in range(max_wait):
                    try:
                        queue_info = await client.get_queue_item(queue_item_id)

                        # Check if job has started
                        if "executable" in queue_info and queue_info["executable"]:
                            build_number = queue_info["executable"].get("number")
                            if build_number:
                                console.print(
                                    f"[green]✓[/green] Pipeline started - Build #{build_number}"
                                )
                                console.print(f"[dim]Job: {job_name} #{build_number}[/dim]\n")
                                break

                        # Check if still in queue
                        if queue_info.get("blocked"):
                            console.print("[yellow]Pipeline is blocked in queue...[/yellow]")
                        elif queue_info.get("stuck"):
                            console.print("[yellow]Pipeline is stuck in queue...[/yellow]")
                        else:
                            console.print("[dim]Pipeline is queued...[/dim]")

                    except Exception as e:
                        logger.debug(f"Could not retrieve queue info: {e}")
                        # Continue without queue details

                    await asyncio.sleep(1)

                if build_number:
                    if wait:
                        console.print("[cyan]Monitoring pipeline execution...[/cyan]")
                        console.print("[dim]Fetching stage information...[/dim]\n")

                        # Wait for build to complete
                        last_stages = None
                        while True:
                            build_info = await client.get_build_info(job_name, build_number)
                            result = build_info.get("result")

                            # Try to get stage info
                            try:
                                workflow_info = await client.get_workflow_info(
                                    job_name, build_number
                                )
                                stages = workflow_info.get("stages", [])

                                # Only print if stages changed
                                current_stages = [(s["name"], s.get("status")) for s in stages]
                                if current_stages != last_stages:
                                    from rich.table import Table

                                    table = Table(show_header=True, box=None)
                                    table.add_column("Stage", style="cyan")
                                    table.add_column(
                                        "Status",
                                        justify="center",
                                        min_width=14,
                                        no_wrap=True,
                                    )

                                    for stage in stages:
                                        stage_name = stage["name"]
                                        stage_status = stage.get("status", "UNKNOWN")

                                        if stage_status == "SUCCESS":
                                            status_display = "[green]✓ SUCCESS[/green]"
                                        elif stage_status == "FAILED":
                                            status_display = "[red]✗ FAILED[/red]"
                                        elif stage_status == "IN_PROGRESS":
                                            status_display = "[yellow]⟳ RUNNING[/yellow]"
                                        elif stage_status == "NOT_EXECUTED":
                                            status_display = "[dim]⋯ PENDING[/dim]"
                                        elif stage_status == "ABORTED":
                                            status_display = "[yellow]⊗ ABORTED[/yellow]"
                                        else:
                                            status_display = f"[dim]{stage_status}[/dim]"

                                        table.add_row(stage_name, status_display)

                                    console.print(table)
                                    console.print()
                                    last_stages = current_stages
                            except Exception as e:
                                # Workflow API might not be available
                                logger.debug(f"Could not retrieve workflow stages: {e}")
                                # Continue without stage details

                            if result is not None:
                                # Build completed
                                if result == "SUCCESS":
                                    console.print(
                                        "[green]✓ Pipeline completed successfully[/green]"
                                    )
                                    console.print(f"[dim]Build #{build_number}[/dim]")
                                    if notify:
                                        console.print(
                                            "\n[green]🔔 Notification: Pipeline succeeded[/green]"
                                        )
                                elif result == "FAILURE":
                                    console.print("[red]✗ Pipeline failed[/red]")
                                    console.print(f"[dim]Build #{build_number}[/dim]")
                                    if notify:
                                        console.print(
                                            "\n[red]🔔 Notification: Pipeline failed[/red]"
                                        )
                                    sys.exit(EXIT_JENKINS_API_ERROR)
                                elif result == "ABORTED":
                                    console.print("[yellow]⊗ Pipeline was aborted[/yellow]")
                                    console.print(f"[dim]Build #{build_number}[/dim]")
                                    if notify:
                                        console.print(
                                            "\n[yellow]🔔 Notification: Pipeline aborted[/yellow]"
                                        )
                                    sys.exit(EXIT_JENKINS_API_ERROR)
                                else:
                                    console.print(
                                        f"[yellow]Pipeline completed with status: {result}[/yellow]"
                                    )
                                    console.print(f"[dim]Build #{build_number}[/dim]")
                                    if notify:
                                        console.print(
                                            f"\n[yellow]🔔 Notification: Pipeline status {result}[/yellow]"
                                        )
                                break

                            await asyncio.sleep(5)
                    else:
                        # Just notify when done
                        console.print("[cyan]Waiting for completion to notify...[/cyan]")
                        while True:
                            build_info = await client.get_build_info(job_name, build_number)
                            result = build_info.get("result")

                            if result is not None:
                                if result == "SUCCESS":
                                    console.print(
                                        "\n[green]🔔 Pipeline completed successfully[/green]"
                                    )
                                elif result == "FAILURE":
                                    console.print("\n[red]🔔 Pipeline failed[/red]")
                                    sys.exit(EXIT_JENKINS_API_ERROR)
                                elif result == "ABORTED":
                                    console.print("\n[yellow]🔔 Pipeline was aborted[/yellow]")
                                    sys.exit(EXIT_JENKINS_API_ERROR)
                                else:
                                    console.print(
                                        f"\n[yellow]🔔 Pipeline status: {result}[/yellow]"
                                    )
                                break

                            await asyncio.sleep(10)
                else:
                    console.print("\n[yellow]⚠ Pipeline did not start within 60 seconds[/yellow]")
                    console.print(f"[dim]Queue item ID: {queue_item_id}[/dim]")
                    console.print(
                        f"[dim]Check status with: jctl pipeline describe {job_name} <build>[/dim]"
                    )

        except Exception as e:
            console.print(f"\n[red]Error running pipeline:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    asyncio.run(run_pipeline())


@pipeline.command()
@click.argument("job_name", shell_complete=complete_job_name)
@click.argument("build_number", type=int)
@click.option("--reason", help="Reason for cancellation (for audit logs)")
@click.option("--yes", "-y", is_flag=True, help="Skip the confirmation prompt.")
@click.pass_context
def cancel(
    ctx: click.Context, job_name: str, build_number: int, reason: str | None, yes: bool
) -> None:
    """Cancel/abort a running pipeline."""
    # The previous implementation used @click.confirmation_option, which on
    # "no" exits 1 via Click's generic Abort. That mixed user-cancellation
    # with real errors in callers' exit-code parsing. Map an explicit "no"
    # to EXIT_USER_CANCELLED (130) — the conventional Ctrl+C signal code.
    if not yes and not click.confirm(f"Cancel pipeline {job_name} #{build_number}?", default=False):
        console.print("[yellow]Cancellation aborted by user[/yellow]")
        sys.exit(EXIT_USER_CANCELLED)

    client = get_jenkins_client(ctx)

    console.print(f"[cyan]Cancelling:[/cyan] {job_name} #{build_number}")

    if reason:
        console.print(f"[dim]Reason: {reason}[/dim]")

    # Stop the build
    async def stop_build() -> None:
        try:
            with console.status("[yellow]Stopping pipeline...[/yellow]"):
                await client.stop_build(job_name, build_number)
        except Exception as e:
            console.print(f"[red]Error stopping pipeline:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    asyncio.run(stop_build())

    console.print(f"[green]✓[/green] Pipeline {job_name} #{build_number} cancelled")

    if reason:
        console.print(f"[dim]Audit log: Cancelled by user - {reason}[/dim]")
