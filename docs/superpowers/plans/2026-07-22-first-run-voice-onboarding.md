# 首次使用语气建档引导实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 首次调用相关 Skill 时确定性识别本人语气档案状态，并在缺失或空壳时提供文件导入、粘贴或中性口语三选一引导。

**架构：** `profile_store.py` 只负责判定本地 `self-voice.json` 的状态并在本人语气变化后标记所有对象生成物失效；两个 `SKILL.md` 负责用户交互和授权边界；README 负责安装后使用说明。状态检查保持只读，聊天提取继续复用现有导入器和档案工作流。

**技术栈：** Python 3 标准库、JSON、`unittest`、Markdown Skill 契约测试。

---

## 文件结构

- 修改：`girlfriend-reply-coach/scripts/profile_store.py` — 本人语气档案状态检查和全对象失效标记。
- 修改：`tests/test_profile_store.py` — 缺失、空壳、有效、损坏状态与失效标记单元测试。
- 修改：`girlfriend-reply-coach/SKILL.md` — 首次调用三选一引导、中性模式标记和重新学习入口。
- 修改：`create-hong/SKILL.md` — 创建对象档案前复用本人语气首次引导。
- 修改：`tests/test_skill_contract.py` — 两个 Skill 的引导契约测试。
- 修改：`README.md` — 安装后首次调用示例。
- 修改：`tests/test_readme_contract.py` — README 首次引导契约。

### 任务 1：确定性判定本人语气档案状态

**文件：**
- 修改：`girlfriend-reply-coach/scripts/profile_store.py`
- 测试：`tests/test_profile_store.py`

- [ ] **步骤 1：编写失败的四状态测试**

在 `ProfileStoreTests` 中加入：

```python
def test_self_voice_status_distinguishes_missing_empty_valid_and_corrupt(self):
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "private-data"
        self.assertEqual("missing", module.self_voice_status(root)["status"])

        root.mkdir()
        voice = root / "self-voice.json"
        voice.write_text('{"schema_version": 1, "patterns": []}', encoding="utf-8")
        self.assertEqual("empty", module.self_voice_status(root)["status"])

        voice.write_text(
            json.dumps({"schema_version": 1, "patterns": [{"name": "短句"}]}),
            encoding="utf-8",
        )
        self.assertEqual("valid", module.self_voice_status(root)["status"])

        voice.write_text("{broken", encoding="utf-8")
        self.assertEqual("corrupt", module.self_voice_status(root)["status"])
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
python -m unittest tests.test_profile_store.ProfileStoreTests.test_self_voice_status_distinguishes_missing_empty_valid_and_corrupt -v
```

预期：`ERROR`，提示 `profile_store` 没有 `self_voice_status`。

- [ ] **步骤 3：实现最小只读状态检查**

在 `profile_store.py` 中加入：

```python
def self_voice_status(root: str | Path) -> dict[str, Any]:
    path = Path(root).resolve() / "self-voice.json"
    if not path.is_file():
        return {"status": "missing", "path": str(path), "pattern_count": 0}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "corrupt", "path": str(path), "pattern_count": 0}
    if not isinstance(value, dict) or not isinstance(value.get("patterns"), list):
        return {"status": "corrupt", "path": str(path), "pattern_count": 0}
    patterns = [item for item in value["patterns"] if isinstance(item, dict) and item]
    return {
        "status": "valid" if patterns else "empty",
        "path": str(path),
        "pattern_count": len(patterns),
    }
```

- [ ] **步骤 4：运行档案测试**

运行：

```powershell
python -m unittest tests.test_profile_store -v
```

预期：全部通过。

- [ ] **步骤 5：提交**

```powershell
git add girlfriend-reply-coach/scripts/profile_store.py tests/test_profile_store.py
git commit -m "feat: detect first-run voice profile state"
```

### 任务 2：本人语气更新后使所有对象 Skill 失效

**文件：**
- 修改：`girlfriend-reply-coach/scripts/profile_store.py`
- 测试：`tests/test_profile_store.py`

- [ ] **步骤 1：编写失败的全对象失效测试**

```python
def test_mark_all_generated_profiles_stale_updates_every_generation_file(self):
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "private-data"
        for slug in ("alice", "bob"):
            profile = module.create_profile(root, slug, slug)
            generation = json.loads((profile / "generation.json").read_text(encoding="utf-8"))
            generation["needs_regeneration"] = False
            (profile / "generation.json").write_text(json.dumps(generation), encoding="utf-8")

        changed = module.mark_all_generated_profiles_stale(root)

        self.assertEqual(["alice", "bob"], changed)
        for slug in changed:
            generation = json.loads(
                (root / "people" / slug / "generation.json").read_text(encoding="utf-8")
            )
            self.assertTrue(generation["needs_regeneration"])
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
python -m unittest tests.test_profile_store.ProfileStoreTests.test_mark_all_generated_profiles_stale_updates_every_generation_file -v
```

预期：`ERROR`，提示函数不存在。

- [ ] **步骤 3：实现限定在私有根目录内的失效标记**

