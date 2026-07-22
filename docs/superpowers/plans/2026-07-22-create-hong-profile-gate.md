# `create-hong` 建档门槛与薄 Skill 生成实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现只有在授权、双方映射、三份档案和摘要确认全部有效后，才生成并安装独立 `hong-<slug>` 薄 Skill 的本地工作流。

**架构：** 新增纯 Python `create_hong.py`，将档案校验、版本哈希、模板渲染和事务安装拆成可测试函数。`profile_store.py` 负责私有档案初始化与 generation 状态；生成物只含 `SKILL.md` 和 `binding.json`，运行时固定绑定一个 slug。

**技术栈：** Python 3 标准库、JSON、SHA-256、`pathlib`、`unittest`、Markdown Skill。

---

### 任务 1：档案状态与生成门槛

**文件：**
- 创建：`girlfriend-reply-coach/scripts/create_hong.py`
- 创建：`tests/test_create_hong.py`
- 修改：`girlfriend-reply-coach/scripts/profile_store.py`

- [ ] 编写失败测试：合法 slug、保留字、授权、非重叠双方映射、双方文本计数、三份档案结构、确认摘要哈希；一次返回所有缺失条件。
- [ ] 运行 `python -m unittest tests.test_create_hong.ProfileGateTests -v`，确认因模块或函数缺失失败。
- [ ] 实现 `validate_slug()`、`profile_version()`、`summary_hash()`、`generation_issues()`；扩展 `create_profile()` 初始化授权、映射、文本计数和 `generation.json` 的未确认状态。
- [ ] 运行目标测试，预期全部通过。
- [ ] 提交：`git commit -m "feat: enforce profile gate before hong generation (task 1/4)"`。

### 任务 2：薄 Skill 渲染与隐私约束

**文件：**
- 修改：`girlfriend-reply-coach/scripts/create_hong.py`
- 修改：`tests/test_create_hong.py`

- [ ] 编写失败测试：合法档案生成 `SKILL.md` 和 `binding.json`；固定 slug、要求 `goutoujunshi`、版本校验和拒绝降级；生成物不含聊天正文、真实别名、档案摘要或绝对私有路径。
- [ ] 运行 `python -m unittest tests.test_create_hong.ThinSkillTests -v`，确认函数缺失失败。
- [ ] 实现 `render_thin_skill()` 与 `write_thin_skill()`，binding 只含 schema、slug、profile version 和私有根目录解析规则。
- [ ] 运行目标测试，预期全部通过。
- [ ] 提交：`git commit -m "feat: render privacy-safe bound hong skills (task 2/4)"`。

### 任务 3：双端事务安装与生成记录

**文件：**
- 修改：`girlfriend-reply-coach/scripts/create_hong.py`
- 修改：`tests/test_create_hong.py`

- [ ] 编写失败测试：`codex`、`claude`、`both` 路径；默认冲突零写入；强制覆盖中途失败恢复旧目录；成功后 `generation.json` 记录路径、版本和 `needs_regeneration=false`。
- [ ] 运行 `python -m unittest tests.test_create_hong.GeneratedInstallTests -v`，确认失败。
- [ ] 实现 `generated_targets()`、`install_generated_skill()`、`generate_for_profile()`，复用同级临时目录和备份的事务模式。
- [ ] 添加 CLI：`prepare` 写入授权/映射/计数，`preview` 输出摘要与哈希，`generate` 必须接收用户确认哈希，`mark-stale` 标记需重新生成。
- [ ] 运行 `python -m unittest tests.test_create_hong -v`，预期全部通过。
- [ ] 提交：`git commit -m "feat: install generated hong skills transactionally (task 3/4)"`。

### 任务 4：创建器 Skill 与文档

**文件：**
- 创建：`create-hong/SKILL.md`
- 创建：`create-hong/agents/openai.yaml`
- 修改：`install.py`
- 修改：`README.md`
- 修改：`girlfriend-reply-coach/SKILL.md`
- 修改：`tests/test_skill_contract.py`
- 修改：`tests/test_readme_contract.py`
- 修改：`tests/test_installer.py`

- [ ] 先写失败契约测试：安装器同时安装 `create-hong`；README 规定先建档再调用；`girlfriend-reply-coach` 不允许未建档对象降级；创建器列出授权、导入、映射、预览、确认、生成顺序。
- [ ] 运行相关测试确认失败。
- [ ] 编写 `create-hong` Skill，更新安装器固定 Skill 列表、README 命令与底层适配器硬门槛。
- [ ] 运行 `python -m unittest discover -s tests -v`、`python girlfriend-reply-coach/scripts/create_hong.py --help`、`git diff --check`。
- [ ] 确认全套测试通过、帮助包含 `prepare/preview/generate/mark-stale`，工作区只含计划内文件。
- [ ] 提交：`git commit -m "docs: add create-hong profile-first workflow (task 4/4)"`。
