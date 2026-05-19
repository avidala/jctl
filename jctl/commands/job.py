"""Job management commands."""

import asyncio
import sys

import click
from rich.console import Console

from jctl.constants import (
    EXIT_JENKINS_API_ERROR,
)
from jctl.utils.completion import complete_job_name
from jctl.utils.jenkins_client_factory import get_jenkins_client
from jctl.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def job() -> None:
    """Manage Jenkins jobs."""
    pass


@job.command()
@click.argument("job_name", shell_complete=complete_job_name)
@click.option("--param", "-p", multiple=True, help="Job parameters (key=value)")
@click.option("--wait", is_flag=True, help="Wait for job completion")
@click.option("--dry-run", is_flag=True, help="Show what would be triggered")
@click.pass_context
def trigger(
    ctx: click.Context, job_name: str, param: tuple[str, ...], wait: bool, dry_run: bool
) -> None:
    """Trigger a Jenkins job with parameters.

    Examples:
        jctl job trigger deploy/release-pipeline -p environment=dev -p version=1.2.3
        jctl job trigger deploy/release-pipeline --param environment=dev --wait
    """
    params = dict(p.split("=", 1) for p in param) if param else {}

    console.print(f"[cyan]Triggering job:[/cyan] {job_name}")

    if params:
        console.print("[cyan]Parameters:[/cyan]")
        for key, value in params.items():
            console.print(f"  {key} = {value}")

    if dry_run:
        console.print("[yellow]Dry run mode - no actual trigger[/yellow]")
        return

    # Get authenticated client
    client = get_jenkins_client(ctx)

    async def trigger_job():
        try:
            with console.status("[cyan]Triggering job...[/cyan]"):
                queue_item_id = client.trigger_job(job_name, params if params else None)

            console.print("\n[green]✓[/green] Job triggered successfully")
            console.print(f"[dim]Queue item ID: {queue_item_id}[/dim]")

            if wait:
                console.print("\n[cyan]Waiting for job to start...[/cyan]")

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
                                    f"[green]✓[/green] Job started - Build #{build_number}"
                                )
                                break

                        # Check if still in queue
                        if queue_info.get("blocked"):
                            console.print("[yellow]Job is blocked in queue...[/yellow]")
                        elif queue_info.get("stuck"):
                            console.print("[yellow]Job is stuck in queue...[/yellow]")
                        else:
                            console.print("[dim]Job is queued...[/dim]")

                    except Exception as e:
                        logger.debug(f"Could not retrieve queue info: {e}")
                        # Continue without queue details

                    await asyncio.sleep(1)

                if build_number:
                    console.print(f"\n[cyan]Monitoring build #{build_number}...[/cyan]")

                    # Wait for build to complete
                    while True:
                        build_info = await client.get_build_info(job_name, build_number)
                        result = build_info.get("result")

                        if result is not None:
                            # Build completed
                            if result == "SUCCESS":
                                console.print(
                                    f"\n[green]✓ Build #{build_number} completed successfully[/green]"
                                )
                            elif result == "FAILURE":
                                console.print(f"\n[red]✗ Build #{build_number} failed[/red]")
                                sys.exit(EXIT_JENKINS_API_ERROR)
                            elif result == "ABORTED":
                                console.print(
                                    f"\n[yellow]⊗ Build #{build_number} was aborted[/yellow]"
                                )
                                sys.exit(EXIT_JENKINS_API_ERROR)
                            else:
                                console.print(
                                    f"\n[yellow]Build #{build_number} completed with status: {result}[/yellow]"
                                )
                            break

                        # Build still running
                        duration = build_info.get("duration", 0)
                        if duration == 0:
                            console.print("[dim]Build is running...[/dim]")

                        await asyncio.sleep(5)
                else:
                    console.print("\n[yellow]⚠ Job did not start within 60 seconds[/yellow]")
                    console.print(f"[dim]Queue item ID: {queue_item_id}[/dim]")
                    console.print(f"[dim]Check status with: jctl job status {job_name}[/dim]")

        except Exception as e:
            console.print(f"\n[red]Error triggering job:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    asyncio.run(trigger_job())


@job.command()
@click.argument("job_name", shell_complete=complete_job_name)
@click.argument("build_number", type=int, required=False)
@click.option("--follow", "-f", is_flag=True, help="Stream logs in real-time")
@click.pass_context
def logs(ctx: click.Context, job_name: str, build_number: int | None, follow: bool) -> None:
    """View or stream job logs.

    Examples:
        jctl job logs deploy/release-pipeline 123
        jctl job logs deploy/release-pipeline --follow
    """
    # Get authenticated client
    client = get_jenkins_client(ctx)

    async def get_logs():
        try:
            # If no build number, get the latest build
            if build_number is None:
                with console.status(f"[cyan]Getting latest build for {job_name}...[/cyan]"):
                    jobs = await client.get_jobs()
                    job = next((j for j in jobs if j.get("fullName") == job_name), None)

                    if not job:
                        console.print(f"[red]Error:[/red] Job '{job_name}' not found")
                        sys.exit(EXIT_JENKINS_API_ERROR)

                    last_build = job.get("lastBuild")
                    if not last_build:
                        console.print(f"[red]Error:[/red] No builds found for '{job_name}'")
                        sys.exit(EXIT_JENKINS_API_ERROR)

                    latest_build_number = last_build.get("number")
                    if not latest_build_number:
                        console.print("[red]Error:[/red] Could not get latest build number")
                        sys.exit(EXIT_JENKINS_API_ERROR)

                    console.print(f"[dim]Using latest build #{latest_build_number}[/dim]\n")
                    return latest_build_number

            return build_number

        except Exception as e:
            console.print(f"[red]Error getting build info:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    async def stream_logs(build_num: int):
        """Stream logs in real-time."""
        console.print(f"[cyan]Streaming logs for:[/cyan] {job_name} #{build_num}\n")
        console.print("[dim]Press Ctrl+C to stop streaming[/dim]\n")

        def print_line(line: str):
            console.print(line, highlight=False)

        try:
            await client.stream_build_log(job_name, build_num, print_line)
            console.print("\n[green]✓[/green] Build completed")
        except KeyboardInterrupt:
            console.print("\n[yellow]Streaming stopped by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error streaming logs:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    async def fetch_logs(build_num: int):
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
                print(log_text, end="")
                return

            console.print(f"[cyan]Logs for:[/cyan] {job_name} #{build_num}\n")
            console.print(log_text, highlight=False)

        except Exception as e:
            console.print(f"[red]Error fetching logs:[/red] {e}")
            sys.exit(EXIT_JENKINS_API_ERROR)

    # Main execution
    build_num = asyncio.run(get_logs())

    if follow:
        asyncio.run(stream_logs(build_num))
    else:
        asyncio.run(fetch_logs(build_num))
