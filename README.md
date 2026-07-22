# hongduixiang

一个面向 Codex 和 Claude Code CLI 的个性化回复语气 Skill。

不再套用千篇一律的口吻。hongduixiang 可以从经授权的聊天记录中学习你的通用说话习惯，以及你面对指定对象时特有的称呼、句长、语气词、标点、表情和亲密程度，再把已有恋爱建议忠实改写成更像你本人会发送的回复。

> 这个项目帮助你更诚实、清楚地沟通，不用于操控、监视、冒充或替代真实关系中的交流。

## 功能

- 默认联动独立的 `goutoujunshi` Skill 获取情境判断和原始话术。
- 忠实改写军师话术或用户提供的草稿，不改变事实、责任、边界、承诺和行动。
- 根据聊天证据学习你的句长、称呼、标点、表情和亲密程度。
- 为每个对象建立独立的关系专属语气差异，避免多人资料混用。
- 军师不可用时可提供明确标注的低风险临时回复。
- 支持 WeFlow 导出的 TXT、JSON 和 JSONL 聊天记录。
- 私人画像默认保存在 Git 仓库之外，并提供带确认令牌的删除流程。
- 拒绝 PUA、情绪勒索、秘密监控、威胁、跟踪和绕过拒绝等请求。

## 工作方式

```text
当前聊天与背景
        ↓
goutoujunshi：判断情境、决定策略、生成原始话术
        ↓
语义锁：事实、责任、边界、承诺、行动、安全提示
        ↓
hongduixiang：本人通用语气 + 当前对象专属语气差异
        ↓
可直接发送的个性化回复
```

用户已经有草稿时，也可以跳过军师，仅做语气改写。没有军师草稿时允许降级生成普通回复，但会标注“未经过 `goutoujunshi` 情境分析”。没有语气档案时使用自然、简短、无专属称呼的中性口语。

## 为什么采用联动而不是复制

两个 Skill 保持独立职责：

