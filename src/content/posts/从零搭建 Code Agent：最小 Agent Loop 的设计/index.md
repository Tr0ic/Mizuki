---
title: "从零搭建 Code Agent：最小 Agent Loop 的设计"
published: 2026-08-24T20:01:01+08:00
updated: 2026-08-26T21:36:24+08:00
description: "用 Python 设计一个可测试的最小 Agent Loop，梳理控制边界、工具契约、模型适配、退出状态和 JSONL 运行轨迹。"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2075303487131350018"
draft: false
pinned: false
---

## 目录

- [一、控制边界](#一控制边界)
- [二、运行数据](#二运行数据)
  - [（一）Action](#一action)
  - [（二）HistoryItem](#二historyitem)
  - [（三）RunResult](#三runresult)
  - [（四）frozen](#四frozen)
- [三、模型协议](#三模型协议)
  - [（一）FakeModel](#一fakemodel)
- [四、工具契约](#四工具契约)
  - [（一）ToolSpec](#一toolspec)
  - [（二）ToolDefinition](#二tooldefinition)
  - [（三）错误转换](#三错误转换)
- [五、模型适配](#五模型适配)
  - [（一）RawJsonModel](#一rawjsonmodel)
  - [（二）JsonModelAdapter](#二jsonmodeladapter)
- [六、运行循环](#六运行循环)
- [七、失败与退出](#七失败与退出)
- [八、JSONL 轨迹](#八jsonl-轨迹)
  - [（一）追加写入](#一追加写入)
  - [（二）安全摘要](#二安全摘要)
  - [（三）只读回放](#三只读回放)
- [九、测试边界](#九测试边界)
- [十、Code Agent 映射](#十code-agent-映射)

本文不接入真实模型服务，笔者只会尝试用 Python 手写一个可以稳定测试的最小 Agent Loop。重点放在控制边界、工具契约、模型适配、失败状态和 JSONL 轨迹上。

## 一、控制边界

Agent 是整个功能系统，Agent Loop 是其中负责协调模型与工具的控制程序。模型、控制程序和工具分别拥有不同的职责。

把模型比作大脑、工具比作四肢时，中间还缺少神经和控制系统。Agent Loop 就处在这个位置：它负责传递信号，也负责限制动作。

| 组成 | 主要职责 | 权力边界 |
| --- | --- | --- |
| 模型 | 根据任务和历史提出 ToolCall 或 Finish | 不能直接执行本地函数，也不能制造环境事实 |
| 模型适配器 | 把外部模型格式转换成内部 Action | 不决定工具是否获得执行权限 |
| Agent Loop | 调用模型、维护历史、执行预算和停止策略 | 不把模型生成的文字当成环境结果 |
| Runtime | 查找工具、分发调用、转换预期错误 | 只能执行注册表允许的 handler |
| 工具 | 校验参数并完成具体操作 | 不决定 Agent 下一步做什么 |
| Observation | 保存工具结果或预期错误 | 不修改运行流程 |

这里最容易混淆的是 `Finish`。模型返回 `Finish`，表示它认为任务已经完成；当前最小实现识别这个对象后直接返回答案。模型拥有提议权，真正执行 `return` 的仍是普通 Python 控制程序。

实际项目还会多一道完成门。例如 Code Agent 可以要求“测试通过后才接受结束”。这时 `Finish` 更像一份结束申请：验证通过才终止，验证失败则把原因写回历史，让模型继续修正。当前版本暂时省略了这层验证。

工具调用也是同样的道理。模型可以生成：

```text
ToolCall(
    tool_name="calculator",
    arguments={
        "left": 12,
        "operation": "multiply",
        "right": 7,
    },
)
```

这只是结构化申请。工具名是否存在、参数是否有效、执行有没有失败，都要经过 Runtime 和工具函数确认。

## 二、运行数据

字典当然也能表示任务和动作，但字段写错后，问题通常要到运行时才暴露。最小循环使用 `dataclass` 定义运行数据：

```text
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias


@dataclass(frozen=True)
class Task:
    prompt: str


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class Finish:
    answer: str


Action: TypeAlias = ToolCall | Finish


@dataclass(frozen=True)
class Observation:
    tool_name: str
    content: str
    is_error: bool = False


@dataclass(frozen=True)
class ModelFeedback:
    content: str
    is_error: bool = True


HistoryItem: TypeAlias = ToolCall | Observation | ModelFeedback
```

### （一）Action

模型每一轮只能提出两种动作：

```text
ToolCall | Finish
```

`ToolCall` 表示继续与环境交互，`Finish` 表示申请结束。`Action` 是类型别名，不会在运行时创建新的包装对象。

### （二）HistoryItem

正常工具路径的历史如下：

```text
ToolCall → Observation → ToolCall → Observation
```

模型输出非法时，Loop 会加入 `ModelFeedback`：

```text
非法模型输出 → ModelFeedback → 下一次模型调用
```

`Task` 每轮都单独传给模型，所以没有重复放进历史。当前 `Finish` 会直接结束循环，也不会进入下一轮上下文。

### （三）RunResult

只返回字符串，很难区分正常完成、预算耗尽和模型输出持续非法。结构化结果把原因单独保存：

```text
class ExitReason(StrEnum):
    FINISHED = "finished"
    MAX_STEPS_EXCEEDED = "max_steps_exceeded"
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class RunResult:
    exit_reason: ExitReason
    answer: str | None
    steps_used: int
    error: str | None = None
```

`run_agent_result()` 给轨迹和评测返回 `RunResult`。原来的 `run_agent()` 仍保留为便捷入口：正常完成时返回答案，预算耗尽或模型输出持续非法时抛出对应异常。

### （四）frozen

这些对象记录的是某一刻已经发生的事实。创建完成后再修改 `Observation.content`，会让历史失去可信度，因此 dataclass 使用了 `frozen=True`。

`frozen=True` 只提供浅层限制。`ToolCall.arguments` 指向的映射内部仍可能是可变字典，后续可以在边界处复制或转换参数。

## 三、模型协议

Agent Loop 需要模型具备什么能力？答案只有一个：接收任务和历史，返回下一步动作。

```text
from collections.abc import Sequence
from typing import Protocol


class Model(Protocol):
    def next_action(
        self,
        task: Task,
        history: Sequence[HistoryItem],
    ) -> Action:
        ...
```

这里使用 `Protocol` 描述 **结构化接口**。任何对象只要拥有签名兼容的 `next_action()`，静态类型检查器就可以把它当作 `Model`。

因此 `FakeModel` 无需显式继承 `Model`：

```text
class FakeModel:
    def next_action(
        self,
        task: Task,
        history: Sequence[HistoryItem],
    ) -> Action:
        ...
```

这种关系可以理解成带静态检查的鸭子类型。普通基类强调显式继承，也可以携带共享实现和状态；`Protocol` 则是关注对象具备哪些能力，只要一个东西，长得像鸭子，行为也像鸭子，那么它就是鸭子，Protocol 的继承关系也是这样，同样，如果 `FakeModel` 在定义中宣称自己是 `Model`，并且采用了 `Model` 的函数，传入了同样类型的参数得到了同样类型的结果，那么它就是 `Model`，从而减少 Agent Loop 对具体模型类的依赖。

类型标注不会让 Python 在调用时自动检查对象。`Protocol` 的主要检查发生在 mypy 等静态类型检查器中；运行时传入缺少 `next_action()` 的对象，最终仍会得到 `AttributeError`。

### （一）FakeModel

真实模型的输出会受到模型版本、提示词、温度和服务状态影响。直接依赖真实 API 测试 Agent Loop，失败原因容易混在一起：可能是循环错误，也可能只是模型这次换了答案。

`FakeModel` 接收一组预定动作，并逐个返回：

```text
model = FakeModel([
    ToolCall(
        tool_name="calculator",
        arguments={
            "left": 12,
            "operation": "multiply",
            "right": 7,
        },
    ),
    Finish(answer="12 * 7 = 84，84大于80。"),
])
```

它不会理解 Observation，也不会真的判断 `84 > 80`。它只负责按顺序返回动作，并记录每次调用收到的任务与历史。

这正好适合测试控制程序。第一轮固定返回 `ToolCall`，第二轮固定返回 `Finish`，测试便可以检查第二次调用是否已经包含 `Observation("84")`。动作耗尽时抛出 `FakeModelExhaustedError`，也能直接暴露测试数据配置不足。

## 四、工具契约

最初的注册表只保存函数：

```text
TOOL_REGISTRY = {
    "calculator": run_calculator,
}
```

Runtime 知道怎样执行，模型却看不到工具名称、用途和参数规则。于是需要把“给模型看的说明”和“只能由 Runtime 使用的函数”分开表达。

### （一）ToolSpec

`ToolSpec` 保存可序列化的工具说明：

```text
@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Mapping[str, object]
    output_description: str
    error_description: str
```

calculator 的输入 Schema 规定三个必需字段，并拒绝额外字段：

```text
CALCULATOR_SPEC = ToolSpec(
    name="calculator",
    description=(
        "Perform one binary arithmetic operation. Supports add, "
        "subtract, multiply, and divide."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "left": {"type": "number"},
            "operation": {
                "type": "string",
                "enum": [
                    "add",
                    "subtract",
                    "multiply",
                    "divide",
                ],
            },
            "right": {"type": "number"},
        },
        "required": ["left", "operation", "right"],
        "additionalProperties": False,
    },
    output_description="The arithmetic result encoded as a string.",
    error_description=(
        "Rejects missing or extra arguments, invalid types, "
        "unsupported operations, and division by zero."
    ),
)
```

`additionalProperties: false` 表示不允许拼错的 `rigth`，也不允许契约之外的 `precision`、`command` 等字段。`operation` 使用固定 `enum`，因为 calculator 只实现了四种运算。

### （二）ToolDefinition

Runtime 使用 `ToolDefinition` 把 spec 与 handler 绑定：

```text
@dataclass(frozen=True)
class ToolDefinition:
    spec: ToolSpec
    handler: ToolFunction


TOOL_REGISTRY = {
    CALCULATOR_SPEC.name: ToolDefinition(
        spec=CALCULATOR_SPEC,
        handler=run_calculator,
    ),
}
```

模型只能通过 `get_tool_specs()` 得到 spec，拿不到 Python callable。Runtime 查到同一个 `ToolDefinition` 后，才会调用 `definition.handler()`。

绑定可以减少两个字典之间的名称错配，但不能自动证明 spec 与 handler 的语义完全一致。假如 Schema 增加了 `power`，`run_calculator()` 没有实现它，模型会提出一份符合公开说明的调用，handler 最终仍会抛出 `unsupported operation: power`。这种情况叫契约漂移，需要共享定义或契约测试继续约束。

当前版本把 Schema 提供给模型，尚未接入通用 JSON Schema 校验器。`run_calculator()` 仍保留字段、类型、操作名称和除零校验，它才是当前的权威执行边界。

### （三）错误转换

Runtime 只捕获预期的 `ToolError`：

```text
try:
    content = definition.handler(call.arguments)
except ToolError as error:
    return Observation(
        tool_name=call.tool_name,
        content=str(error),
        is_error=True,
    )
```

除零、未知运算和非法参数属于可恢复的工具失败，可以作为 Observation 返回模型。`NameError`、普通 `RuntimeError` 等程序缺陷继续向上抛出，让测试和日志暴露问题。

## 五、模型适配

`Model.next_action()` 返回的是内部 `Action`，真实模型服务通常先返回文本、JSON 或 provider 自己的 tool-calling 结构。谁负责把这些格式统一起来？

答案是模型适配器。

```text
provider 原始响应
        ↓
具体 Model adapter
        ↓
ToolCall | Finish
        ↓
Agent Loop
```

不同 provider 可以分别实现同一个 `Model` Protocol。Loop 始终只处理内部类型，不需要堆积 `if provider == ...`。

### （一）RawJsonModel

最小实验先定义一个返回原始 JSON 文本的接口：

```text
class RawJsonModel(Protocol):
    def next_response(
        self,
        task: Task,
        history: Sequence[HistoryItem],
    ) -> str:
        ...
```

测试中的 `FakeRawJsonModel` 没有显式继承这个 Protocol，只要 `next_response()` 的名称、参数和返回类型一致，mypy 就会把它视为结构子类型。

### （二）JsonModelAdapter

adapter 获取原始文本，再把它严格转换成内部 Action：

```text
class JsonModelAdapter:
    def __init__(self, raw_model: RawJsonModel) -> None:
        self._raw_model = raw_model

    def next_action(
        self,
        task: Task,
        history: Sequence[HistoryItem],
    ) -> Action:
        raw_response = self._raw_model.next_response(
            task,
            history,
        )
        return parse_json_action(raw_response)
```

它只接受两种结构：

```text
{"type":"tool_call","tool_name":"calculator","arguments":{"left":12,"operation":"multiply","right":7}}
{"type":"finish","answer":"12 * 7 = 84，84大于80。"}
```

非法 JSON、缺少字段、多出字段、未知 action type 和错误字段类型都会变成公共的 `InvalidModelOutputError`。这个异常定义在 Model 接口层，Loop 无需依赖某个具体 adapter 的异常类。

adapter 负责发现格式错误，Loop 负责决定是否重试。第一次输出非法且仍有预算时，Loop 将错误转换成 `ModelFeedback`；预算耗尽后，以 `invalid_model_output` 结束。

## 六、运行循环

加入结构化结果、模型反馈和轨迹后，核心链路仍然没有变化：

```text
调用模型
  ├─ Finish → finished
  ├─ ToolCall → 执行工具 → Observation → 下一轮
  └─ InvalidModelOutputError
       ├─ 有预算 → ModelFeedback → 下一轮
       └─ 无预算 → invalid_model_output
```

简化后的代码如下：

```text
def run_agent_result(
    task: Task,
    model: Model,
    *,
    max_steps: int = 5,
) -> RunResult:
    history: list[HistoryItem] = []

    for step in range(1, max_steps + 1):
        try:
            action = model.next_action(task, history)
        except InvalidModelOutputError as error:
            history.append(ModelFeedback(content=str(error)))
            if step == max_steps:
                return RunResult(
                    exit_reason=ExitReason.INVALID_MODEL_OUTPUT,
                    answer=None,
                    steps_used=step,
                    error=str(error),
                )
            continue

        if isinstance(action, Finish):
            return RunResult(
                exit_reason=ExitReason.FINISHED,
                answer=action.answer,
                steps_used=step,
            )

        history.append(action)
        history.append(execute_tool(action))

    return RunResult(
        exit_reason=ExitReason.MAX_STEPS_EXCEEDED,
        answer=None,
        steps_used=max_steps,
    )
```

以“计算 `12 × 7`，并判断是否大于 `80`”为例：

```text
第 1 轮
  FakeModel → ToolCall(calculator, 12, multiply, 7)
  Runtime   → 执行 calculator
  Tool      → "84"
  Runtime   → Observation(content="84", is_error=False)

第 2 轮
  FakeModel → Finish("12 * 7 = 84，84大于80。")
  Loop      → RunResult(exit_reason="finished")
```

第二次调用 `model.next_action()` 时，第一轮的 `ToolCall` 和 `Observation` 会一起传入。真实模型可以根据 `84` 决定下一步；当前 `FakeModel` 只会返回预先准备好的 `Finish`。

## 七、失败与退出

失败需要先判断它属于哪一层，再决定是否继续。

| 情况 | 处理 | 是否继续 |
| --- | --- | --- |
| 未知工具 | 错误 Observation | 预算允许时继续 |
| calculator 除零 | 错误 Observation | 预算允许时继续 |
| 模型首次输出非法 JSON | ModelFeedback | 预算允许时重试 |
| 模型持续输出非法 JSON | invalid_model_output | 终止 |
| 步数耗尽 | max_steps_exceeded | 终止 |
| handler 抛出意外 RuntimeError | 记录 internal_error 后重新抛出 | 终止并等待修复 |

预期工具失败不一定说明工具代码有缺陷。它也可能来自模型参数、用户输入或外部服务的暂时故障。只要失败类型已经写进工具契约，并且下一轮仍有恢复空间，就可以交给模型调整动作。

程序缺陷采用另一条路径。Loop 会为轨迹写入 `internal_error`，随后继续抛出异常，避免调用者把一次崩溃误认为正常完成。

步数耗尽也值得单独处理。它是 Agent 系统预先允许出现的运行结果，说明模型没能在预算内完成任务。评测时应把它和基础设施故障分开统计。

## 八、JSONL 轨迹

只有最终答案，很难回答“模型第几步调用了什么工具”“错误从哪里产生”“预算为什么耗尽”。因此每次运行还需要一条可追踪的事件链。

JSONL 每行保存一个完整 JSON 对象：

```text
{"run_id":"r1","step":0,"event_type":"run_started","input_summary":"chars=18;sha256=..."}
{"run_id":"r1","step":1,"event_type":"model_action","action_type":"tool_call","tool_name":"calculator","argument_keys":["left","operation","right"]}
{"run_id":"r1","step":1,"event_type":"observation","output":"chars=2;sha256=...","is_error":false}
{"run_id":"r1","step":2,"event_type":"model_action","action_type":"finish","output":"chars=22;sha256=..."}
{"run_id":"r1","step":2,"event_type":"run_finished","exit_reason":"finished"}
```

所有事件共享 `run_id`。同一次工具调用及其 Observation 使用相同的 `step`，这样可以顺藤摸瓜找到动作与结果的对应关系。

### （一）追加写入

`JsonlTraceWriter` 每次只追加一个完整对象：

```text
class JsonlTraceWriter:
    def append(self, event: RunEvent) -> None:
        with self._path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            json.dump(
                event.to_record(),
                stream,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            stream.write("\n")
```

进程中途崩溃时，前面已经写完的行仍然是独立事件。与一次性在结尾写入整段运行数据相比，这种格式更容易找到最后一个成功步骤。

### （二）安全摘要

轨迹可能接触任务、源代码、工具参数和模型输出。普通日志没有理由保存所有原文，当前实现采用保守摘要：

```text
任务与文本输出 → 字符数 + SHA-256
工具参数       → 只记录参数键
handler        → 完全不记录
环境变量       → 完全不记录
```

SHA-256 不提供加密能力。低熵内容仍可能被枚举猜出，API key 也不应该把哈希写进普通轨迹。哈希在这里用于一致性识别，不能代替秘密管理。

### （三）只读回放

`trace_show` 只依赖 reader，按文件顺序打印事件：

```text
uv run --project .. python -m minimal_agent.trace_show path\to\run.jsonl
```

查看轨迹不需要写权限。把追加或修改能力放进回放命令没有业务价值，还会增加误改审计证据的风险。

## 九、测试边界

测试仍然按模块拆分：

| 测试文件 | 验证内容 |
| --- | --- |
| test_models.py | 数据对象、Action 与 history item |
| test_model.py | FakeModel 顺序、历史记录和耗尽错误 |
| test_tools.py | calculator 结果、契约和参数错误 |
| test_runtime.py | spec-handler 绑定、白名单和错误 Observation |
| test_agent.py | 完整循环、结构化结果和最大步数 |
| test_json_model.py | JSON 解析、非法输出、反馈重试和终止 |
| test_trace.py | 事件顺序、安全摘要、退出原因和只读回放 |

最重要的历史断言仍然保留：

```text
assert model.calls == [
    (task, ()),
    (
        task,
        (
            tool_call,
            Observation(
                tool_name="calculator",
                content="84",
                is_error=False,
            ),
        ),
    ),
]
```

它证明了第一轮历史为空、工具动作被保存、执行结果变成 Observation，并且两者一起进入第二轮模型上下文。

轨迹测试还会检查完整事件顺序：

```text
run_started
model_action(tool_call)
observation
model_action(finish)
run_finished(finished)
```

内部异常测试则要求先写入 `internal_error`，随后仍然抛出原异常。只记录不抛出会隐藏程序缺陷，只抛出不记录又会失去运行证据。

项目使用两个命令验证实现：

```text
uv run --project .. python -m pytest -q -p no:cacheprovider
uv run --project .. python -m mypy minimal_agent tests
```

当前结果为 `33 passed`，mypy 严格检查 `17` 个源文件无错误。pytest 检查运行行为，mypy 检查 Protocol、联合类型和函数签名，两者解决的问题不同。

## 十、Code Agent 映射

把计算器替换成代码工具，就得到 Code Agent 的基本轮廓：

| 最小循环 | Code Agent |
| --- | --- |
| Task | 修复 issue、实现功能、解释仓库 |
| ToolSpec | 文件工具的名称、说明、参数 Schema 和错误契约 |
| ToolCall | 搜索、读取、编辑、运行测试 |
| ToolDefinition | 模型可见 spec 与受控 handler 的绑定 |
| Observation | 文件摘要、搜索结果、diff、stdout、stderr、退出码 |
| ModelFeedback | 非法模型输出的纠正信息 |
| Finish | 最终说明、补丁结果或无法完成的原因 |
| RunResult | 完成、预算耗尽或模型输出失败 |
| JSONL 轨迹 | 动作、耗时、错误、退出原因和安全审计记录 |
| Model Protocol | OpenAI、Claude、本地模型或回放模型适配器 |

模型说“测试已经通过”不能成为环境事实。控制程序需要真的调用测试工具，再把退出码和输出转换成 Observation。模型读取这份反馈后，才能决定继续修复还是提出 `Finish`。

一句话概括就是：模型负责选择行动，适配器负责统一格式，Runtime 负责守住能力边界，工具负责改变或读取环境，Observation 负责把事实带回下一轮，轨迹负责留下可以复查的证据。

相关资料：

- [Hugging Face Agents Course：Actions](https://huggingface.co/learn/agents-course/zh-CN/unit1/actions)
- [Hugging Face Agents Course：Observations](https://huggingface.co/learn/agents-course/zh-CN/unit1/observations)
- [Python 3.12：typing.Protocol](https://docs.python.org/3.12/library/typing.html#typing.Protocol)
- [Python 3.12：dataclasses](https://docs.python.org/3.12/library/dataclasses.html)
- [ReAct：Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
