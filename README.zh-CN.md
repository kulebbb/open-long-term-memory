# Open Long-Term Memory

[English](README.md) | 简体中文

面向 AI Agent 的 Markdown 原生长期记忆框架。

本项目提供一套轻量、可审计的长期记忆方案：将持久事实保存为普通 Markdown 文件。它适合希望记忆可被任何编辑器读取、可通过 Git 追踪、可在多台机器间同步，同时不想引入数据库或向量库的人和 Agent。

核心规则很简单：**一个事实一个文件**。YAML frontmatter 是唯一真相，索引和内容地图（MOC）都是由脚本生成的投影。

## 设计目标

- **人类可读**：每条记忆都是普通 Markdown 文件。
- **渐进式披露**：Agent 从小型索引开始，不把整个仓库塞进上下文。
- **可审计**：Git 记录每条事实由谁在何时修改。
- **Agent 友好**：内置 Skills 定义何时、如何召回与写入记忆。
- **适配多机**：只允许 fast-forward 的同步脚本会明确报告本地克隆是否过期。
- **零运行时依赖**：索引器只使用 Python 标准库，同步脚本使用 POSIX `sh`。
- **兼容 Obsidian**：文件名等于记忆 ID，因此 `[[id]]` 会自动成为图谱边。

## 工作原理

召回分为三层：

| 层级 | 读取内容 | 用途 |
|------|----------|------|
| L0 | `INDEX.md` 和最小范围的 `moc/*.md` | 快速导航和摘要 |
| L1 | 候选文件的 frontmatter 和首段 | 判断是否与当前任务相关 |
| L2 | 一到三个明确相关文件的完整正文 | 只加载真正需要的证据 |

Agent 不应把整个记忆仓库直接写入提示词。

## 快速开始

环境要求：

- Python 3.9 或更高版本
- Git
- 可运行 `scripts/memory-sync.sh` 的 POSIX 兼容 shell

```bash
git clone https://github.com/kulebbb/open-long-term-memory.git
cd open-long-term-memory

# 启用提交前的自动索引重建
git config core.hooksPath .githooks

# 验证演示数据和生成索引
python3 -m unittest discover -s tests -v
python3 scripts/build_memory_index.py --check
```

仓库自带一组虚构的 `sample-app` 演示数据，确保所有索引页面都有可查看的内容。开始使用自己的记忆库时，替换或删除所有 `example-*` 记录即可。

## 一条提示词让 Agent 安装并启用

将下面整段复制给能够使用终端和编辑文件的 Agent。如果你没有在消息中提供 GitHub 仓库地址，Agent 必须先询问地址，不能直接安装或修改任何内容。

```text
你负责在我本机安装并启用 Open Long-Term Memory。

开始前先确认我已经提供 GitHub 仓库地址。如果我没有提供，先停下来问我：
- 我的长期记忆仓库完整 GitHub URL；真实个人记忆必须使用 private 仓库；
- 本地安装路径，默认 ~/open-long-term-memory。

如果我还没有创建仓库，引导我先在 GitHub 创建一个空的 private 仓库，再把完整地址发给你。使用我现有的 Git 或 GitHub 认证，不要让我在对话中粘贴访问令牌。

确认后请完整执行以下安装流程：

1. 检查 git、python3（3.9 或更高版本）和 POSIX 兼容的 sh 是否可用。
2. 不得覆盖、删除、reset 或 force-push 已存在的目录或仓库。先检查现有内容，任何修改前都先问我。
3. 如果我的仓库已经包含 SCHEMA.md、INDEX.md、scripts/ 和 skills/，直接克隆该仓库。
4. 如果仓库为空或缺少本框架，从 https://github.com/kulebbb/open-long-term-memory.git 引导安装。保留框架、许可证、脚本、测试和 Agent Skills；只有我确认后才能删除虚构的 sample-* 和 example-* 数据。将我的 GitHub 地址设为 origin；创建聚焦的中文提交；只有我确认后才能 push。
5. 在克隆目录运行：
   git config core.hooksPath .githooks
   python3 -m unittest discover -s tests -v
   python3 scripts/build_memory_index.py --check
   sh scripts/memory-sync.sh
6. 在 Agent 平台使用的全局指令文件中追加以下幂等块，例如 ~/.codex/AGENTS.md、~/.claude/CLAUDE.md 或同类文件，以启用内置 Skills：

   <!-- open-long-term-memory:begin -->
   长期记忆：
   - 召回持久事实前，读取 <绝对克隆路径>/skills/recall-long-term-memory/SKILL.md。
   - 保存持久事实前，读取 <绝对克隆路径>/skills/write-long-term-memory/SKILL.md。
   - 两类操作前都先运行 `sh <绝对克隆路径>/scripts/memory-sync.sh`。
   <!-- open-long-term-memory:end -->

   如果你的平台没有全局指令机制，打印这个块，并明确告诉我应该安装到哪里。
7. 如果仓库是公开的，提醒我生成索引可能暴露个人数据，并在写入任何个人事实前帮我迁移到私有仓库。
8. 安装完成后汇报：仓库 URL、本地路径、分支与 commit、测试和同步结果、hook 与 Skills 是否已启用，并让我提供一个召回测试。

绝不输出秘密，绝不 force-push，绝不编造仓库地址。
```

