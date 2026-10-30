# 记忆文件规范

一句话：**一个事实一个 Markdown 文件；frontmatter 是唯一真相；`INDEX.md` 与 `moc/*.md` 由脚本生成，不手改。**

## 目录与 type

| 目录 | 必需 `type` | 说明 |
|------|-------------|------|
| `profile/` | `profile` | 稳定的身份、偏好和长期规则 |
| `people/` | `person` | 人物、角色和关系 |
| `projects/<slug>/` | `project` | 单个项目的事实；`<slug>` 是项目锚 |
| `decisions/` | `decision` | 带日期、将来可能被替代的决定 |
| `journal/` | `journal` | 时间性笔记，可归档 |
| `open-loops/` | `open-loop` | 未结事项与关闭条件 |

`type` 必须与所在目录一致，不一致视为错误。

### `profile` 还是 `decision`？

只问一句：**以后会不会被新事实推翻？**

- 不会：写 `profile`，用于长期身份、偏好和规则。
- 会：写 `decision`，保留日期和替代历史。

同一条规则只写一处。

## Frontmatter

```yaml
---
id: dec-2026-01-15-example-stack
type: decision
status: active
created: 2026-01-15
updated: 2026-01-15
author: user
tags: [example, architecture]
projects: [sample-app]
people: [person-example-maintainer]
links: [journal-2026-01-16-example-kickoff]
contradicts: []
supersedes: null
source: chat
recall_hint: "示例应用的技术方案是什么"
confirm_required: true
---
```

必填字段：

- `id`
- `type`
- `status`
- `created`
- `author`

建议字段：

- `updated`
- `tags`
- `projects`
- `people`
- `links`
- `contradicts`
- `supersedes`
- `source`
- `recall_hint`
- `confirm_required`

### 字段说明

| 字段 | 含义 |
|------|------|
| `id` | 全局唯一，只能使用小写字母、数字和连字符 |
| `type` | `profile`、`person`、`project`、`decision`、`journal` 或 `open-loop` |
| `status` | `active`、`superseded` 或 `archived` |
| `created` | 创建日期，格式 `YYYY-MM-DD` |
| `updated` | 最后一次有意义更新的日期 |
| `author` | 用户记录写 `user`；Agent 记录写自己的稳定短名 |
| `tags` | 用于检索的自由标签 |
| `projects` | `projects/` 下的项目目录名 |
| `people` | 已存在的 `person` 记录 ID |
| `links` | 相关事实 ID，无方向语义 |
| `contradicts` | 与本条冲突、尚未定论的 ID |
| `supersedes` | 被本条替代的旧事实 ID |
| `source` | `chat`、`manual` 或 `import` |
| `recall_hint` | 用户召回时可能自然说出的话 |
| `confirm_required` | 写入前是否需要在对话中确认 |

每条记忆都必须回答：**这是谁记的？**

- 用户口述或手写：`author: user`
- Agent 写入：使用自己的稳定短名
- 不使用 `assistant`、`AI` 这类泛称
- 不代签其他人或 Agent 的名字

### 文件名

文件名必须等于 `<id>.md`。

```text
id: dec-2026-01-15-example-stack
path: decisions/dec-2026-01-15-example-stack.md
```

这样 Obsidian 可以直接解析 `[[id]]`，`rg` 也能按 ID 精确定位。

以 `_` 或 `.` 开头的文件不参与索引。

内容目录只放记忆文件。其他笔记放到 `journal/`，或用下划线前缀排除。

数组可写内联形式：

```yaml
tags: [example, architecture]
```

也可写块状形式：

```yaml
projects:
  - sample-app
```

同一字段不要声明两次。

## 锚

`projects` 和 `people` 是检索记忆的主轴。

| type | 锚要求 | 缺失后果 |
|------|--------|----------|
| `decision` | 至少 1 个 project 或 person | 进入 `moc/unfiled.md`，警告 |
| `open-loop` | 至少 1 个 project 或 person | 进入 `moc/unfiled.md`，警告 |
| `journal` | 建议，不强制 | 不进入 unfiled |
| `person` / `profile` | 豁免 | — |
| `project` | 由 `projects/<slug>/` 自动归属 | — |

