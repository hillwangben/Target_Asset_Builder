"""CLI 入口 - 提供命令行交互接口"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from src import __version__
from src.catalog import CatalogManager
from src.config import load_config, AppConfig
from src.models import CollectionTask, SensorType, TargetType
from src.collector import Collector

console = Console()


def _setup_logging(level: str = "INFO", log_file: str = ""):
    """配置日志。"""
    handlers: list[logging.Handler] = [RichHandler(console=console, show_time=False)]

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=handlers,
    )


@click.group()
@click.version_option(__version__, prog_name="tab")
@click.option(
    "-c", "--config",
    default=None,
    help="配置文件路径",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="详细输出模式",
)
@click.pass_context
def main(ctx: click.Context, config: Optional[str], verbose: bool):
    """Target Asset Builder - 多模态军事目标数据采集系统"""
    ctx.ensure_object(dict)

    try:
        cfg = load_config(config)
    except FileNotFoundError as e:
        console.print(f"[red]错误:[/red] {e}")
        sys.exit(1)

    log_level = "DEBUG" if verbose else cfg.logging.level
    _setup_logging(log_level, cfg.logging.file)

    ctx.obj["config"] = cfg


@main.command()
@click.option(
    "--country", "-n", default=None,
    help="国家/地区代码，如 USA, China, Russia（可选）",
)
@click.option(
    "--type", "-t", "target_type", default=None,
    type=click.Choice([e.value for e in TargetType], case_sensitive=False),
    help="目标类型（可选）",
)
@click.option(
    "--model", "-m", default=None,
    help="型号，如 F-22, J-20, Arleigh-Burke（可选）",
)
@click.option(
    "--sensor", "-s", default="unknown",
    type=click.Choice([e.value for e in SensorType], case_sensitive=False),
    help="传感器类型",
)
@click.option(
    "--source", "source_name", default="github",
    type=click.Choice(["github", "url", "web", "huggingface", "multi"], case_sensitive=False),
    help="数据源（github=GitHub仓库, url=直接URL, web=网页搜索, huggingface=HuggingFace数据集, multi=多源综合）",
)
@click.option(
    "--keywords", "-k", multiple=True, required=True,
    help="搜索关键词（可多次指定）",
)
@click.option(
    "--min-width", type=int, default=0,
    help="最小宽度（像素）",
)
@click.option(
    "--min-height", type=int, default=0,
    help="最小高度（像素）",
)
@click.option(
    "--min-dimension", type=int, default=0,
    help="最小维度（像素，取宽高中较小值）",
)
@click.option(
    "--max-count", type=int, default=None,
    help="最大采集数量，达到此数量后自动停止",
)
@click.option(
    "--max-duration", type=int, default=None,
    help="最大采集时长（秒），达到此时间后自动停止",
)
@click.pass_context
def collect(
    ctx: click.Context,
    country: Optional[str],
    target_type: Optional[str],
    model: Optional[str],
    sensor: str,
    source_name: str,
    keywords: tuple[str, ...],
    min_width: int,
    min_height: int,
    min_dimension: int,
    max_count: Optional[int],
    max_duration: Optional[int],
):
    """执行数据采集任务。

    注意：country、type、model 参数均为可选，未指定时将使用默认值 "ALL" 进行采集，
    不会进行特定分类过滤。
    """
    cfg: AppConfig = ctx.obj["config"]

    # 使用配置文件的默认值（如果命令行未指定）
    if max_count is None:
        max_count = cfg.limits.default_max_count
    if max_duration is None:
        max_duration = cfg.limits.default_max_duration

    # 覆盖分辨率过滤配置
    if min_width > 0 or min_height > 0 or min_dimension > 0:
        cfg.filters.resolution.enabled = True
        cfg.filters.resolution.min_width = min_width
        cfg.filters.resolution.min_height = min_height
        cfg.filters.resolution.min_dimension = min_dimension

    # 未指定的参数使用 "ALL" 作为占位符
    final_country = country if country else "ALL"
    final_type = TargetType(target_type) if target_type else TargetType.AIRPLANE
    final_model = model if model else "ALL"

    task = CollectionTask(
        country=final_country,
        type=final_type,
        model=final_model,
        sensor=SensorType(sensor),
        keywords=list(keywords),
        source=source_name,
        max_count=max_count,
        max_duration_seconds=max_duration,
    )

    limit_info = []
    if max_count:
        limit_info.append(f"最大数量: {max_count}")
    if max_duration:
        limit_info.append(f"最大时长: {max_duration}秒")
    limit_str = " | ".join(limit_info) if limit_info else "无限制"

    # 显示采集信息
    console.print(
        f"\n[bold green]开始采集任务[/bold green]\n"
        f"  目标: [cyan]{task.display_name}[/cyan]\n"
        f"  传感器: [cyan]{sensor}[/cyan]\n"
        f"  数据源: [cyan]{source_name}[/cyan]\n"
        f"  关键词: [cyan]{', '.join(keywords)}[/cyan]\n"
        f"  限制: [cyan]{limit_str}[/cyan]\n"
    )

    collector = Collector(cfg)
    stats = asyncio.run(collector.collect(task))

    _print_stats(stats)
    console.print("\n[bold green]采集完成！[/bold green]\n")


@main.command("collect-batch")
@click.option(
    "--file", "-f", "task_file", required=True,
    type=click.Path(exists=True),
    help="批量任务 JSON 文件路径",
)
@click.pass_context
def collect_batch(ctx: click.Context, task_file: str):
    """从 JSON 文件批量执行采集任务。"""
    import json

    cfg: AppConfig = ctx.obj["config"]
    collector = Collector(cfg)

    with open(task_file, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)

    if isinstance(tasks_data, dict):
        tasks_data = [tasks_data]

    console.print(f"[bold]共 {len(tasks_data)} 个采集任务[/bold]\n")

    for i, task_data in enumerate(tasks_data, 1):
        console.print(f"[cyan]任务 {i}/{len(tasks_data)}[/cyan]")

        # 处理可选参数，未指定时使用 "ALL"
        country = task_data.get("country", "ALL")
        type_value = task_data.get("type")
        model = task_data.get("model", "ALL")

        task = CollectionTask(
            country=country,
            type=TargetType(type_value) if type_value else TargetType.AIRPLANE,
            model=model,
            sensor=SensorType(task_data.get("sensor", "unknown")),
            keywords=task_data["keywords"],
            source=task_data.get("source", "github"),
            max_count=task_data.get("max_count"),
            max_duration_seconds=task_data.get("max_duration_seconds"),
        )

        stats = asyncio.run(collector.collect(task))
        _print_stats(stats)
        console.print()

    console.print("[bold green]所有任务完成！[/bold green]")


@main.command()
@click.option(
    "--country", "-n", default=None,
    help="按国家过滤",
)
@click.option(
    "--type", "-t", "target_type", default=None,
    help="按目标类型过滤",
)
@click.option(
    "--model", "-m", default=None,
    help="按型号过滤",
)
@click.option(
    "--sensor", "-s", default=None,
    help="按传感器类型过滤",
)
@click.option(
    "--format", "output_format", default="table",
    type=click.Choice(["table", "json"]),
    help="输出格式",
)
@click.pass_context
def search(
    ctx: click.Context,
    country: Optional[str],
    target_type: Optional[str],
    model: Optional[str],
    sensor: Optional[str],
    output_format: str,
):
    """查询已采集的数据目录。"""
    cfg: AppConfig = ctx.obj["config"]
    catalog = CatalogManager(cfg.storage.root_dir, cfg.storage.catalog_file)
    catalog.load()

    results = catalog.get_assets_by_filter(
        country=country,
        target_type=target_type,
        model=model,
        sensor=sensor,
    )

    if output_format == "json":
        import json
        console.print_json(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not results:
        console.print("[yellow]未找到匹配的记录[/yellow]")
        return

    table = Table(title="采集数据目录", show_lines=True)
    table.add_column("国家", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("型号", style="yellow")
    table.add_column("传感器")
    table.add_column("媒体")
    table.add_column("格式")
    table.add_column("分辨率")
    table.add_column("大小")
    table.add_column("路径", max_width=40)

    for asset in results:
        res = asset.get("resolution")
        res_str = f"{res['width']}x{res['height']}" if res else "-"
        size = asset.get("file_size", 0)
        size_str = _format_size(size)

        table.add_row(
            asset.get("country", "-"),
            asset.get("type", "-"),
            asset.get("model", "-"),
            asset.get("sensor", "-"),
            asset.get("media_type", "-"),
            asset.get("format", "-"),
            res_str,
            size_str,
            asset.get("file_path", "-"),
        )

    console.print(table)
    console.print(f"\n共 [bold]{len(results)}[/bold] 条记录")


@main.command()
@click.pass_context
def stats(ctx: click.Context):
    """显示采集统计信息。"""
    cfg: AppConfig = ctx.obj["config"]
    catalog = CatalogManager(cfg.storage.root_dir, cfg.storage.catalog_file)
    catalog.load()
    s = catalog.get_stats()
    _print_stats(s)


@main.command()
@click.pass_context
def info(ctx: click.Context):
    """显示系统信息。"""
    cfg: AppConfig = ctx.obj["config"]

    table = Table(title="系统信息")
    table.add_column("配置项", style="cyan")
    table.add_column("值")

    table.add_row("版本", __version__)
    table.add_row("存储目录", str(cfg.storage.root_dir))
    table.add_row("目录文件", cfg.storage.catalog_file)
    table.add_row("下载数", str(cfg.download.concurrency))
    table.add_row("分辨率过滤", "启用" if cfg.filters.resolution.enabled else "禁用")

    if cfg.filters.resolution.enabled:
        table.add_row("  最小宽度", str(cfg.filters.resolution.min_width) or "不限")
        table.add_row("  最小高度", str(cfg.filters.resolution.min_height) or "不限")
        table.add_row("  最小维度", str(cfg.filters.resolution.min_dimension) or "不限")

    console.print(table)


def _print_stats(stats) -> None:
    """打印采集统计。"""
    table = Table(title="采集统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("总文件数", str(stats.total_files))
    table.add_row("总大小", _format_size(stats.total_size))
    table.add_row("跳过", str(stats.skipped))
    table.add_row("失败", str(stats.failed))

    if stats.by_country:
        table.add_section()
        table.add_row("[bold]按国家[/bold]", "")
        for country, count in sorted(stats.by_country.items()):
            table.add_row(f"  {country}", str(count))

    if stats.by_type:
        table.add_section()
        table.add_row("[bold]按类型[/bold]", "")
        for t, count in sorted(stats.by_type.items()):
            table.add_row(f"  {t}", str(count))

    if stats.by_media:
        table.add_section()
        table.add_row("[bold]按媒体[/bold]", "")
        for m, count in sorted(stats.by_media.items()):
            table.add_row(f"  {m}", str(count))

    console.print(table)


def _format_size(size_bytes: int) -> str:
    """格式化文件大小。"""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


if __name__ == "__main__":
    main()