- [`goutoujunshi`](https://github.com/powerycy/goutoujunshi) 独立负责“**说什么**”：关系判断、沟通策略和原始话术。
- `hongduixiang` 只负责“**怎么用你的方式说**”：根据本人语气和当前对象的关系专属语气进行忠实改写。
- 用户也可以提供自己的草稿，直接进入纯改写模式。

本仓库不复制、改编或内置 `goutoujunshi` 的理论资料和话术库。运行时联动让军师可以独立升级，也能避免语气适配器越权改变原意。

| 对比维度 | 通用聊天机器人 | 固定哄人话术库 | 纯语气模仿 | 单一恋爱军师 | 本项目 |
| --- | --- | --- | --- | --- | --- |
| 当前情境判断 | 依赖临时提示 | 基本没有 | 通常没有 | 强项 | 由联动的 `goutoujunshi` 负责 |
| 对象个性化 | 上下文内临时使用 | 通常没有 | 可能只有表面措辞 | 依赖问卷或当前叙述 | 使用独立的对象语气差异档案 |
| 用户本人语气 | 容易生成通用口吻 | 固定模板口吻 | 强项 | 通常不是重点 | 只采用档案支持的称呼、句长和表达习惯 |
| 语义保真 | 取决于提示是否充分 | 没有 | 容易只追求相似 | 负责原始含义 | 锁定事实、责任、边界、承诺和行动后再改写 |
| 持续纠正 | 多依赖当前会话 | 没有 | 可修改样例 | 可补充关系信息 | 区分通用语气与对象专属语气后更新 |
| 行动与后续 | 不一定稳定提供 | 通常只有一句话 | 通常只有一句话 | 强项 | 不增删军师给出的行动和后续安排 |
| 隐私设计 | 取决于所用服务 | 通常不处理数据 | 取决于实现 | 取决于实现 | 私人数据与 Git 分离，默认本地、最小化和可删除 |

这些是设计能力上的差异，不代表某条回复一定能消除冲突、挽回关系或改变对方。Skill 不能替代真实沟通，也不会把拒绝当成需要破解的障碍。

## 安装后的首次调用

安装过程不会自动打开对话。第一次调用 `girlfriend-reply-coach` 或 `create-hong` 时，Skill 会检查本地本人语气档案；如果档案不存在或还是空壳，会主动显示：

```text
还没有你的语气档案。建立后，我可以根据聊天记录学习你的称呼、句长、语气词、标点和表情习惯。

请选择：
1. 导入 TXT / JSON / JSONL 聊天记录
2. 直接粘贴几段聊天
3. 暂时跳过，使用自然的中性口语
```

选择文件或粘贴内容后，需要先确认你有权使用资料，再确认聊天中的本人发送者；系统不会根据内容猜测身份。档案有效后不再重复显示向导。

选择跳过时仍可继续当前普通回复，但会标注：

```text
本次未使用个人语气档案。
```

跳过不会伪造语气档案，也不能用来生成对象专属 `hong-<slug>`。以后可以直接说“重新学习我的语气”再次进入导入流程；本人语气更新后，依赖旧档案的对象 Skill 需要重新预览确认和生成。

## 先建档，再生成每个人的专属 Skill

个性化不是在命令后临时写一个名字。每个对象都必须先通过 `create-hong` 建立独立档案库，再生成绑定该档案的 `/hong-<slug>`。系统会分别提取用户本人的通用语气、当前对象的可观察互动模式，以及用户只对这个对象使用的称呼和表达习惯。

```text
聊天记录
   ├── 对象档案：她的可观察偏好、雷区与互动模式
   ├── 本人通用语气：相对稳定的句长、标点与表达习惯
   └── 关系专属语气：你只对这个人使用的称呼和亲密表达
                    ↓
             hong-<对象代号>
```

完整流程如下：

```text
/create-hong xiaoyu
        ↓
确认有权使用聊天记录并导入 TXT / JSON / JSONL / 粘贴内容
        ↓
确认“谁是本人、谁是对象”（不根据聊天内容猜测）
        ↓
生成 self-voice.json、profile.json、voice-delta.json
        ↓
预览摘要与 confirmation_hash，用户明确确认
        ↓
生成并安装 /hong-xiaoyu
```

至少需要双方各一条可识别的文本消息，并且必须确认发送者映射。缺少授权、聊天证据、映射、三份档案或确认中的任何一项，都不会创建空壳 Skill。不得把 `/hong-<slug>` 当作临时对象切换命令；未创建时必须先运行 `create-hong`，不能用普通回复冒充个性化结果。

生成的薄 Skill 不含真实姓名、聊天正文、画像摘要或私人目录绝对路径，只保存匿名 slug 和档案版本绑定。新增聊天或收到“不像我”的纠正后，旧 Skill 会被标记为需要重新生成，必须再次预览确认。聊天中的 `<img src="file://...">` 只作为媒体占位处理，本地绝对路径会被移除且不会自动打开。

在 Codex 或 Claude Code 中，直接说“使用 `create-hong` 为 xiaoyu 建档”即可由 Skill 引导。底层脚本也可以手动运行：

```powershell
python .\girlfriend-reply-coach\scripts\create_hong.py prepare `
  --slug xiaoyu --alias "对象代号" `
  --self-alias "聊天中的本人昵称" --partner-alias "聊天中的对象昵称" `
  --self-count 20 --partner-count 18 --authorized

python .\girlfriend-reply-coach\scripts\create_hong.py preview --slug xiaoyu

python .\girlfriend-reply-coach\scripts\create_hong.py generate `
  --slug xiaoyu --confirm-hash <confirmation_hash> --target both
```

`prepare` 记录授权、发送者映射和已导入文本数；语气与人物档案仍需根据实际导入结果建立，不能用虚构计数代替聊天证据。

## 安装

先克隆仓库：

```powershell
git clone https://github.com/liutianyi746-lab/hongduixiang.git
cd hongduixiang
```

### 一键安装三个基础 Skill（推荐）

同时安装到 Codex 和 Claude Code：

```powershell
python install.py --target both
```

只安装到 Codex：

```powershell
python install.py --target codex
```

只安装到 Claude Code：

```powershell
python install.py --target claude
```

安装器会复制本仓库的 `girlfriend-reply-coach` 和 `create-hong`，并从官方仓库
[`powerycy/goutoujunshi`](https://github.com/powerycy/goutoujunshi)
浅克隆独立的 `goutoujunshi`。它会校验三个 `SKILL.md` 后再写入目标目录，不会执行第三方仓库中的脚本。

如果任意目标已经存在，默认会在写入前停止，避免出现只安装一半的状态。确认需要同时覆盖所有已有版本时使用：

```powershell
python install.py --target both --force
```

`--force` 会先创建本地备份；任一复制步骤失败时自动恢复所有旧目录。安装完成后请重新启动 Codex、Codex App 或 Claude Code。

> `goutoujunshi` 是独立第三方项目，本项目未获其官方背书。它使用 PolyForm Noncommercial License 1.0.0；使用联动功能时仍须遵守其许可证。

### 手动安装（故障排查）

手动安装时必须分别安装三个基础 Skill。先将 `girlfriend-reply-coach` 和 `create-hong` 复制到相应目录，再从 `https://github.com/powerycy/goutoujunshi` 获取 `goutoujunshi` 并把其 Skill 目录复制到同一 `skills` 目录下。不要把第三方源码提交进本仓库。

#### Codex CLI / Codex App

本项目 Skill 的手动复制命令：

```powershell
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\girlfriend-reply-coach" "$HOME\.codex\skills\girlfriend-reply-coach"
Copy-Item -Recurse -Force ".\create-hong" "$HOME\.codex\skills\create-hong"
```

最终应同时存在：

```text
~/.codex/skills/girlfriend-reply-coach/SKILL.md
~/.codex/skills/create-hong/SKILL.md
~/.codex/skills/goutoujunshi/SKILL.md
```

在 Codex 中直接提及 Skill 名称即可：

```text
先使用 goutoujunshi 分析下面的聊天并生成原始回复，
再使用 girlfriend-reply-coach，按我对“小雨”的说话习惯忠实改写。
聊天：她说：“算了，你忙吧。”
```

也可以提供更多上下文：

```text
使用 girlfriend-reply-coach，纯改写模式。
对象：小雨
草稿：刚才是我没提前告诉你，让你一直等。这件事是我没做好，对不起。
要求：只改成我的语气，不改变责任和原意。
```

#### Claude Code CLI

Claude Code 支持相同的 `SKILL.md` 结构。本项目 Skill 的手动复制命令：

```powershell
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force ".\girlfriend-reply-coach" "$HOME\.claude\skills\girlfriend-reply-coach"
Copy-Item -Recurse -Force ".\create-hong" "$HOME\.claude\skills\create-hong"
```

最终应同时存在：

```text
~/.claude/skills/girlfriend-reply-coach/SKILL.md
~/.claude/skills/create-hong/SKILL.md
~/.claude/skills/goutoujunshi/SKILL.md
```

启动 Claude Code：

```powershell
claude
```

然后通过斜杠命令调用：

```text
/goutoujunshi 分析下面的聊天并生成原始回复；再用 /girlfriend-reply-coach 按我对“对象甲”的语气忠实改写
```

也可以直接用自然语言描述问题，让 Claude 在匹配到 Skill 描述时自动加载：

```text
草稿是“这次是我忘记了，对不起，我会认真补救”。请使用 girlfriend-reply-coach 纯改写，不改变责任和承诺。
```

Claude Code 也支持把 Skill 放在项目级目录 `.claude/skills/girlfriend-reply-coach/`。个人目录适用于所有项目，项目目录只对当前项目生效。详见 [Claude Code Skills 官方文档](https://code.claude.com/docs/en/slash-commands)。

## 导入 WeFlow 聊天记录

导入前，请确认你有权使用相关聊天资料，并尊重聊天参与者的隐私。

兼容格式：

- WeFlow TXT
- 普通 JSON
- JSONL
- 常见 ChatLab、Arkme JSON 字段结构

这里的 WeFlow 支持仅指兼容用户自行导出的数据格式。本项目不包含 WeFlow 代码，也不隶属于或代表 WeFlow。

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
├── people/<slug>/
│   ├── profile.json
│   └── voice-delta.json
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

## 三种使用模式

### 联动模式（默认）

先由 `goutoujunshi` 生成原始话术，再由本 Skill 锁定原意并改写语气。默认只输出一条可直接发送的回复。

### 纯改写模式

提供自己的草稿。本 Skill 只调整称呼、句长、语气词、标点、表情和有证据的关系专属表达。

### 降级模式

军师不可用且没有草稿时，允许生成简短的普通临时回复。输出会明确标记：

```text
临时版本：未经过 goutoujunshi 情境分析。
```

复杂冲突、重大决定和现实安全风险不会使用降级回复代替完整判断。

联动示例：

```text
goutoujunshi 原始话术：
“刚才是我没有提前说明，让你一直等。这件事是我没做好，对不起。”

hongduixiang 改写：
“刚刚是我没提前跟你说，让你一直等我，这个确实是我没做好，对不起。”
```

改写只改变表达形式，不会删除道歉、改变责任或虚构用户做不到的安排。

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
    ├── create_hong.py
    ├── import_weflow.py
    └── profile_store.py

create-hong/
├── SKILL.md
└── agents/openai.yaml

tests/
├── behavioral-scenarios.md
├── style-adapter-scenarios.md
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
- 15 类旧版恋爱教练场景的历史行为回放。
- 联动、纯改写、降级、语义保真和多人隔离的契约测试。

## 来源与许可

本项目是独立项目，不隶属于、不代表，也未获得 `goutoujunshi`、`create-ex` 或 WeFlow 的官方背书。

本项目在运行时与独立安装的 `goutoujunshi` 联动，不复制、改编或内置其理论资料和话术库。`goutoujunshi` 自身使用 PolyForm Noncommercial License 1.0.0；使用联动功能时仍需分别遵守其许可证。本仓库没有通过一份总许可证授予任何第三方项目的额外权利，商业使用前请分别确认适用许可。

详细归属、Required Notice、WeFlow 格式兼容边界及许可证原文见：

- [第三方项目与许可声明](THIRD_PARTY_NOTICES.md)
- [goutoujunshi — PolyForm Noncommercial License 1.0.0](licenses/goutoujunshi-PolyForm-Noncommercial-1.0.0.txt)
- [create-ex — MIT License](licenses/create-ex-MIT.txt)

## 参与贡献

欢迎提交 Issue 或 Pull Request。提交测试材料时请只使用虚构、脱敏或明确授权的数据，不要上传任何真实私人聊天记录。
