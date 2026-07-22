# README 组合优势与第三方声明实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 README 中准确解释项目组合优势，并补齐两个参考 Skill 的许可证、署名、非商业限制，以及 WeFlow 格式兼容与无官方隶属声明。

**架构：** `README.md` 面向普通用户说明方法来源、能力对比和使用边界；`THIRD_PARTY_NOTICES.md` 集中记录上游项目、作者、链接和适用说明；`licenses/` 保存未经改写的上游许可证文本。项目不声明一份可能覆盖范围不清的总许可证。

**技术栈：** Markdown、PowerShell 文档检查、Python `unittest`、Git。

---

### 任务 1：添加第三方许可证原文

**文件：**
- 创建：`licenses/goutoujunshi-PolyForm-Noncommercial-1.0.0.txt`
- 创建：`licenses/create-ex-MIT.txt`

- [x] **步骤 1：复制经核验的上游许可证文本**

从本地已安装的两个参考项目逐字复制许可证，不修改作者、年份、链接或 Required Notice。

- [x] **步骤 2：验证许可证内容**

运行：

```powershell
Compare-Object (Get-Content licenses\goutoujunshi-PolyForm-Noncommercial-1.0.0.txt) (Get-Content C:\Users\32916\.codex\skills\goutoujunshi\LICENSE)
Compare-Object (Get-Content licenses\create-ex-MIT.txt) (Get-Content C:\Users\32916\.agents\skills\create-ex\LICENSE)
```

预期：两条命令均无差异输出。

### 任务 2：添加第三方声明

**文件：**
- 创建：`THIRD_PARTY_NOTICES.md`

- [x] **步骤 1：写明来源与适用许可**

列出：

- `goutoujunshi`、`powerycy`、官方仓库链接、PolyForm Noncommercial 1.0.0、Required Notice；
- `create-ex`、`therealXiaomanChu`、官方仓库链接、MIT License；
- `WeFlow`、`hicccc77/WeFlow` 官方仓库链接，以及“只兼容用户导出格式、未复制或捆绑 WeFlow 代码”的说明；
- WeFlow 仓库在核查时未提供可识别的许可证，因此本项目不授予任何 WeFlow 代码权利；
- 本项目是独立项目，不获两个上游项目背书；
- 方法借鉴不代表复制上游完整知识库、提示词或工具代码；
- 商业使用者应先确认许可范围并取得必要授权。

- [x] **步骤 2：检查声明字段**

运行：

```powershell
rg -n "powerycy|therealXiaomanChu|hicccc77/WeFlow|PolyForm Noncommercial|MIT License|Required Notice|格式兼容|非商业|独立项目" THIRD_PARTY_NOTICES.md
```

预期：每个必要字段至少匹配一次。

### 任务 3：更新 README 组合优势与许可边界

**文件：**
- 修改：`README.md`

- [x] **步骤 1：添加组合优势章节**

在“工作方式”和“安装”之间加入：

- `goutoujunshi` 负责情绪、事实、关系利益、边界、行动和后续；
- `create-ex` 提供从聊天材料和纠正中蒸馏关系记忆与表达模式的方法；
- 本项目将其改造成对象档案和本人语气档案，不模拟或冒充现任；
- 核心原则是“先决定说什么，再决定怎么说”。

加入五类方案、七个维度的 Markdown 对比表。

- [x] **步骤 2：添加来源与许可证章节**

说明项目当前按非商业用途发布，引用 `THIRD_PARTY_NOTICES.md` 及两个许可证文件；同时说明 WeFlow 仅为格式兼容、不复制或捆绑其代码，并声明无官方隶属或背书。

- [x] **步骤 3：验证 README 结构**

运行 PowerShell，检查章节顺序、两个上游名称、五类方案、七个比较维度、非商业说明和第三方声明链接。

预期：输出 `README comparison and notices checks passed`。

### 任务 4：回归验证与发布

**文件：**
- 修改：`docs/superpowers/plans/2026-07-22-readme-comparison-and-notices.md`

- [x] **步骤 1：运行测试**

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

预期：18 项测试全部通过。

- [x] **步骤 2：检查差异**

```powershell
git diff --check
git status --short
```

预期：无空白错误；只有本计划内文件发生变化。

- [x] **步骤 3：提交并推送**

```powershell
git add README.md THIRD_PARTY_NOTICES.md licenses docs/superpowers/plans/2026-07-22-readme-comparison-and-notices.md
git commit -m "docs: explain upstream influences and licensing"
git push origin main
```

预期：提交成功并推送到 `origin/main`。
