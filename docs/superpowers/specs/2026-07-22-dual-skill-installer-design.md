# `hongduixiang` 与 `goutoujunshi` 双 Skill 安装器设计

## 目标

提供一个仅依赖 Python 标准库的跨平台安装器。用户运行一次命令，即可把本仓库的 `girlfriend-reply-coach` 和官方仓库中的独立 `goutoujunshi` 同时安装到 Codex、Claude Code 或两者的个人 Skills 目录。

安装器只负责获取、校验和复制两个独立 Skill，不把 `goutoujunshi` 提交、打包或内置到本仓库。

## 命令接口

入口位于仓库根目录：

```text
python install.py --target codex
python install.py --target claude
python install.py --target both
```

参数：

- `--target {codex,claude,both}`：必填，决定安装目标。
- `--force`：可选，允许替换已存在的同名 Skill 目录。
- `--goutoujunshi-repo URL`：测试和高级用户可选，默认使用 `https://github.com/powerycy/goutoujunshi.git`。

不提供静默覆盖。未传 `--force` 时，只要任一目标目录已存在，安装器应在改变任何目标前失败并列出冲突路径，避免部分安装。

## 安装位置

- Codex：`~/.codex/skills/girlfriend-reply-coach` 与 `~/.codex/skills/goutoujunshi`
- Claude Code：`~/.claude/skills/girlfriend-reply-coach` 与 `~/.claude/skills/goutoujunshi`

测试可以通过内部函数传入临时 home，不依赖或修改真实用户目录。

## 数据流

1. 解析目标并计算全部目标路径。
2. 检查本仓库包含 `girlfriend-reply-coach/SKILL.md`。
3. 检查所有目标冲突；未使用 `--force` 时在任何写入前停止。
4. 检查 `git` 可用。
5. 使用系统临时目录执行浅克隆：`git clone --depth 1 <repo> <temp>`。
6. 定位下载仓库中的 `goutoujunshi/SKILL.md`；同时兼容仓库根目录本身就是 Skill 的布局。
7. 打印第三方项目、官方仓库地址、PolyForm Noncommercial License 1.0.0 和非官方背书提示。
8. 为每个安装目标先复制到同级临时目录，再原子重命名为最终目录。
9. 所有安装成功后打印实际绝对路径和重新启动对应 CLI/App 的提示。

## 覆盖与失败原子性

默认模式不删除已有目录。

`--force` 模式为每个已有目标创建同级备份目录，然后安装新版本。全部目标成功后删除备份；任何目标失败时删除本次新目录并恢复所有备份。这样 `both` 不会出现 Codex 已更新、Claude Code 仍是旧版本的半完成状态。

所有删除和重命名仅允许发生在计算出的 `~/.codex/skills/<允许名称>`、`~/.claude/skills/<允许名称>` 及其安装临时/备份路径。Skill 名称固定为 `girlfriend-reply-coach` 和 `goutoujunshi`，不接受用户传入任意目录名。

## 下载校验

下载内容必须满足：

- 能定位唯一的 `goutoujunshi` Skill 目录；
- 该目录直属包含非空 `SKILL.md`；
- `SKILL.md` 的 YAML frontmatter 中 `name` 等于 `goutoujunshi`。

校验失败时不写入任何目标目录。安装器不执行下载仓库中的脚本。

## 输出与错误

成功输出列出每个环境中的两个绝对安装路径。错误输出应包含失败阶段、相关路径或 Git 错误摘要，并返回非零退出码。

典型错误包括：

- Python 找不到本地 `girlfriend-reply-coach/SKILL.md`；
- 未安装 Git；
- 网络或克隆失败；
- 下载仓库不含合法 `goutoujunshi` Skill；
- 目标已存在但未传 `--force`；
- 文件权限不足；
- 覆盖失败后的恢复失败。

不得输出私人聊天、人物档案或私有数据目录内容。

## 文档

README 的安装章节以一键安装为首选，分别展示 Codex、Claude Code 和同时安装命令；保留手动安装作为故障排查方案，并明确手动模式需要分别安装两个 Skill。

`girlfriend-reply-coach/SKILL.md` 只声明运行时依赖 `goutoujunshi`，不负责自行执行安装器。

## 测试

使用 `unittest`、临时目录和本地假仓库/模拟 Git 运行器覆盖：

1. `codex` 只生成 Codex 的两个目标；
2. `claude` 只生成 Claude Code 的两个目标；
3. `both` 安装四个目录；
4. 默认遇到任一冲突时零写入；
5. `--force` 成功覆盖两个环境；
6. 强制覆盖中途失败时恢复全部旧目录；
7. 克隆失败时返回非零且零写入；
8. 缺少或错误命名的 `SKILL.md` 时拒绝安装；
9. README 同时包含三个安装目标和第三方许可提示；
10. 完整现有测试套件无回归。

## 非目标

- 不安装 Git 或 Python；
- 不自动更新已安装 Skill；
- 不修改 Codex 或 Claude Code 的全局配置；
- 不安装、读取或迁移私人聊天数据；
- 不重新分发 `goutoujunshi`；
- 不绕过第三方许可证或网络访问限制。
