# `goutoujunshi` 语气适配联动实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 `girlfriend-reply-coach` 改为以 `goutoujunshi` 输出为默认输入的语气适配器，并提供纯改写与明确标注的低风险降级模式。

**架构：** `goutoujunshi` 独立负责情境判断和原始话术；本 skill 锁定原始话术的事实、责任、边界、承诺与行动，再应用 `self-voice.json` 和对象独立的 `voice-delta.json`。Python 档案工具只负责初始化隔离的数据结构，不实现关系判断。

**技术栈：** Markdown Skill、Python 3 标准库、`unittest`、YAML 配置。

---

## 文件结构

- 修改 `girlfriend-reply-coach/SKILL.md`：定义联动、纯改写、降级模式和语义保真规则。
- 修改 `girlfriend-reply-coach/references/profile-and-privacy.md`：记录对象专属 `voice-delta.json` 的证据与隔离规则。
- 修改 `girlfriend-reply-coach/scripts/profile_store.py`：创建人物时初始化 `voice-delta.json` 并登记清单路径。
- 修改 `tests/test_profile_store.py`：验证对象差异档案初始化与多人隔离。
- 修改 `tests/behavioral-scenarios.md`：把关系判断场景改为联动与改写保真场景。
- 修改 `README.md`：删除“本项目内置军师判断”的描述，说明三种模式和职责边界。
- 修改 `girlfriend-reply-coach/agents/openai.yaml`：默认提示改为先联动军师再按本人语气改写。

### 任务 1：对象专属语气差异档案

**文件：**
- 修改：`girlfriend-reply-coach/scripts/profile_store.py`
- 修改：`tests/test_profile_store.py`

- [ ] **步骤 1：编写失败测试**

在 `test_create_profile_keeps_private_data_outside_skill` 中断言：

```python
voice_delta = profile_dir / "voice-delta.json"
self.assertTrue(voice_delta.exists())
delta = json.loads(voice_delta.read_text(encoding="utf-8"))
self.assertEqual("current", delta["person_id"])
self.assertEqual([], delta["patterns"])
self.assertEqual("people/current/voice-delta.json", manifest["profiles"]["current"]["voice_delta_path"])
```

新增多人隔离测试，分别创建 `alice` 和 `bob`，确认两个文件路径不同且 `person_id` 不同。

- [ ] **步骤 2：运行测试并确认失败**

运行：`python -m unittest tests.test_profile_store -v`

预期：FAIL，原因是 `voice-delta.json` 尚不存在。

- [ ] **步骤 3：实现最小初始化逻辑**

在 `create_profile` 中创建：

```python
voice_delta_path = profile_dir / "voice-delta.json"
if not voice_delta_path.exists():
    _write_json(voice_delta_path, {
        "schema_version": 1,
        "person_id": safe_slug,
        "updated_at": created_at,
        "patterns": [],
        "corrections": [],
    })
```

并在 manifest 人物条目增加 `voice_delta_path`。

- [ ] **步骤 4：运行测试确认通过**

运行：`python -m unittest tests.test_profile_store -v`

预期：全部 PASS。

### 任务 2：重写 Skill 职责和行为测试

**文件：**
- 修改：`girlfriend-reply-coach/SKILL.md`
- 修改：`girlfriend-reply-coach/references/profile-and-privacy.md`
- 修改：`tests/behavioral-scenarios.md`
- 修改：`girlfriend-reply-coach/agents/openai.yaml`

- [ ] **步骤 1：先更新行为场景为失败标准**

覆盖以下场景：默认调用 `goutoujunshi`；保持道歉责任和行动不变；用户草稿只做语气改写；军师不可用时标注临时版本；对象甲乙语气不得混用；不复现操控性习惯；高风险提示不得被删除。

- [ ] **步骤 2：检查旧 Skill 与新场景冲突**

运行：

```powershell
rg -n "先判断|判断当前需要|关系动作|情况判断" girlfriend-reply-coach/SKILL.md
```

预期：匹配旧的独立判断职责，证明尚未满足新设计。

- [ ] **步骤 3：最小重写 Skill**

正文必须明确：

```markdown
默认先使用 `goutoujunshi` 获得原始话术。本 skill 只改变称呼、句长、语气词、标点、表情、亲密程度和有证据的关系专属表达。
```

并定义语义锁、三种模式、档案读取顺序、降级标记、安全边界与精简输出。

- [ ] **步骤 4：更新档案说明与默认提示**

在隐私文档加入 `people/<slug>/voice-delta.json`，明确只保存用户对该对象的表达差异。默认提示使用“先取得军师草稿，再忠实改写”的措辞。

- [ ] **步骤 5：静态验证**

运行：

```powershell
rg -n "联动模式|纯改写模式|降级模式|语义锁|voice-delta.json|未经过.*goutoujunshi" girlfriend-reply-coach tests/behavioral-scenarios.md
```

预期：所有关键规则均有匹配；`SKILL.md` 不再声称自行进行完整关系判断。

### 任务 3：README 对外说明

**文件：**
- 修改：`README.md`

- [ ] **步骤 1：定位冲突描述**

运行：

```powershell
rg -n "提取她的真实偏好|情况判断|结合关系判断工作流|参考项目|下一阶段" README.md
```

预期：找到与新职责不一致的介绍、对比表、使用示例和许可说明。

- [ ] **步骤 2：重写产品定位和用法**

开头明确“根据聊天记录学习本人及其面对指定对象的语言差异”；架构改为 `goutoujunshi → 原始话术 → hongduixiang 语气改写`；说明纯改写与降级模式；删除“参考或吸收军师资料”的表述。

- [ ] **步骤 3：更新许可与第三方关系表述**

说明本项目只在运行时与独立 skill 联动，不复制其资料；保留不隶属、不背书声明。不得据此宣称获得商业授权。

- [ ] **步骤 4：验证公开文档无真实人物信息与职责冲突**

运行：

```powershell
rg -n "私聊_|32916" README.md girlfriend-reply-coach
rg -n "参考.*goutoujunshi|内置.*goutoujunshi|结合关系判断工作流" README.md
```

预期：两条命令均无匹配。

### 任务 4：完整验证与提交

**文件：**
- 验证：`girlfriend-reply-coach/`
- 验证：`tests/`
- 验证：`README.md`

- [ ] **步骤 1：运行完整自动化测试**

运行：`python -m unittest discover -s tests -v`

预期：全部 PASS。

- [ ] **步骤 2：运行仓库检查**

运行：

```powershell
git diff --check
git status --short
```

预期：无空白错误；只有本计划列出的文件发生变化。

- [ ] **步骤 3：对照设计进行规格自检**

逐项确认三种运行模式、语义保真、多人隔离、降级提示、高风险保留、非复制联动均已覆盖。

- [ ] **步骤 4：提交实现**

```powershell
git add README.md girlfriend-reply-coach tests docs/superpowers/plans/2026-07-22-goutoujunshi-style-adapter.md
git commit -m "feat: make reply coach a style adapter"
```
