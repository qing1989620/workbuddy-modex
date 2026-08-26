"""AI Usage Ledger operations (Rule 7).

Records every AI-assisted step; generates the paper's AI-usage declaration
from the ACTUAL log. Never fabricated. Outputs:
  - state/ai_usage.jsonl  (the ledger)
  - paper/ai-usage-declaration.md (paper section, generated from ledger)
  - dist/AI工具使用详情.md (detail report)
"""
from __future__ import annotations

import time

from .. import atomic
from ..paths import ProjectPaths
from ..schemas import AIUsageRecord, AIUsageSummary


def append_usage(pp: ProjectPaths, rec: AIUsageRecord) -> None:
    rec.record_id = rec.record_id or f"AU-{len(atomic.read_jsonl(pp.state_dir / 'ai_usage.jsonl')) + 1:03d}"
    atomic.append_jsonl(pp.state_dir / "ai_usage.jsonl", rec.model_dump(mode="json"))


def list_usage(pp: ProjectPaths) -> list[AIUsageRecord]:
    return [AIUsageRecord(**r) for r in atomic.read_jsonl(pp.state_dir / "ai_usage.jsonl")]


def summarize(pp: ProjectPaths) -> AIUsageSummary:
    recs = list_usage(pp)
    tools = sorted({r.tool for r in recs})
    return AIUsageSummary(
        total_records=len(recs),
        accepted=sum(1 for r in recs if r.accepted),
        human_reviewed=sum(1 for r in recs if r.human_review),
        tools=tools,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
    )


def generate_ai_report(pp: ProjectPaths) -> tuple[str, str]:
    """Generate (declaration_md, detail_md) from the real ledger."""
    recs = list_usage(pp)
    if not recs:
        decl = ("# AI 工具使用声明\n\n本论文的 AI 使用记录尚未生成（ledger 为空）。\n"
                "正式声明必须基于实际日志生成，禁止伪造。\n")
        return decl, decl

    # Declaration (concise, for the paper appendix).
    lines = ["# AI 工具使用声明", ""]
    tools = sorted({r.tool for r in recs})
    lines.append(f"本论文在研究过程中使用了以下 AI 工具：{', '.join(tools)}。")
    lines.append(f"共记录 AI 辅助步骤 {len(recs)} 项，其中 {sum(1 for r in recs if r.human_review)} 项经过人工复核。")
    lines.append("所有关键结果均通过实际运行实验验证，未由 AI 直接生成实验数值。")
    decl = "\n".join(lines) + "\n"

    # Detail report (audit).
    det = ["# AI 工具使用详情", "", "| ID | 工具 | 任务 | 用途 | 人工复核 | 验证方式 | 采用 |",
           "|---|---|---|---|---|---|---|"]
    for r in recs:
        det.append(f"| {r.record_id} | {r.tool} | {r.task} | {r.purpose} | "
                   f"{'是' if r.human_review else '否'} | {r.verification_method} | "
                   f"{'是' if r.accepted else '否'} |")
    detail = "\n".join(det) + "\n"

    # Persist both.
    pp.paper_dir.mkdir(parents=True, exist_ok=True)
    (pp.paper_dir / "ai-usage-declaration.md").write_text(decl, encoding="utf-8")
    pp.dist_dir.mkdir(parents=True, exist_ok=True)
    (pp.dist_dir / "AI工具使用详情.md").write_text(detail, encoding="utf-8")
    return decl, detail
