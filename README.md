# 🔥 AgentForge

> **轻量、Provider 无关、开箱即跑的 AI Agent 开发框架。**
> 默认内置 **Mock Provider**——无需任何 API 密钥，所有示例与测试即可运行。

---

## ✨ 为什么是 AgentForge？

大多数 Agent 框架在「跑通第一个 Demo」之前，就要求你先申请 API Key、配置环境变量、理解一长串抽象概念。AgentForge 反其道而行：

- 🚀 **零密钥即可运行**：内置 Mock Provider，克隆仓库后 `python examples/research_agent.py` 立刻看到效果。
- 🔌 **Provider 无关**：OpenAI / Anthropic / Ollama / 自建后端，只需切换一个名字。
- 🧩 **工具即函数**：一个 `@tool` 装饰器，自动生成 JSON Schema 并全局注册。
- 🔁 **ReAct 推理循环**：开箱即用的「思考 → 调用工具 → 观察」多轮推理。
- 👥 **多智能体编排**：Supervisor 路由式 Team，几行代码组装协作团队。
- 🔭 **可观测（AgentLens）**：事件总线默认打印结构化 trace，亦可接入任意后端。

### 对比

| 维度 | AgentForge | 传统框架 |
|------|-----------|----------|
| 跑通首例 | 无需 Key，一行命令 | 常需 Key + 配置 |
| 切换模型 | `get_provider("openai")` | 重写大量胶水代码 |
| 自定义工具 | `@tool` 装饰器 | 手写 JSON Schema |
| 可观测性 | 事件总线内置 | 通常需外接 |

---

## 📦 安装

```bash
# 从源码安装（推荐，便于运行示例）
pip install -e .

# 或从 PyPI（发布后）
pip install agentforge

# 按需安装真实 Provider 的 SDK
pip install agentforge[openai]      # OpenAI
pip install agentforge[anthropic]   # Anthropic (Claude)
pip install agentforge[ollama]      # 本地 Ollama
pip install agentforge[all]         # 全部
```

核心仅依赖 `pyyaml`，其余 SDK 均为可选。

---

## ⏱️ 30 秒快速开始

```python
import agentforge  # 触发 provider + tool 注册
from agentforge.core.provider import get_provider
from agentforge.core.agent import Agent
from agentforge.core.memory import MemoryStore

provider = get_provider("mock")()          # 默认 Mock，无需 Key
agent = Agent(
    name="researcher",
    role="你是一个严谨的研究助手，善于用工具核实事实。",
    provider=provider,
    tools=["web_search", "calculator", "get_datetime"],
    memory=MemoryStore(),
)
result = agent.run("What is (2+3)*4? Explain it.")
print(result.answer)
```

切换为真实模型只需改一行：

```python
provider = get_provider("openai")(model="gpt-4o-mini")   # 读取 OPENAI_API_KEY
```

---

## 🧠 核心概念

### Provider —— 与模型对话的唯一边界
所有 LLM 调用都收敛到 `Provider.chat(messages, tools)`，框架其余部分完全与具体模型解耦。

```python
from agentforge.core.provider import get_provider
provider = get_provider("mock")()
```

内置 `mock` / `openai` / `anthropic` / `ollama`，也可 `register_provider("my", MyProvider)` 自定义。

### Tool —— 把函数变成智能体能力
`@tool` 装饰器自动从签名 + 类型标注 + docstring 推断 JSON Schema，并在定义时注册到全局。

```python
from agentforge.core.tool import tool

@tool
def calculator(expression: str) -> str:
    """计算安全算术表达式。"""
    return str(eval(expression, {"__builtins__": {}}, {}))

calculator.run(expression="(2+3)*4")   # => "20"
```

### Memory —— 对话历史 + 长期记忆
`MemoryStore` 提供短期对话（`add` / `history`）与长期 KV（`remember` / `recall`），可作为扩展点替换为向量库。

### Agent —— ReAct 推理循环
把任务交给 Agent，它会自行决定「是否调用工具、调用哪个、何时给出最终答案」。