默认只警告；`--strict` 将缺锚升级为错误。

不要为了消除警告而填写不相干的锚。假边比缺边更难清理。

## 关系

只支持三种关系：

| 字段 | 语义 | 示例 |
|------|------|------|
| `supersedes` | 本条替代旧事实；旧事实改为 `status: superseded` | 新报价规则替代旧规则 |
| `contradicts` | 两条事实冲突，尚未定论，都保留 | “偏好 A”与“其实偏好 B” |
| `links` | 上下文相关，无方向 | 某决定来自一次项目复盘 |

值一律写记忆 ID，不写路径。

指向不存在的 ID 是硬错误；`supersedes` 目标仍为 `active` 会产生警告。

需要 Obsidian 图上的显式边时，可在正文写：

```markdown
关联：[[other-memory-id]]
```

生成器不会改写正文。

## 正文

- 第一个非标题段落是结论，并作为索引摘要。
- 控制在约一屏内。
- 可使用 `结论：` 开头，增强可读性。
- 必要时增加“不要自动联想到”段，防止误召回。
- 绝不写入秘密。

## 生成文件

`INDEX.md` 和 `moc/*.md` 是生成文件。脚本只改写 `<!-- moc:begin -->` 与 `<!-- moc:end -->` 之间的内容。

```bash
python3 scripts/build_memory_index.py
python3 scripts/build_memory_index.py --check
```

生成内容：

- `INDEX.md`：L0 入口，包含最近决定与各分类计数
- `moc/standing-rules.md`：active profile
- `moc/people.md`：active person，并反查相关项目
- `moc/decisions.md`：active 与 superseded decision
- `moc/open-loops.md`：active open-loop
- `moc/journal.md`：active 与 superseded journal
- `moc/unfiled.md`：缺 project/person 锚的 active decision/open-loop
- `moc/project-<slug>.md`：每个项目的聚合页

项目聚合页包含项目文件、决定、未结、时间笔记和相关人物。项目至少有一条 active 事实时才会生成。

项目被删除或整体归档后，只有标记外内容与生成器原始开场白完全一致时，聚合页才会自动删除。有人手写过内容时保留并报错，等待人工确认。

`status: archived` 不进入索引；需要历史时用 `rg` 搜索。

被 `.gitignore` 忽略的文件、隐藏文件和符号链接不会进入索引。

## 连边建议

```bash
python3 scripts/build_memory_index.py --suggest-links <id>
```

该命令只读，不修改文件。评分规则：

- 同项目锚：2 分
- 同标签：1 分

候选至少 2 分；archived 记录和项目容器文件不参与。

关系不会自动写入。只把用户确认相关的 ID 加入 `links:`。错边比缺边更难清理。

## 多机同步

读写前运行：

```bash
sh scripts/memory-sync.sh
```

| 标签 | 含义 |
|------|------|
| `OK` / `SYNCED` | 已对齐，可正常使用 |
| `STALE` | 落后，但未提交改动阻止了快进 |
| `OFFLINE` | 无法核对远端 |
| `AHEAD` | 本地有未推送提交 |
| `DIVERGED` | 本地与远端都有新提交 |
| `SKIP` | 不在 `main`、没有 `origin` 或不是 Git 仓库 |

脚本不会 force-push、merge、rebase，也不会修改未提交文件。

遇到 `DIVERGED` 应停下问用户。正常恢复流程最多允许执行一次 `git pull --rebase origin main`；冲突时立刻 `git rebase --abort`，展示双方内容，禁止 force-push。

## 校验汇总

硬错误：

- 缺必填字段
- ID 非法或重复
- 文件名不等于 ID
- 目录与 type 不符
- type、status 或日期非法
- `links`、`contradicts` 或 `supersedes` 指向不存在的 ID
- 项目 slug 不存在
- 索引标记不是恰好一对
- 项目聚合页无法安全删除

警告：

- 缺 project/person 锚
- `people` 不是 person 记录
- `source` 非法
- `supersedes` 目标仍为 active
- 缺 `updated`
- `projects/` 根目录下存在 Markdown
- 被忽略或为符号链接的记忆文件

`--check` 发现生成文件过期时退出码为 2。
