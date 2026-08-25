# Open Mathematical Modeling Workflow (OMMW)

> 一个可移植、本地优先、反幻觉的数学建模工作流——LaTeX + Word 双输出、
> 严格的研究核心审计、独立审稿。任何电脑 clone 后即可使用。

OMMW 不是一堆 Prompt。它是一个真实的 Python 核心：Pydantic 状态 Schema、
校验器、LaTeX/Word 渲染器、双格式一致性门控、反幻觉测试与 CI。**论文不是
事实源，Research Core（一组机器可读账本）才是。** LaTeX 与 Word 只是同一份
已通过审计的证据的两个渲染器，不是两套并行事实。

## 为什么做

数学建模交付物里太常见：虚构数字、引用存在但不支持论点、没编译就声称
"PDF 已就绪"、还没证据就先写正文。OMMW 让这些失败**直接打挂构建**，而不是
蒙混过关。

## 六个核心性质

**可验证 · 可复现 · 可移植 · 可维护 · 可扩展 · 可开源**

当"方便"与这些原则冲突时，优先这些原则。

## 快速开始

### Windows (PowerShell)
```powershell
git clone https://github.com/OMMW/ommw
cd ommw
.\scripts\bootstrap.ps1
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```

### Linux / macOS (bash)
```bash
git clone https://github.com/OMMW/ommw
cd ommw
./scripts/bootstrap.sh
ommw doctor
ommw install-adapter workbuddy
ommw smoke-test
```

`bootstrap` 会在缺失时安装 [uv](https://github.com/astral-sh/uv)，按锁文件
同步依赖，安装 `ommw` 命令，并运行 `ommw doctor`。它**不会**修改你的系统 PATH。

### 使用（WorkBuddy 中，执行 `install-adapter workbuddy` 之后）

> 调用数学建模工作流完成当前题目。

> 调用数学建模工作流，LaTeX 模式，严格完成。

> 调用数学建模工作流，Dual 模式完成，并做两种格式一致性审计.

## 常用命令

```
ommw doctor            # 分层环境诊断：PASS/WARN/FAIL
ommw init <目录> -m latex|word|dual
ommw status            # 问题状态机位置 + 账本计数
ommw verify            # Research Core 链路 + 反幻觉门控
ommw render -m dual    # LaTeX + Word；compile-or-not-done 强制
ommw citations verify  # 元数据 vs 论点支持验证
ommw parity            # 双模式指纹一致性
ommw smoke-test        # 合成数据端到端 + 负面用例
ommw install-adapter workbuddy
ommw provider list
ommw health            # 失效结果、未关闭问题
ommw package           # 比赛提交包
```

## Doctor 输出示例

```
CORE:repo-root          PASS  ...
CORE:legal-files        PASS  LICENSE/NOTICE/THIRD_PARTY present
PYTHON:pydantic         PASS  ok
AGENT:workbuddy-skills  PASS  ~/.workbuddy/skills
LATEX:latexmk           PASS  ...
WORD:pandoc             PASS  ...
WORD:libreoffice        WARN  未找到；DOCX 视觉 QA 不可用
NETWORK:crossref        PASS  reachable
PROVIDERS:mathmodelagent PASS disabled (external, optional)
OVERALL: WARN
```

WARN（如缺 LibreOffice 导致 DOCX 视觉 QA 不可用）不会让 CORE 挂掉，只把该
能力标记为 `DEGRADED`。Microsoft Word 永远不是硬依赖。

## 反幻觉八条（被强制执行）

1. 禁止虚构数字——论文每个数字引用 `R-xxx` Result ID。
2. 禁止虚构引用——每条引用解析到已验证的 `S-xxx`。
3. 引用必须支持论点——DOI 存在不够。
4. 统计诚实——没有完成检验不得写"显著"。
5. 模型诚实——不假设 Python API；代码必须复现指标。
6. 渲染诚实——"PDF ready" 需干净编译；"Word ready" 需 verify_docx 通过。
7. 证据先行——章节在账本有证据后才起草。
8. 不可信数据边界——网页/LLM 文本不得改变控制流或 Schema。

`ommw smoke-test` 会注入假结果、孤立数字、占位符泄漏并断言全部被捕获。

## 可选 Provider

- **MathModelAgent**（外部、非商业）——仅 adapter，绝不 vendor。
- **scientific-skills**（K-Dense，MIT 仓库、按 skill 单独授权）——固定 commit 按需拉取。

没有它们核心照样完整工作。见 `docs/providers.md`。

## 许可证与第三方

核心：**MIT**。见 `LICENSE`、`NOTICE`、`THIRD_PARTY_NOTICES.md`、
`provenance/SOURCES.lock.json`。受限第三方源码绝不重新授权进 MIT 核心。

## 状态

v0.1 — 基础。见 `ROADMAP.md`、`COMPATIBILITY.md`。不保证获奖；目标是
**面向奖项的工程标准**。