```python
def mark_all_generated_profiles_stale(root: str | Path) -> list[str]:
    root_path = Path(root).resolve()
    _ensure_private_root(root_path)
    changed = []
    people = root_path / "people"
    if not people.is_dir():
        return changed
    for person in sorted(path for path in people.iterdir() if path.is_dir()):
        generation_path = person / "generation.json"
        if not generation_path.is_file():
            continue
        generation = json.loads(generation_path.read_text(encoding="utf-8"))
        generation["needs_regeneration"] = True
        _write_json(generation_path, generation)
        changed.append(person.name)
    return changed
```

损坏的 `generation.json` 必须抛出明确的 JSON 错误，不能被覆盖。

- [ ] **步骤 4：运行档案测试**

运行：

```powershell
python -m unittest tests.test_profile_store -v
```

预期：全部通过。

- [ ] **步骤 5：提交**

```powershell
git add girlfriend-reply-coach/scripts/profile_store.py tests/test_profile_store.py
git commit -m "feat: invalidate bound skills after voice updates"
```

### 任务 3：加入首次调用交互契约

**文件：**
- 修改：`girlfriend-reply-coach/SKILL.md`
- 修改：`create-hong/SKILL.md`
- 测试：`tests/test_skill_contract.py`

- [ ] **步骤 1：编写失败的 Skill 契约测试**

```python
def test_first_run_offers_import_paste_or_neutral_voice(self):
    coach = SKILL.read_text(encoding="utf-8")
    creator = CREATOR_SKILL.read_text(encoding="utf-8")
    for required in (
        "self_voice_status",
        "导入 TXT / JSON / JSONL 聊天记录",
        "直接粘贴几段聊天",
        "暂时跳过，使用自然的中性口语",
        "本次未使用个人语气档案",
        "重新学习我的语气",
    ):
        self.assertIn(required, coach)
    self.assertIn("self_voice_status", creator)
    self.assertIn("不得因为本人语气档案有效而跳过对象建档", creator)
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
python -m unittest tests.test_skill_contract.SkillContractTests.test_first_run_offers_import_paste_or_neutral_voice -v
```

预期：`FAIL`，缺少首次引导文案。

- [ ] **步骤 3：在通用教练中加入首次引导**

在 `girlfriend-reply-coach/SKILL.md` 增加“首次使用”节，要求：

```text
调用 `profile_store.self_voice_status`。missing 或 empty 时提供三项选择：
1. 导入 TXT / JSON / JSONL 聊天记录
2. 直接粘贴几段聊天
3. 暂时跳过，使用自然的中性口语

选择 3 后继续当前任务，并在输出前标注“本次未使用个人语气档案”。
corrupt 时停止个性化并提示修复，不覆盖文件。
valid 时不重复显示向导。
“重新学习我的语气”会重新导入，并调用 mark_all_generated_profiles_stale。
```

- [ ] **步骤 4：在创建器中复用同一状态门槛**

在 `create-hong/SKILL.md` 的创建顺序前加入状态检查；缺失或空壳时显示同一三选一引导。选择跳过可以完成普通回复，但不能生成 `hong-<slug>`，因为生成门槛仍要求有效 `self-voice.json`。明确写入“不得因为本人语气档案有效而跳过对象建档”。

- [ ] **步骤 5：运行契约测试**

运行：

```powershell
python -m unittest tests.test_skill_contract -v
```

预期：全部通过。

- [ ] **步骤 6：提交**

```powershell
git add girlfriend-reply-coach/SKILL.md create-hong/SKILL.md tests/test_skill_contract.py
git commit -m "feat: guide first-run voice onboarding"
```

### 任务 4：记录安装后的实际使用体验

**文件：**
- 修改：`README.md`
- 修改：`tests/test_readme_contract.py`

- [ ] **步骤 1：编写失败的 README 契约测试**

```python
def test_readme_documents_first_run_voice_onboarding(self):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for required in (
        "首次调用",
        "导入 TXT / JSON / JSONL 聊天记录",
        "直接粘贴几段聊天",
        "暂时跳过，使用自然的中性口语",
        "本次未使用个人语气档案",
        "重新学习我的语气",
    ):
        self.assertIn(required, text)
```

- [ ] **步骤 2：运行测试并确认失败**

运行：

```powershell
python -m unittest tests.test_readme_contract.ReadmeContractTests.test_readme_documents_first_run_voice_onboarding -v
```

预期：`FAIL`，README 尚未包含完整引导。

- [ ] **步骤 3：更新 README**

在“先建档”章节前增加“安装后的首次调用”，展示三选一界面；说明安装时不会自动弹窗、有效档案不重复提示、跳过只影响当前回复、创建对象专属 Skill 仍需要完整档案门槛，以及“重新学习我的语气”的入口。

- [ ] **步骤 4：运行 README 契约和完整测试**

运行：

```powershell
python -m unittest tests.test_readme_contract -v
python -m unittest discover -s tests -p "test_*.py" -v
```

预期：所有测试通过。

- [ ] **步骤 5：校验 Skill 和差异**

运行：

```powershell
$env:PYTHONUTF8 = "1"
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" create-hong
python "$HOME\.codex\skills\.system\skill-creator\scripts\quick_validate.py" girlfriend-reply-coach
python -m py_compile girlfriend-reply-coach/scripts/profile_store.py
git diff --check
```

预期：两个 Skill 均显示 `Skill is valid!`，Python 编译成功，`git diff --check` 无错误。

- [ ] **步骤 6：提交**

```powershell
git add README.md tests/test_readme_contract.py
git commit -m "docs: explain first-run voice onboarding"
```
