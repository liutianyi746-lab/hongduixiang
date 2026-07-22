# 哄女朋友 Skill 实现计划

> **面向 AI 代理的工作者：** 使用 `executing-plans` 逐项完成本计划，并以复选框跟踪进度。

**目标：** 在本仓库创建本地优先的 `girlfriend-reply-coach` Skill，支持从 WeFlow TXT/JSON/JSONL 记录学习用户语气、保存经标注的关系记忆，并生成符合用户口吻的沟通建议。

**架构：** 用一个纯 Python 导入器将各格式转换为统一消息模型；从统一模型派生语气档案和关系记忆。`SKILL.md` 决定分析、边界和生成流程，脚本只承担确定性的格式解析、摘要写入与本地档案管理。

**技术栈：** Markdown Skill、Python 标准库、pytest。

---

## 文件结构

- `girlfriend-reply-coach/SKILL.md`：Skill 触发条件、完整运行流程与安全边界。
- `girlfriend-reply-coach/agents/openai.yaml`：Skill 在 Codex 中的界面元数据。
- `girlfriend-reply-coach/scripts/import_weflow.py`：TXT、JSON、JSONL 到统一消息列表的本地导入器。
- `girlfriend-reply-coach/scripts/profile_store.py`：创建、读取、更新、删除本地档案。
- `girlfriend-reply-coach/references/weflow-import.md`：受支持格式、字段映射和过滤规则。
- `girlfriend-reply-coach/references/response-rubric.md`：关系分析与语气改写的固定检查表。
- `tests/test_import_weflow.py`：导入和过滤行为的单元测试。
- `tests/test_profile_store.py`：档案写入、标注和删除的单元测试。
- `tests/fixtures/`：脱敏的 TXT、JSON、JSONL 最小样例。

### 任务 1：初始化并定义统一消息模型

**文件：**
- 创建：`girlfriend-reply-coach/SKILL.md`
- 创建：`girlfriend-reply-coach/agents/openai.yaml`
- 创建：`girlfriend-reply-coach/scripts/import_weflow.py`

- [ ] 创建 `girlfriend-reply-coach` 的标准目录与 YAML 前置元数据，名称使用 `girlfriend-reply-coach`。
- [ ] 在 `import_weflow.py` 定义 `Message(timestamp, sender, content, kind)` 和 `ImportResult(messages, skipped_count, warnings)` 数据类；`kind` 只允许 `text`、`media`、`system`。
- [ ] 实现 `normalize_message()`：去除首尾空白，缺失发送者或时间时返回跳过原因；系统提示映射为 `system`。
- [ ] 提交：`git add girlfriend-reply-coach && git commit -m "feat: scaffold girlfriend reply coach"`。

### 任务 2：以测试驱动实现 TXT 导入

**文件：**
- 创建：`tests/fixtures/weflow.txt`
- 创建：`tests/test_import_weflow.py`
- 修改：`girlfriend-reply-coach/scripts/import_weflow.py`

- [ ] 写入最小 TXT 样例，包含两位发送者、普通文本、`[表情包]`、撤回提示和加好友系统提示。
- [ ] 写失败测试：`parse_txt()` 应解析时间、发送者、正文；多行正文保持为一个消息；表情包输出 `media`；撤回和加好友提示输出 `system`。
- [ ] 运行 `python -m pytest tests/test_import_weflow.py -q`，预期导入函数不存在或测试失败。
- [ ] 用正则识别 `YYYY-MM-DD HH:MM:SS '发送者'` 的消息头并按下一个消息头切分正文；调用 `normalize_message()`。
- [ ] 再运行同一命令，预期通过。
- [ ] 提交：`git add tests/fixtures/weflow.txt tests/test_import_weflow.py girlfriend-reply-coach/scripts/import_weflow.py && git commit -m "feat: import weflow txt chats"`。

### 任务 3：实现 JSON 与 JSONL 导入适配器

**文件：**
- 创建：`tests/fixtures/weflow.json`
- 创建：`tests/fixtures/weflow.jsonl`
- 修改：`tests/test_import_weflow.py`
- 修改：`girlfriend-reply-coach/scripts/import_weflow.py`