## 接入 Agent

将本仓库作为独立克隆保存，并在 Agent 的全局指令中加入指向实际克隆路径的说明：

```text
长期记忆：
- 召回持久事实前，读取 <clone>/skills/recall-long-term-memory/SKILL.md。
- 保存持久事实前，读取 <clone>/skills/write-long-term-memory/SKILL.md。
- 两类操作前都先运行 `sh <clone>/scripts/memory-sync.sh`。
```

这样 Skill 会随仓库一起更新，不需要在每台机器维护第二份规则副本。

更多细节见 [Agent 接入说明](docs/agent-integration.md)。

## 日常命令

```bash
# 重新生成 INDEX.md 和 moc/*.md
python3 scripts/build_memory_index.py

# 只校验，不写入
python3 scripts/build_memory_index.py --check

# 将缺少 project/person 锚视为错误
python3 scripts/build_memory_index.py --strict

# 为一条新记忆推荐最多 5 个潜在关联
python3 scripts/build_memory_index.py --suggest-links <id>

# 检查当前克隆是否与远端一致
sh scripts/memory-sync.sh

# 运行全部测试
python3 -m unittest discover -s tests -v
```

每次提交记忆变更时，`pre-commit` 钩子会自动重建生成文件。GitHub Actions 会重复执行相同检查，因此即使有人绕过了本地钩子，也无法在索引过期时静默发布。

## 仓库结构

| 路径 | 用途 |
|------|------|
| `profile/` | 稳定的身份、偏好和长期规则 |
| `people/` | 人物、角色和关系 |
| `projects/<slug>/` | 某个产品、团队或项目的长期事实 |
| `decisions/` | 带日期的决定，ADR-lite |
| `journal/` | 时间性笔记，可归档 |
| `open-loops/` | 未完成事项及明确的关闭条件 |
| `moc/` | 自动生成的内容地图 |
| `skills/` | Agent 召回与写入工作流 |
| `scripts/` | 索引生成与多机同步 |
| `templates/` | 可复制的 frontmatter 模板 |
| `tests/` | 标准库测试套件 |
| `INDEX.md` | 自动生成的顶层索引 |

`profile` 回答的问题是：“什么会一直成立，直到被明确修改？”

`decision` 回答的问题是：“在某个时间点决定了什么，以及以后是否可能被替代？”

字段、关系规则、校验行为和生成页面的完整规则见 [SCHEMA.zh-CN.md](SCHEMA.zh-CN.md)。英文规范见 [SCHEMA.md](SCHEMA.md)。

## 多机同步

每台机器保留自己的克隆。读取或写入记忆前，先运行：

```bash
sh scripts/memory-sync.sh
```

脚本只执行 fetch 和 fast-forward，不会 merge、rebase，也不会修改未提交文件。

| 标签 | 含义 | 建议操作 |
|------|------|----------|
| `OK` / `SYNCED` | 已与远端对齐 | 继续 |
| `STALE` | 落后，但本地改动阻止了拉取 | 读取时注明可能落后；写入前先清理工作区 |
| `OFFLINE` | 远端不可用 | 使用本地数据，并说明未核对远端 |
| `AHEAD` | 本地存在未推送提交 | 在其他地方写入前先 push |
| `DIVERGED` | 本地和远端都有新提交 | 停下询问用户，禁止 force-push |
| `SKIP` | 不在 `main`、没有远端或不是 Git 仓库 | 按本地副本处理并明确说明 |

## 隐私与安全

本仓库作为**模板**可以公开；真实记忆通常应使用私有仓库。

- 不存密码、API Key、访问令牌、银行卡号或私钥。
- 个人资料、客户数据、内部 URL 和专有决策均按敏感信息处理。
- 除非所有贡献者都已检查内容，否则不要公开真实记忆仓库。
- 生成索引会包含记忆摘要。被 `.gitignore` 忽略的文件和符号链接不会进入索引，以降低意外泄露风险。
- 内置演示记录全部为虚构数据。不要向公开模板贡献真实个人或组织记忆。

安全报告和操作建议见 [SECURITY.md](SECURITY.md)。备份、索引恢复、敏感信息轮换和项目退役流程见 [运维说明](docs/operations.md)。

## 扩展框架

默认只保留少量类型：

- `profile`
- `person`
- `project`
- `decision`
- `journal`
- `open-loop`

如果要增加新类型，需要同步修改 `SCHEMA.md`、`scripts/build_memory_index.py`、模板和测试。生成索引永远不要手动修改，应重新运行索引器。

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)。所有贡献必须使用虚构示例，不得包含秘密或真实个人数据。

## 许可证

MIT，见 [LICENSE](LICENSE)。
