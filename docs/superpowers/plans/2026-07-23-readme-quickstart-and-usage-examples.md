# README 小白上手与日常示例实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在 README 开头增加可复制的“5 分钟上手”，并补齐 `/hong-xiaoyu` 日常调用和“不像我”后的完整更新示例。

**架构：** 仅修改用户文档和 README 契约测试，不改变 Skill 或脚本行为。开头教程负责从安装到第一次成功调用；现有“先建档”章节负责更详细的日常调用与重新学习流程。

**技术栈：** Markdown、Python 标准库 `unittest`。

---

## 文件结构

- 修改：`tests/test_readme_contract.py` — 锁定小白教程、双端调用、日常聊天和重新学习流程。
- 修改：`README.md` — 添加“5 分钟上手”和两类完整示例。

### 任务 1：建立 README 内容契约

**文件：**
- 修改：`tests/test_readme_contract.py`

- [ ] **步骤 1：编写失败的契约测试**

在 `ReadmeContractTests` 中加入：

```python
def test_readme_has_beginner_quickstart_and_daily_usage_examples(self):
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for required in (
        "## 5 分钟上手",
        "安装完成后重新启动",
        "Codex 中输入",
        "Claude Code 中输入",
        "/hong-xiaoyu 她说：",
        "多轮聊天也可以直接粘贴",
        "这句不像我",
        "重新学习我的语气",
        "重新预览并确认",
        "generate --force",
    ):
        self.assertIn(required, text)
```

- [ ] **步骤 2：运行测试确认正确失败**

运行：

```powershell
& 'C:\Users\32916\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m unittest tests.test_readme_contract.ReadmeContractTests.test_readme_has_beginner_quickstart_and_daily_usage_examples -v
```

预期：`FAIL`，首先缺少 `## 5 分钟上手`。

- [ ] **步骤 3：提交红灯测试**

```powershell
git add tests/test_readme_contract.py
git commit -m "test: require beginner README usage examples"
```

### 任务 2：编写 5 分钟上手与完整示例

**文件：**
- 修改：`README.md`
- 测试：`tests/test_readme_contract.py`

- [ ] **步骤 1：在 README 开头添加“5 分钟上手”**

在安全提示之后、`## 功能` 之前加入八个短步骤：

```markdown
## 5 分钟上手

### 1. 安装
### 2. 重新启动
### 3. 首次创建本人语气
### 4. 导入或粘贴聊天
### 5. 确认发送者
### 6. 预览并生成 hong-xiaoyu
### 7. 开始使用
### 8. 不像我时更新
```

安装命令使用 `git clone` 和 `python install.py --target both`；Codex 使用自然语言 `使用 create-hong...`，Claude Code 使用 `/create-hong...`。解释每一步预期结果，但不在快速上手中展开底层 JSON 和哈希算法。

- [ ] **步骤 2：添加单句与多轮聊天调用示例**

在现有 `/hong-xiaoyu` 生成流程后加入：

```text
/hong-xiaoyu 她说：“算了，你忙吧。”
```

以及：

```text
/hong-xiaoyu

小雨：你忙吧
我：怎么了
小雨：没怎么，不用管我
```

说明默认只输出一条可直接发送的回复，并重申必须先完成对象建档。

- [ ] **步骤 3：添加“不像我”的完整更新示例**

加入以下用户入口和顺序：

```text
/hong-xiaoyu 这句不像我。我不会说“我在听”，我一般会说“你跟我讲嘛”。
重新学习我的语气
```

文档必须说明：重新取得聊天授权、导入或粘贴、确认本人发送者、更新本人语气、把依赖旧语气的对象 Skill 标记为失效、重新预览并确认，最后使用：

```powershell
python .\girlfriend-reply-coach\scripts\create_hong.py generate `
  --slug xiaoyu --confirm-hash <new_confirmation_hash> --target both --force
```

- [ ] **步骤 4：运行契约测试和全量测试**

运行：

```powershell
& 'C:\Users\32916\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m unittest tests.test_readme_contract -v
& 'C:\Users\32916\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m unittest discover -s tests -p 'test_*.py' -v
```

预期：README 契约和全部测试通过。

- [ ] **步骤 5：检查格式与隐私**

运行：

```powershell
git diff --check
rg -n -i "daijia|呆佳|32916|私聊_" README.md
```

预期：`git diff --check` 无错误；隐私扫描无匹配。

- [ ] **步骤 6：提交**

```powershell
git add README.md
git commit -m "docs: add beginner quickstart and usage examples"
```