- [ ] 写失败测试：含 `timestamp`、`sender`、`content` 的 JSON 数组和 JSONL 行应产生与 TXT 相同的统一消息；不完整记录增加警告并跳过。
- [ ] 运行 `python -m pytest tests/test_import_weflow.py -q`，预期新增案例失败。
- [ ] 实现 `parse_json()` 与 `parse_jsonl()`；字段名只接受文档中列出的候选字段，不猜测未知嵌套结构。
- [ ] 实现 `import_file(path)`，按照扩展名选择解析器，并为不支持扩展名抛出明确错误。
- [ ] 重新运行测试，预期通过。
- [ ] 提交：`git add tests/test_import_weflow.py tests/fixtures/weflow.json tests/fixtures/weflow.jsonl girlfriend-reply-coach/scripts/import_weflow.py && git commit -m "feat: import json chat exports"`。

### 任务 4：以测试驱动实现本地档案存储

**文件：**
- 创建：`tests/test_profile_store.py`
- 创建：`girlfriend-reply-coach/scripts/profile_store.py`

- [ ] 写失败测试：`create_profile(root, self_name, partner_alias)` 建立 `profiles/self-persona.md`、`relationships/current/relationship-memory.md` 和 `meta.json`。
- [ ] 写失败测试：`add_memory()` 必须拒绝不是 `事实`、`推测`、`待确认` 的标注；`delete_profile()` 只删除传入的档案根目录。
- [ ] 运行 `python -m pytest tests/test_profile_store.py -q`，预期失败。
- [ ] 实现上述函数，所有路径使用 `pathlib.Path`，在删除前解析目标并验证它位于调用方传入的档案根目录内。
- [ ] 再运行同一命令，预期通过。
- [ ] 提交：`git add tests/test_profile_store.py girlfriend-reply-coach/scripts/profile_store.py && git commit -m "feat: add local profile storage"`。

### 任务 5：编写 Skill 工作流与参考资料

**文件：**
- 修改：`girlfriend-reply-coach/SKILL.md`
- 创建：`girlfriend-reply-coach/references/weflow-import.md`
- 创建：`girlfriend-reply-coach/references/response-rubric.md`

- [ ] 在 `SKILL.md` 写明触发描述：用于关系沟通分析、哄伴侣、冲突修复、道歉和将建议改写成用户本人语气的场景。
- [ ] 定义首次使用：询问用户本人称呼、当前伴侣代号、是否保留原始文件；导入前先请用户确认发送者映射。
- [ ] 定义每次回复：情绪承接、事实/推测/未知、首选动作、1–3 条语气一致的可发送消息、分支下一步与“像我/不像我”反馈。
- [ ] 定义安全规则：本地优先、尊重拒绝、禁止骚扰与操控、危机优先安全支持。
- [ ] 在 `weflow-import.md` 记录 TXT 验证格式、JSON/JSONL 的支持字段、媒体与系统消息过滤规则；将 ChatLab、Arkme JSON、HTML 标为“待收到样例后适配”，不宣称已支持。
- [ ] 在 `response-rubric.md` 给出输出前的检查项：事实忠实、边界、语气吻合、无虚假承诺、可执行的下一步。
- [ ] 提交：`git add girlfriend-reply-coach/SKILL.md girlfriend-reply-coach/references && git commit -m "docs: define coaching workflow"`。

### 任务 6：端到端验证与 Skill 校验

**文件：**
- 修改：`tests/test_import_weflow.py`
- 修改：`tests/test_profile_store.py`
- 修改：`girlfriend-reply-coach/agents/openai.yaml`（仅在生成工具指出不一致时）

- [ ] 写端到端测试：导入 TXT 后，以指定的“我”创建档案；只把 `text` 消息交给语气摘要输入，并验证系统消息未进入该输入。
- [ ] 运行 `python -m pytest -q`，预期新增端到端测试先失败。
- [ ] 添加最小编排函数或调整现有接口，使测试通过；不在脚本中调用模型或上传内容。
- [ ] 运行 `python -m pytest -q`，预期全部通过。
- [ ] 在 Windows PowerShell 设置 `$env:PYTHONUTF8='1'` 后运行 Skill 创建器的 `quick_validate.py girlfriend-reply-coach`，预期 YAML 元数据和目录结构通过校验。
- [ ] 提交：`git add girlfriend-reply-coach tests && git commit -m "test: validate local coaching workflow"`。
