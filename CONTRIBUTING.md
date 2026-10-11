# 贡献指南 · Contributing to AgentForge

感谢你对 AgentForge 的关注！我们欢迎任何形式的贡献：文档、示例、Bug 修复、新 Provider、新 Tool，以及各类想法。

在提交之前，请先阅读 [README.md](./README.md) 与 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解项目定位与架构。

> **核心约定**：保持「**零密钥可跑**」。任何新增能力都应默认提供 Mock / 离线行为，确保 `pytest -q` 在无网络、无 API Key 的环境下全部通过。

---

## 开发环境搭建 · Development Setup

本项目要求 **Python 3.9+**（CI 覆盖 3.9 / 3.10 / 3.11 / 3.12 / 3.13）。

```bash
# 1. 克隆仓库
git clone https://github.com/YANLEI0817/agentforge.git
cd agentforge

# 2. 创建并激活虚拟环境
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 3. 以可编辑模式安装（包含全部可选 SDK）
pip install -e ".[all]"
pip install pytest pyyaml

# 4. 运行全部测试（默认使用 Mock Provider，无网络需求）
python -m pytest -q
```

运行示例程序（同样无需任何 Key）：

```bash
python examples/research_agent.py
python examples/coding_team.py
python examples/debate_team.py
python -m agentforge.cli --task "计算 (2+3)*4 并向我解释"
```

---

## 代码风格 · Code Style

- 遵循 **PEP 8**，单行不超过 100 字符，使用 4 空格缩进。
- **所有函数签名必须带类型标注**（项目整体使用 `from __future__ import annotations` 以兼容 3.9）。
- **公开类与公开方法必须写 docstring**（推荐 Google 风格：`Args:` / `Returns:` / `Raises:`）。
- 变量与函数命名清晰达意；复杂逻辑需加行内注释说明「为什么」而非「做了什么」。
- 导入顺序：标准库 → 第三方 → 本项目（本项目内部使用相对导入）。
- 避免引入循环依赖；可选 SDK（`openai` / `anthropic` / `requests`）**必须惰性导入**（在函数体内 `import`），以保证缺省安装也能导入包。
- 提交前请确保 `python -m pytest -q` 全绿。

---

## 如何新增一个 Provider · Adding a Provider

Provider 是与 LLM 对话的唯一边界，所有模型调用都收敛到 `Provider.chat(messages, tools)`。

1. 在 `agentforge/providers/` 下新建文件，例如 `my_provider.py`：

```python
"""MyProvider implementation."""
from __future__ import annotations

from typing import Any, List, Optional

from ..core.provider import ChatResult, Message, Provider


class MyProvider(Provider):
    """Provider backed by MyService."""

    def __init__(self, model: str = "my-model", api_key: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(model=model, api_key=api_key, **kwargs)

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Run a chat completion and map the response into a ChatResult."""
        import myservice  # lazy import: optional SDK

        client = myservice.Client(api_key=self.api_key)
        resp = client.generate(...)
        return ChatResult(content=..., tool_calls=[...], raw=resp)
```

2. 在 `agentforge/providers/__init__.py` 中注册（用 `try/except` 包裹，保证无 SDK 时也不报错）：

```python
try:
    from .my_provider import MyProvider
    register_provider("my", MyProvider)
except Exception:  # pragma: no cover - depends on optional SDK
    pass
```

3. 为新 Provider 补充**离线单元测试**：在 `tests/` 下用 `monkeypatch.setitem(sys.modules, "myservice", fake_module)` 注入假 SDK，断言 `chat()` 对响应内容的解析与 `tool_calls` 的转换是否正确，**不得发起真实网络请求**（参考 `tests/test_providers.py`）。

---

## 如何新增一个 Tool · Adding a Tool

Tool 把一个普通函数变成智能体可调用的能力，`@tool` 会自动从签名 + 类型标注 + docstring 推断 JSON Schema 并全局注册。

