---
name: create-hong
description: Use when 用户要为一个具体交往对象首次建立本地档案、导入聊天、生成独立 hong-slug 专属 Skill，或在新增资料和语气纠正后更新该专属 Skill。
---

# 创建对象专属回复 Skill

## 硬门槛

不得把 `/hong-<slug>` 当作临时对象切换命令。专属 Skill 只有在授权、聊天证据、双方映射、三份档案和用户预览确认全部完成后才能生成。缺少任一条件时列出缺项，不创建空壳 Skill，也不宣称对象已绑定。

## 创建顺序

1. 收集匿名代号和小写 slug；不要求真实姓名。
2. 让用户明确确认有权使用聊天资料。
3. 按 [imports.md](../girlfriend-reply-coach/references/imports.md) 导入 TXT、JSON、JSONL 或直接粘贴聊天；系统消息和媒体不计入文本门槛。
4. 展示发送者和文本数，让用户明确确认本人别名与对象别名；不得根据内容猜测。
5. 从本人消息建立 `self-voice.json`，从当前关系建立 `profile.json` 和 `voice-delta.json`。每项模式保留证据、置信度、适用情境和更新时间。
6. 展示对象、映射、文本数、本人语气、对象专属语气、冲突项、Skill 名称和安装目标的摘要。
7. 用户纠正时先更新档案并重新生成摘要。只有用户明确确认当前摘要后，才使用确认哈希生成。
8. 运行 `create_hong.py generate`，将薄 Skill 事务式安装到 Codex、Claude Code 或两者。

至少需要双方各一条可识别文本消息。不得仅凭手动代号生成专属 Skill。

## 本地命令

脚本位于 `girlfriend-reply-coach/scripts/create_hong.py`：

```text
prepare     写入授权、发送者映射和双方文本计数
preview     输出当前摘要与 confirmation_hash
generate    校验全部门槛并生成 hong-<slug>
mark-stale  档案变化后标记旧 Skill 需要重新生成
```

先使用 `--help` 查看精确参数。私有根目录默认位于 `~/.codex/private/girlfriend-reply-coach`，可由 `GIRLFRIEND_REPLY_COACH_DATA` 指定。不得把它放入 Git 仓库。

## 生成物

生成的 `hong-<slug>` 只有 `SKILL.md` 和 `binding.json`，不包含真实别名、聊天、档案摘要或绝对私有路径。它固定读取一个 slug，先联动 `goutoujunshi` 决定内容，再按本人语气和当前对象专属语气忠实改写。

档案缺失、版本失配或 `needs_regeneration=true` 时，专属 Skill 必须停止回复并提示重新创建或更新；不得降级、猜测或切换其他对象。

## 更新

新增聊天或收到“不像我”的纠正时，先标记旧 Skill 失效，再更新对应档案、重新预览并取得新的明确确认，最后使用 `generate --force` 事务式替换。不要直接修改薄 Skill 来掩盖档案错误。

## 隐私与安全

- 未经授权不读取或处理聊天资料。
- 不把私人资料写入公开仓库或生成 Skill。
- 不冒充对象，不模拟对象人格；只改写用户自己的回复。
- 不复现辱骂、操控、威胁、跟踪、欺骗或消息轰炸等有害习惯。
- 安全提示、责任、边界和行动不能在语气改写中被删除或弱化。
