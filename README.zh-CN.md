# Open Long-Term Memory

面向 AI Agent 的 Markdown 原生长期记忆框架。

本项目把长期记忆保存为普通 Markdown 文件：**一个事实一个文件**。YAML frontmatter 是唯一真相，`INDEX.md` 与 `moc/*.md` 都是脚本生成的导航投影。它不依赖数据库或向量库，便于人阅读、Git 审计、多机同步和 Agent 渐进式召回。

## 核心特性

- Markdown + YAML，任何编辑器都能读写。
- 分层召回：先读 L0 索引，再读 L1 摘要，最后只展开真正相关的 L2 正文。
- 自动生成顶层索引、分类 MOC 和项目聚合页。
- 校验 ID、目录类型、关系、锚点和索引 freshness。
- `pre-commit` 与 GitHub Actions 双重检查。
- 多机同步脚本明确报告 `OK`、`STALE`、`OFFLINE`、`AHEAD`、`DIVERGED` 等状态。
- 内置 Agent 写入与召回 Skills。
- 兼容 Obsidian 双链和图谱。

## 快速开始

要求：Python 3.9+、Git、POSIX 兼容 shell。

```bash
git clone https://github.com/kulebbb/open-long-term-memory.git
cd open-long-term-memory

git config core.hooksPath .githooks
python3 -m unittest discover -s tests -v
python3 scripts/build_memory_index.py --check
```

仓库自带一组明确虚构的 `sample-app` 演示数据，用于展示索引、项目聚合页和关系。开始使用自己的记忆库时，替换或删除所有 `example-*` 记录即可。

## 接入 Agent

在 Agent 的全局指令中加入实际克隆路径：

```text
长期记忆：
- 召回前读 <clone>/skills/recall-long-term-memory/SKILL.md。
- 写入前读 <clone>/skills/write-long-term-memory/SKILL.md。
- 两类操作前都先运行 `sh <clone>/scripts/memory-sync.sh`。
```

这样 Skill 随仓库同步更新，不需要在每台机器复制第二份规则。

更多接入细节见 [Agent 接入](docs/agent-integration.md)。

## 常用命令

```bash
python3 scripts/build_memory_index.py
python3 scripts/build_memory_index.py --check
python3 scripts/build_memory_index.py --strict
python3 scripts/build_memory_index.py --suggest-links <id>
sh scripts/memory-sync.sh
python3 -m unittest discover -s tests -v
```

## 目录

| 路径 | 用途 |
|------|------|
| `profile/` | 稳定的身份、偏好和长期规则 |
| `people/` | 人物、角色和关系 |
| `projects/<slug>/` | 项目或产品的长期事实 |
| `decisions/` | 带日期的决定（ADR-lite） |
| `journal/` | 时间性笔记，可归档 |
| `open-loops/` | 未结事项及关闭条件 |
| `moc/` | 自动生成的内容地图 |
| `skills/` | Agent 召回与写入工作流 |
| `scripts/` | 索引生成与多机同步 |
| `templates/` | 可复制模板 |
| `tests/` | 标准库测试 |

完整字段、关系与校验规则见 [SCHEMA.zh-CN.md](SCHEMA.zh-CN.md)。

## 隐私边界

这个仓库本身适合公开为**模板**；真实长期记忆通常应使用私有仓库。

- 不写密码、API Key、访问令牌、银行卡号或私钥。
- 个人资料、客户数据、内部链接和商业决策默认按敏感信息处理。
- 生成索引会包含记忆摘要；被 `.gitignore` 忽略的文件和符号链接不会进入索引。
- 公开模板只接受虚构示例，不接受真实个人或组织记忆。

备份、索引恢复、敏感信息轮换和项目退役流程见 [运维说明](docs/operations.md)。

## 许可证

MIT，见 [LICENSE](LICENSE)。
