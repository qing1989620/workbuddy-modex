# Abstract 硬门与写作规范（v0.2）

> 实现：`paper/gates.py::abstract_gate`。CLI：`ommw audit-paper`。

## 硬门（缺失 = CRITICAL FAILURE）

摘要必须**同时**存在于两个渲染源：

- `paper/latex/sections/abstract.tex`
- `paper/word/sections/abstract.md`

两侧同时缺失/清空 ⇒ `ABSTRACT_MISSING`（CRITICAL）⇒ 论文 BLOCKED，后续
任何阶段不得继续。单侧缺失触发 `ABSTRACT_NOT_IN_LATEX_SOURCES`（MEDIUM，
双模式漂移提示）。

## 摘要内容期望（非硬门，MEDIUM 级提示）

- `ABSTRACT_TOO_SHORT`：有效词过少，不足以概括方法/结果/结论。
- `ABSTRACT_NO_QUANTITATIVE_RESULT`：全文无 R-XXX 引用、无数值、无百分比
  ——评委无从判断贡献。
- `ABSTRACT_NO_KEYWORDS`：缺关键词行。
- `ABSTRACT_GENERIC_MODEL_PHRASE`：出现"建立数学模型进行求解"等套话。

## 写作规范（agent 义务）

1. 摘要 ≤ 1 页（双格式一致）；三要素齐全：**问题→方法→结果（带 R-ID）**。
2. 结果必须锚定台账：写 "MAE 降至 R-002 的 0.7054 订单" 而非裸数字。
3. 关键词 3-5 个，中英文一致。
4. 在**证据冻结（EVIDENCE_FREEZE）之后**写摘要，数字不许随正文漂移。
5. 摘要写完后必须再过一遍 `abstract_gate`；任何 CRITICAL 立即回退补写。

## 为什么这是硬门

demo4 复盘（audits/paper-production-postmortem.md）显示：占位符论文的
摘要即空壳。摘要缺失是"论文根本没生产"的最强信号，故设为最高优先级否决项。
