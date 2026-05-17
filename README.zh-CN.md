# overleaf-cookie-bridge

一个只依赖 Overleaf 浏览器登录态 cookie 的小型 CLI，用于安全读取、备份、拉取和替换指定 Overleaf 项目文件。

适用于没有 Overleaf Git 权限、Git 配置不方便，或者希望让 agent 先把论文源码拉到本地处理的场景。

当前支持：

- 验证 `overleaf_session2` cookie 是否可用
- 列出当前账号可见的 Overleaf 项目
- 下载完整项目 zip 备份
- 将项目拉取并解压到本地工作目录
- 通过备份、删除、上传、zip 校验来替换一个已知远端文件

重要说明：Overleaf 没有为这个流程提供公开稳定 API。本项目使用的是 Overleaf 网页端的非官方 endpoint，因此应视为 best-effort 工具。

## 当前状态

当前版本：`0.1.0`

已实现命令：

```bash
overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie backup PROJECT_ID
overleaf-cookie pull PROJECT_ID ./paper
overleaf-cookie push-file PROJECT_ID ./main.tex --remote main.tex --folder-id FOLDER_ID --entity-id ENTITY_ID --dry-run
overleaf-cookie push-file PROJECT_ID ./main.tex --remote main.tex --folder-id FOLDER_ID --entity-id ENTITY_ID --yes
```

## 安装

本地开发安装：

```bash
git clone https://github.com/Master-chenk/overleaf-cookie-bridge.git
cd overleaf-cookie-bridge
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
```

只做运行时安装：

```bash
pip install -e .
```

## 认证

在当前 shell 中设置 Overleaf 浏览器 session cookie：

```bash
export OVERLEAF_SESSION2='<your overleaf_session2 cookie>'
```

`overleaf_session2` 基本等价于你的 Overleaf 登录态。不要把它提交到 git、贴到 issue、写进脚本或文档。

如果 cookie 曾经暴露在聊天、日志或终端记录里，建议完成工作后退出 Overleaf 会话或使该 session 失效。

## 快速开始

```bash
source .venv/bin/activate
export OVERLEAF_SESSION2='<redacted>'

overleaf-cookie verify
overleaf-cookie list --json
overleaf-cookie pull PROJECT_ID ./paper
```

备份默认保存到：

```text
~/.overleaf-cookie-bridge/backups/PROJECT_ID/TIMESTAMP.zip
```

也可以自定义备份目录：

```bash
export OVERLEAF_COOKIE_BACKUP_ROOT=/path/to/backups
```

## 命令说明

### 验证 cookie

```bash
overleaf-cookie verify
```

期望输出类似：

```text
OK: cookie is valid; visible projects: N
```

### 列出项目

```bash
overleaf-cookie list
overleaf-cookie list --json
overleaf-cookie list --all --json
```

### 备份项目

```bash
overleaf-cookie backup PROJECT_ID
```

该命令会下载项目 zip，并保存到备份目录。

### 拉取项目

```bash
overleaf-cookie pull PROJECT_ID ./paper
```

该命令会先保存完整 zip 备份，再把项目安全解压到目标目录。解压时会拒绝 zip path traversal 路径。

### 替换一个远端文件

先预览写入计划，不修改 Overleaf：

```bash
overleaf-cookie push-file PROJECT_ID ./main.tex \
  --remote main.tex \
  --folder-id FOLDER_ID \
  --entity-id ENTITY_ID \
  --entity-type doc \
  --dry-run
```

确认计划后执行：

```bash
overleaf-cookie push-file PROJECT_ID ./main.tex \
  --remote main.tex \
  --folder-id FOLDER_ID \
  --entity-id ENTITY_ID \
  --entity-type doc \
  --yes
```

`push-file` 会先下载完整 zip 备份，删除指定的旧 entity，把本地文件上传到指定 folder，然后再次下载 zip，逐字节验证远端内容和本地文件一致。

你必须提供当前 Overleaf 的 `folder_id` 和 `entity_id`。第一次验证某个项目时，建议先用临时文件测试。替换 `doc` 可能改变 Overleaf 内部 entity id，并可能影响该文件上的评论或历史记录。

## 安全模型

当前 CLI 是保守写入模型：

- 本地解压或远端替换前都会保存完整 zip 备份
- 远端替换必须显式传入 `--yes`
- `push-file --dry-run` 只预览计划，不修改远端
- `push-file --yes` 上传后会重新下载项目 zip 做内容校验
- 常见错误路径会对 cookie 做脱敏
- 解压 zip 时检查路径穿越

agent 使用说明见 `SKILL.md`。

## 开发

```bash
source .venv/bin/activate
pytest -q
ruff check .
python -m build
```

如果缺少 `build` 或 `ruff`：

```bash
pip install -e '.[dev]'
```

## 项目结构

```text
src/overleaf_cookie_bridge/auth.py       # cookie 处理和脱敏
src/overleaf_cookie_bridge/client.py     # 项目列表、zip 下载、CSRF、上传/删除
src/overleaf_cookie_bridge/remote_zip.py # zip 内容校验辅助
src/overleaf_cookie_bridge/sync.py       # zip 备份和安全解压
src/overleaf_cookie_bridge/tree.py       # entity tree 辅助结构
src/overleaf_cookie_bridge/cli.py        # click CLI
tests/                                   # pytest 测试
docs/                                    # endpoint 说明和维护文档
SKILL.md                                 # agent runbook
```

## 安全提醒

请不要在公开 issue 或 PR 中包含：

- Overleaf cookie
- 项目源码 zip
- 未公开论文正文
- 不希望公开的 Overleaf project id 或项目名

敏感问题请按照 `SECURITY.md` 私下报告。

## 相关项目

- https://github.com/jkulhanek/pyoverleaf — Overleaf cookie/session 行为的参考实现。
- Overleaf Git integration — 如果可用，官方 Git 集成依然是更推荐的版本化方案。

## License

MIT. See `LICENSE`.