```python
from agentforge.core.agent import Agent
agent = Agent("calc", "你擅长计算。", provider, tools=["calculator"])
result = agent.run("计算 (2+3)*4")
result.answer   # 最终答案
result.trace    # 每步 thought / action / observation
```

### Team —— 多智能体协作
Supervisor 根据成员职责路由任务，收集结果后综合作答。

```python
from agentforge.core.team import Team
team = Team(provider, {"architect": a1, "engineer": a2})
print(team.run("用 Python 写一个命令行计算器"))
```

### EventBus / AgentLens —— 可观测基础
每一步都会 emit 事件（`agent.start` / `agent.thought` / `tool.call` / `tool.result` / `agent.done` / `team.route`）。未传入 `event_bus` 时，Agent/Team 自动挂载 AgentLens 打印 trace。

```python
from agentforge.core.events import EventBus, TOOL_CALL

bus = EventBus()
bus.subscribe(TOOL_CALL, lambda e, d: print("调用工具:", d["tool"], d["arguments"]))
agent = Agent("x", "role", provider, tools=["calculator"], event_bus=bus)
```

---

## 🧪 示例

| 脚本 | 说明 |
|------|------|
| `examples/research_agent.py` | 研究型 Agent：`calculator` + `web_search` + `get_datetime` |
| `examples/coding_team.py` | 编码团队：Supervisor 路由 `architect` / `engineer` |
| `examples/debate_team.py` | 辩论团队：正反两方 Agent 由 Supervisor 综合 |

运行（默认 Mock，无需 Key）：

```bash
python examples/research_agent.py
python examples/coding_team.py
python examples/debate_team.py
```

命令行同样可用：

```bash
python -m agentforge.cli --task "计算 (2+3)*4 并向我解释"
python -m agentforge.cli --agent debate --task "AI 对人类是利大于弊吗？"
```

---

## 🏗️ 架构

```
                ┌─────────────────────────────┐
   user task →  │           Team              │  (可选：Supervisor 路由)
                │  supervisor_provider + members│
                └──────────────┬──────────────┘
                               │ run(task)
                               ▼
                ┌─────────────────────────────┐
                │           Agent              │  ReAct 循环
                │  role + tools + memory       │
                └───┬───────────────┬─────────┘
                    │               │
            provider.chat()    Tool.run()
                    │               │
              ┌─────▼────┐    ┌─────▼──────┐
              │ Provider │    │   Tools    │  @tool 注册表
              │ (mock/   │    │ calculator │
              │  openai/ │    │ web_search │
              │  ...)    │    │ read_file  │
              └──────────┘    └────────────┘
                    │
                EventBus (AgentLens 默认打印 trace)
```

更详细的模块依赖与数据流见 [ARCHITECTURE.md](./ARCHITECTURE.md)。

---

## 🛠️ 开发指南

```bash
pip install -e ".[all]"        # 安装含可选依赖
pip install pytest             # 测试
pytest -q                      # 全部离线通过（Mock）
python -m agentforge.cli --task "你好，介绍一下自己"
```

### 扩展点
- **新增 Provider**：继承 `Provider`，实现 `chat()`，并 `register_provider("name", Cls)`。
- **新增 Tool**：用 `@tool` 装饰普通函数，自动注册。
- **替换 Memory**：继承/替换 `MemoryStore`，实现持久化或向量检索。

---

## 🗺️ 路线图
- [ ] 流式输出（streaming）与中断/恢复
- [ ] 更多内置工具（HTTP、SQL、代码执行沙箱）
- [ ] 向量记忆后端插件
- [ ] OpenTelemetry / Web UI 观测面板

---

## 🤝 贡献
欢迎 Issue 与 PR！请先阅读本 README 与 ARCHITECTURE.md，保持示例「零密钥可跑」的约定（新增能力默认提供 Mock 行为或离线模拟）。

---

## 📄 License
[MIT](./LICENSE) © 2026 AgentForge Contributors
