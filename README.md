# hongduixiang

一个面向 Codex 和 Claude Code CLI 的个性化「哄对象」回复 Skill。

它会先判断当前聊天里的情绪与关系问题，再结合经过证据支持的对象档案和你的真实说话习惯，给出可以直接发送的回复、行动建议以及后续接话方向。

> 这个项目帮助你更诚实、清楚地沟通，不用于操控、监视、冒充或替代真实关系中的交流。

## 功能

- 分析撒娇、冷淡、争吵、道歉、陪伴、空间、纪念日和关系修复等情境。
- 默认生成一条最推荐、可以直接复制发送的回复。
- 根据聊天证据学习你的句长、称呼、标点、表情和亲密程度。
- 将事实、高置信度模式和待验证推测分开，避免把猜测当结论。
- 支持 WeFlow 导出的 TXT、JSON 和 JSONL 聊天记录。
- 私人画像默认保存在 Git 仓库之外，并提供带确认令牌的删除流程。
- 拒绝 PUA、情绪勒索、秘密监控、威胁、跟踪和绕过拒绝等请求。

## 工作方式

```text
当前聊天或事件背景
        │
        ├── 对象档案：偏好、雷区、冲突与安慰模式
        ├── 本人语气：称呼、句长、语气词、标点与表情
        └── 情境策略：理解、道歉、补救、陪伴、空间或边界
        │
        ▼
情况判断 → 现在怎么做 → 可直接发送的回复 → 后续接话
```

没有建立语气档案时，Skill 会提供自然、克制的临时版本，并避免擅自使用「宝宝」「永远」「一定」等未经证据支持的表达。

## 安装

先克隆仓库：

```powershell
git clone https://github.com/liutianyi746-lab/hongduixiang.git
cd hongduixiang
```

### Codex CLI / Codex App

将 Skill 复制到个人 Skill 目录：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\girlfriend-reply-coach" "$HOME\.codex\skills\girlfriend-reply-coach"
```

在 Codex 中直接提及 Skill 名称即可：

```text
使用 girlfriend-reply-coach。她说：“算了，你忙吧。”
帮我判断她现在需要什么，并写一句我可以直接发的回复。
```

也可以提供更多上下文：

```text
使用 girlfriend-reply-coach。
背景：我答应晚上陪她，但临时加班后忘记提前说。
她回复：“没事，你忙你的。”
要求：按我的语气写，别太肉麻，并告诉我发完以后怎么做。
```

### Claude Code CLI

Claude Code 支持相同的 `SKILL.md` 结构。将目录复制到个人 Skills：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force ".\girlfriend-reply-coach" "$HOME\.claude\skills\girlfriend-reply-coach"
```

启动 Claude Code：

```powershell
claude
```

然后通过斜杠命令调用：

```text
/girlfriend-reply-coach 她说“你根本不在乎我”，结合上下文给我一条能直接发的回复
```

也可以直接用自然语言描述问题，让 Claude 在匹配到 Skill 描述时自动加载：

```text
她因为我忘记纪念日生气了。请使用 girlfriend-reply-coach 分析并帮我回复。
```