```python
from agentforge.core.tool import tool

@tool
def word_count(text: str) -> int:
    """统计文本的单词数量。"""
    return len(text.split())

# 自动注册，可按名获取：
from agentforge.core.tool import get_tool
t = get_tool("word_count")
t.run(text="hello world")   # => "2"
t.schema()                  # OpenAI 风格的工具 schema
```

要点：
- 参数**必须带类型标注**（`str` / `int` / `float` / `bool` / `list` / `dict` 会自动映射为对应的 JSON 类型）。
- docstring 首行会作为工具描述；使用 `@tool(name=..., description=..., parameters=...)` 可自定义名称、描述或手写参数 schema。
- 新增内置工具请放到 `agentforge/tools/builtin.py`，并在 `tests/test_tools.py` 中补充断言。

---

## 提交 / 分支 / PR 规范 · Commits, Branches & Pull Requests

采用 [Conventional Commits](https://www.conventionalcommits.org/) 的简要约定：

```
<type>(<scope>): <subject>

feat(provider): add Gemini provider
fix(agent): stop ReAct loop on max_iterations
docs(readme): add CI badge
test(tools): cover calculator unsafe input
chore(ci): bump setup-python to v5
```

常用 `type`：`feat` / `fix` / `docs` / `test` / `refactor` / `chore` / `perf`。

分支命名：`feat/<short-desc>`、`fix/<short-desc>`、`docs/<short-desc>`。

提交 PR 前请自检：

- [ ] 从最新的 `main` 切出分支，分支名符合命名规范。
- [ ] `python -m pytest -q` 全部通过（含新增测试）。
- [ ] 新增/变更逻辑已补充对应测试，且**不依赖网络或 API Key**。
- [ ] 更新了受影响的文档（README / ARCHITECTURE / 本文件）。
- [ ] PR 描述清晰：**做了什么、为什么、如何验证**，并关联相关 Issue（如 `Closes #12`）。

---

## 发布 · Publishing

项目通过 **PyPI Trusted Publishing (OIDC)** 自动发布，**仓库内不保存任何 Token**。

- 分发名（PyPI distribution）：`agent-forge`；导入包名仍为 `agentforge`。
- 工作流：`.github/workflows/publish.yml`，在**发布 GitHub Release** 时触发（也支持手动 `workflow_dispatch`）。

首次发布前的一次性配置：

1. 在 <https://pypi.org> 创建/预留项目 `agent-forge`。
2. 在该项目的 Publishing 设置中新增 **Trusted Publisher**：
   - Owner：`YANLEI0817`
   - Repository：`agentforge`
   - Workflow：`publish.yml`
   - Environment：`pypi`
3. 在仓库 Settings → Environments 中创建名为 `pypi` 的环境。

之后只需发布 Release，CI 即会自动构建并上传到 PyPI。

本地预演构建（可选）：

```bash
python -m build          # 生成 dist/*.whl 与 *.tar.gz
python -m twine check dist/*
```

---

## 报告 Bug · Reporting Bugs

提交 Issue 时，请尽量包含以下要点（可复制模板）：

```markdown
**环境**
- OS / 架构：
- Python 版本（`python --version`）：
- AgentForge 版本或 commit：
- 使用的 Provider（mock / openai / anthropic / ollama）：

**复现步骤**
1.
2.

**期望行为**
...

**实际行为 / 完整报错栈**
...

**最小可复现代码**
```python
...
```
```

> 提示：请优先使用 **Mock Provider** 复现问题，以排除外部 SDK / Key / 网络因素。

---

## 行为准则 · Code of Conduct

参与本项目即表示你同意遵守贡献者行为准则：**保持尊重、包容与专业**。完整内容见 [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)。

- 对事不对人，欢迎不同观点与技术讨论。
- 不接受任何形式的骚扰、歧视或人身攻击。
- 维护者有权删除不当内容并拒绝不符合准则的贡献。

（本准则基于 [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) v2.1。）

---

再次感谢你的贡献！🔥
