# 人物档案与隐私

## 默认私有目录

将私人资料放在 Git 仓库之外：

```text
~/.codex/private/girlfriend-reply-coach/
├─ manifest.json
├─ self-voice.json
├─ people/<slug>/
│  ├─ profile.json
│  └─ voice-delta.json
├─ derived/<slug>/
└─ raw/                         # 仅在用户明确选择保留时创建
```

若环境变量 `GIRLFRIEND_REPLY_COACH_DATA` 已设置，优先使用该目录。否则默认使用上面的目录。开始写入前明确告诉用户实际绝对路径。脚本拒绝把人物档案写入任何检测到的 Git 工作区。

## 本人语气档案

`self-voice.json` 只记录由用户消息或明确纠正支持的模式：

- 常用称呼和明确禁用称呼；
- 单条长度、短句连发或长段落习惯；
- 标点、emoji、表情和中英文混用；
- 道歉、安慰、撒娇、认真沟通时的表达差异；
- 用户明确不会说的话；
- 每项模式的证据、置信度和更新时间。

不要把女朋友的说话风格混入本人语气档案。

## 对象专属语气差异

`people/<slug>/voice-delta.json` 只记录用户相对于通用语气、面对该对象时特有的表达：

- 专属称呼及明确禁用称呼；
- 亲密程度、撒娇程度和玩笑尺度；
- 只在这段关系中使用的语气词、表情和梗；
- 对正式道歉、日常闲聊等场景的关系专属差异；
- 每项模式的证据、置信度、适用情境和更新时间。

它不保存关系策略、对方人格诊断或 `goutoujunshi` 的资料。不同对象的差异档案按 `slug` 隔离，不得交叉使用。

## 女朋友档案

每条 `claims` 记录：

```json
{
  "id": "稳定标识",
  "content": "难过时更希望先被倾听",
  "classification": "高置信度模式",
  "evidence": ["来源与片段标识 A", "来源与片段标识 B"],
  "confidence": 0.85,
  "contexts": ["工作受挫", "家庭压力"],
  "conflicts_with": [],
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

分类仅允许：

- `已确认事实`：原话、实际行为或用户明确说明直接支持；
- `高置信度模式`：至少两个独立情境重复支持；
- `待验证推测`：证据少或存在其他合理解释。

人物档案可包含称呼、表达习惯、情绪需要、安全感来源、倾听/解决偏好、道歉偏好、礼物与约会偏好、沟通雷区、重要日期、共同经历、有效/无效安慰方式和未解决问题。

## 冲突与纠正

新证据和旧结论冲突时：

1. 不覆盖或删除旧结论；
2. 为双方添加 `conflicts_with`；
3. 降低受影响结论的置信度；
4. 记录新证据和更新时间；
5. 只有用户确认或后续证据充分时才解决冲突。

用户纠正时，先复述准备修改的内容。人物事实纠正进入 `profile.json`；跨对象稳定的本人说话方式进入 `self-voice.json`；只对当前对象成立的表达进入对应 `voice-delta.json`。

## 创建与删除

创建空档案：

```powershell
python scripts/profile_store.py create --root <私有目录> --slug current --alias <代号>
```

先预览将删除的绝对路径和确认令牌：

```powershell
python scripts/profile_store.py preview-delete --root <私有目录> --slug current
```

向用户展示这些路径并获得确认后，使用刚才返回、与路径绑定的令牌删除人物档案、派生摘要及用户明确保留的原始副本：

```powershell
python scripts/profile_store.py delete --root <私有目录> --slug current --confirm <确认令牌>
```

目标路径变化会使旧令牌失效。脚本只允许删除调用者指定私有根目录下的 `people/<slug>`、`derived/<slug>` 和 `raw/<slug>`。

## 最小化原则

- 默认不保留原始聊天、照片和社交资料。
- 证据字段优先保存来源标识和必要短摘要，不复制整段敏感内容。
- 不在无关输出中复述地址、电话、学校、证件号、账号、健康信息或精确位置。
- 照片只用于用户明确指定的可见事实或共同经历，不根据外貌推断人格、忠诚和动机。