Claude Code 也支持把 Skill 放在项目级目录 `.claude/skills/girlfriend-reply-coach/`。个人目录适用于所有项目，项目目录只对当前项目生效。详见 [Claude Code Skills 官方文档](https://code.claude.com/docs/en/slash-commands)。

## 导入 WeFlow 聊天记录

导入前，请确认你有权使用相关聊天资料，并尊重聊天参与者的隐私。

兼容格式：

- WeFlow TXT
- 普通 JSON
- JSONL
- 常见 ChatLab、Arkme JSON 字段结构

只检查文件并输出统计，不保存消息正文：

```powershell
python .\girlfriend-reply-coach\scripts\import_weflow.py "C:\path\to\chat.txt"
```

明确指定输出后，才会保存标准化消息：

```powershell
python .\girlfriend-reply-coach\scripts\import_weflow.py `
  "C:\path\to\chat.txt" `
  --output "$HOME\.codex\private\girlfriend-reply-coach\derived\current\messages.json"
```

导入器会拒绝把聊天输出写进 Git 工作区。系统消息和媒体正文不会进入证据视图；媒体只保留数量等必要统计。

> 导入和标准化不等于自动确认人物结论。画像结论仍需区分证据类别、适用情境与置信度。

## 私人画像

默认私人数据目录：

```text
~/.codex/private/girlfriend-reply-coach/
├── manifest.json
├── self-voice.json
├── people/<slug>/profile.json
├── derived/<slug>/
└── raw/<slug>/
```

创建人物档案：

```powershell
python .\girlfriend-reply-coach\scripts\profile_store.py create `
  --slug current `
  --alias "对象"
```

如需让 Codex 和 Claude Code 共用另一个本地私密目录，可在两个 CLI 启动前设置同一个环境变量：

```powershell
$env:GIRLFRIEND_REPLY_COACH_DATA = "D:\private\girlfriend-reply-coach"
```

不要将这个目录放进 Git 仓库、云盘同步目录或公开共享位置。

### 删除档案

先预览将要删除的绝对路径并取得确认令牌：

```powershell
python .\girlfriend-reply-coach\scripts\profile_store.py preview-delete --slug current
```

确认目标无误后执行：

```powershell
python .\girlfriend-reply-coach\scripts\profile_store.py delete `
  --slug current `
  --confirm <confirmation_token>
```

删除操作会同时清理该人物的档案、派生摘要和可选原始资料，不会删除私有数据根目录中的其他人物。

## 默认输出

根据问题复杂度，Skill 会尽量压缩为以下内容：

1. 情况判断：区分事实、可信判断和未确认推测。
2. 建议你现在怎么做：一至三步可执行动作。
3. 直接回复她：一条最推荐的完整回复。
4. 为什么这样回：说明情绪、责任和档案依据。
5. 发送后的下一步：何时发送、是否等待以及如何接话。
6. 不要这样回复：当前最容易踩中的雷区。

示例：

```text
建议现在先承认没有提前说明，不要急着解释加班有多忙。

直接回复她：
“不是不想陪你，是我临时有事却没提前跟你说，这件事是我没做好。
你不高兴很正常。我先把手头情况跟你说清楚，再和你定一个我们都能做到的时间。”

发完先给她一点回应时间；如果她继续表达委屈，先听完，再讨论补救安排。
```

实际输出不会虚构你做不到的时间安排、礼物或承诺。

## 隐私与安全

- 通用 Skill 与私人数据分开保存。
- 仓库的 `.gitignore` 排除了常见私人数据目录和 Python 缓存。
- 默认不输出或保存聊天正文；只有显式提供 `--output` 才落盘。
- 人物结论必须带证据，高置信度模式需要至少两个独立情境支持。
- 新证据与旧结论冲突时保留双方，不会静默覆盖。
- 不要提交真实聊天、截图、姓名、联系方式或派生画像。
- 涉及自伤、暴力、威胁或现实危险时，应优先寻求身边可信人员和当地紧急服务帮助。

## 项目结构

```text
girlfriend-reply-coach/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── imports.md
│   ├── profile-and-privacy.md
│   └── scenarios.md
└── scripts/
    ├── import_weflow.py
    └── profile_store.py

tests/
├── behavioral-scenarios.md
├── test_import_weflow.py
├── test_profile_store.py
└── test_script_cli.py
```

## 测试

项目使用 Python 标准库 `unittest`，不需要额外测试依赖：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

当前测试覆盖：

- TXT、JSON、JSONL 解析与异常输入。
- 系统消息和媒体内容的证据隔离。
- 私密目录与 Git 工作区保护。
- 人物结论的证据、冲突和置信度规则。
- 带确认令牌的档案删除。
- 15 类典型恋爱场景的行为回放。

## 参与贡献

欢迎提交 Issue 或 Pull Request。提交测试材料时请只使用虚构、脱敏或明确授权的数据，不要上传任何真实私人聊天记录。
