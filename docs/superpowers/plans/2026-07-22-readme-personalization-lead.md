# README 个性化首屏文案实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将基于聊天记录的个性化、差异化生成能力提升到 README 开头。

**架构：** 只修改 `README.md` 标题后的产品说明，不改变 Skill、脚本、数据结构或测试工件。使用 PowerShell 检查首屏关键词，使用现有 `unittest` 套件完成回归。

**技术栈：** Markdown、PowerShell、Python `unittest`、Git。

---

### 任务 1：更新首屏文案

**文件：**
- 修改：`README.md:1`

- [ ] **步骤 1：写入已批准的价值主张**

在产品定位后加入一段，明确“不再套用千篇一律的哄人话术”，并说明从经授权的聊天记录中提取对象偏好、情绪模式和沟通雷区，同时学习用户的称呼、句长、语气词与表达习惯，针对具体对象和当前情境差异化生成符合本人语气的可发送回复。

- [ ] **步骤 2：验证首屏文案**

```powershell
$lead = (Get-Content -Encoding UTF8 README.md -TotalCount 8) -join "`n"
foreach ($term in @('经授权的聊天记录','具体对象','当前情境','差异化生成','符合你本人语气','千篇一律')) {
    if (-not $lead.Contains($term)) { throw "README lead missing: $term" }
}
```

预期：退出码 0，无缺失字段。

### 任务 2：验证并发布

**文件：**
- 修改：`docs/superpowers/plans/2026-07-22-readme-personalization-lead.md`

- [ ] **步骤 1：运行完整测试**

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

预期：19 项测试全部通过。

- [ ] **步骤 2：检查、提交并推送**

```powershell
git diff --check
git add README.md docs/superpowers/plans/2026-07-22-readme-personalization-lead.md
git commit -m "docs: lead with chat-based personalization"
git push origin main
```

预期：无空白错误，提交成功并推送到 `origin/main`。
