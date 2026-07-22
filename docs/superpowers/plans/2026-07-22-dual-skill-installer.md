# 双 Skill 安装器实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 创建跨平台 `install.py`，一次将 `girlfriend-reply-coach` 与官方 `goutoujunshi` 安装到 Codex、Claude Code 或两者，并支持无半完成状态的强制覆盖。

**架构：** 安装器先计算并预检全部目标，再浅克隆和校验第三方 Skill，最后通过同级临时目录、备份与重命名完成事务式复制。文件系统与 Git 调用封装成可注入函数，测试使用临时 home 和本地假源，不访问真实用户目录或网络。

**技术栈：** Python 3 标准库、`argparse`、`pathlib`、`subprocess`、`tempfile`、`shutil`、`unittest`。

---

## 文件结构

- 创建 `install.py`：命令解析、目标规划、下载校验、事务式安装和错误输出。
- 创建 `tests/test_installer.py`：目标选择、冲突、强制覆盖、回滚和来源校验测试。
- 修改 `tests/test_readme_contract.py`：验证一键安装命令与许可提示。
- 修改 `README.md`：一键安装优先，保留双 Skill 手动安装说明。

### 任务 1：目标规划与来源校验

**文件：**
- 创建：`install.py`
- 创建：`tests/test_installer.py`

- [ ] **步骤 1：编写失败测试**

测试 `installation_targets(home, target)` 为 `codex`、`claude` 和 `both` 返回固定 Skill 名称的 2、2、4 个目标；测试 `find_goutoujunshi_skill()` 接受根目录或 `goutoujunshi/` 子目录，拒绝缺少 `SKILL.md` 或 frontmatter 名称错误。

```python
self.assertEqual(
    home / ".codex/skills/goutoujunshi",
    module.installation_targets(home, "codex")["codex:goutoujunshi"],
)
with self.assertRaisesRegex(module.InstallError, "name"):
    module.find_goutoujunshi_skill(bad_repo)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m unittest tests.test_installer.InstallerPlanningTests -v`

预期：FAIL，原因是 `install.py` 或目标函数不存在。

- [ ] **步骤 3：实现最小规划与校验**

实现 `InstallError`、`installation_targets(home, target)`、`find_goutoujunshi_skill(repo_root)` 和只读取 frontmatter `name` 的 `_skill_name(path)`。目标仅允许 `codex`、`claude`、`both`。

- [ ] **步骤 4：运行测试并提交**

运行：`python -m unittest tests.test_installer.InstallerPlanningTests -v`

预期：全部 PASS。

提交：`git commit -m "feat: plan and validate dual skill installs (task 1/3)"`

### 任务 2：事务式安装、覆盖和回滚

**文件：**
- 修改：`install.py`
- 修改：`tests/test_installer.py`

- [ ] **步骤 1：编写失败测试**

使用临时 home、本地 `girlfriend-reply-coach` 源和本地合法 `goutoujunshi` 源测试：正常安装、任一冲突时零写入、`force=True` 覆盖、第二个目标复制失败时恢复全部旧目录。

```python
with self.assertRaisesRegex(module.InstallError, "已存在"):
    module.install_sources(local, goutou, targets, force=False)
self.assertEqual("old", existing_marker.read_text(encoding="utf-8"))
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m unittest tests.test_installer.TransactionalInstallTests -v`

预期：FAIL，原因是 `install_sources` 不存在。

- [ ] **步骤 3：实现事务式复制**

实现：全量冲突预检；同级 `.installing-<uuid>` 临时目录；`--force` 时 `.backup-<uuid>` 备份；全部成功后清理备份；异常时删除新目标并恢复备份。只接受 `installation_targets` 产生的两个固定 Skill 名称。

- [ ] **步骤 4：实现下载与 CLI**

实现 `clone_goutoujunshi(repo_url, destination, runner=subprocess.run)`，执行 `git clone --depth 1` 并把 stderr 摘要包装为 `InstallError`。`main()` 在任何写入前完成目标冲突、本地源、Git 下载和第三方源校验；成功列出路径，失败返回 1。

- [ ] **步骤 5：运行测试并提交**

运行：`python -m unittest tests.test_installer -v`

预期：全部 PASS。

提交：`git commit -m "feat: install both skills transactionally (task 2/3)"`

### 任务 3：README、契约和完整验证

**文件：**
- 修改：`README.md`
- 修改：`tests/test_readme_contract.py`

- [ ] **步骤 1：先写失败的 README 契约测试**

断言 README 包含 `python install.py --target codex`、`claude`、`both`、`--force`、官方仓库地址和 `PolyForm Noncommercial License 1.0.0`。

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m unittest tests.test_readme_contract -v`

预期：FAIL，缺少一键安装命令。

- [ ] **步骤 3：重写安装章节**

将 `python install.py --target both` 放在首选位置，分别给出 Codex 和 Claude Code 命令，解释默认不覆盖与 `--force`。手动安装部分明确两个 Skill 要分别复制/克隆，且第三方 Skill 受其许可证约束。

- [ ] **步骤 4：运行完整验证**

运行：

```text
python -m unittest discover -s tests -v
python install.py --help
git diff --check
git status --short
```

预期：全部测试 PASS；帮助中出现三个 target 和 `--force`；无空白错误；只有计划文件发生变化。

- [ ] **步骤 5：提交**

提交：`git commit -m "docs: add dual skill installation guide (task 3/3)"`
