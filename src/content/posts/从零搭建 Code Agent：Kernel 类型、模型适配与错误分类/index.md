---
title: "从零搭建 Code Agent：Kernel 类型、模型适配与错误分类"
published: 2026-08-26T21:35:36+08:00
updated: 2026-08-26T21:35:36+08:00
description: "为 Code Agent 定义统一的 Kernel 数据类型与模型适配协议，并区分服务商错误、模型输出错误和测试替身耗尽等失败情况。"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2076058859844776739"
draft: false
pinned: false
---

## 目录

- [一、Kernel 类型](#一kernel-类型)
  - [（一）Action 与 History](#一action-与-history)
  - [（二）call_id](#二call_id)
  - [（三）局部不变量](#三局部不变量)
- [二、Model Adapter](#二model-adapter)
  - [（一）Protocol](#一protocol)
  - [（二）FakeModelAdapter](#二fakemodeladapter)
- [三、错误分类](#三错误分类)
  - [（一）Provider 错误](#一provider-错误)
  - [（二）模型输出错误](#二模型输出错误)
  - [（三）Fake 耗尽](#三fake-耗尽)

现在开始是正式的项目搭建了，我会尽量省略前面已经讲过的内容，但是会保留必要的部分。

## 一、Kernel 类型

**Kernel 类型**是 Agent 内部传递消息、行动和工具结果时使用的统一语言。它们与具体 provider 无关，OpenAI、Claude 或本地模型接入后都要转换成这些类型。

当前版本定义了四个主要对象：

| 类型 | 作用 |
| --- | --- |
| Message | 保存一条带角色的对话消息 |
| ToolCall | 表示模型提出的一次工具调用 |
| ToolResult | 保存工具执行结果或错误 |
| FinalAnswer | 表示模型提出的最终回答 |

### （一）Action 与 History

模型每轮可以提出两种行动：调用工具，或者给出最终回答。

```python
Action: TypeAlias = ToolCall | FinalAnswer
```

`Action` 是类型别名，不会创建新的包装对象。模型返回的实际对象仍然是 `ToolCall` 或 `FinalAnswer`，控制程序可以使用 `isinstance()` 判断下一步。

模型下一轮需要看到之前的对话和工具交互，因此 history 包含三种对象：

```text
HistoryItem: TypeAlias = Message | ToolCall | ToolResult
```

为什么 history 既要保存 `ToolCall`，又要保存 `ToolResult`？因为只记录结果会丢失模型上一轮做了什么。完整历史应该保留行动与观察结果：

```text
Message
→ ToolCall(call_id="call_1")
→ ToolResult(call_id="call_1")
→ 下一轮模型调用
```

模型读取这两条记录后，才能知道哪次调用产生了什么结果。

### （二）call_id

同一个工具可能在一轮任务中被调用多次，只依赖工具名无法区分结果。`call_id` 相当于一次调用的编号：

```text
ToolCall(
    call_id="call_1",
    tool_name="read_file",
    arguments={"path": "README.md"},
)

ToolResult(
    call_id="call_1",
    content="README contents",
    is_error=False,
)
```

两边使用同一个 `call_id`，工具结果就能准确对应到原调用。后续即使连续执行多个 `read_file`，也不会把结果接错。

### （三）局部不变量

这些类型使用 `frozen=True` 的 dataclass，并在 `__post_init__()` 中检查非空字段：

```text
def _require_non_blank(
    value: str,
    field_name: str,
) -> None:
    if not value.strip():
        raise ValueError(
            f"{field_name} must not be blank"
        )
```

例如 `ToolCall` 可以独立确认 `call_id` 和 `tool_name` 不能是空白字符串。它无法确认 history 中是否存在匹配的 `ToolResult`，因为创建对象时看不到整段 history。

单个类型只维护自己能够判断的局部不变量。跨对象的顺序、配对和状态关系，留给后续 Kernel 逻辑统一检查。

## 二、Model Adapter

Provider 是实际提供模型能力的平台。Model Adapter 位于 provider 与 Kernel 之间，负责把双方使用的数据格式互相转换：

```text
Kernel history、ToolSpec、budget
              ↓
       具体 Model Adapter
              ↓
        provider 请求格式

        provider 原始响应
              ↓
       具体 Model Adapter
              ↓
          ModelResponse
```

Kernel 只依赖统一的 `ModelAdapter` Interface：

```text
class ModelAdapter(Protocol):
    def complete(
        self,
        history: Sequence[HistoryItem],
        tools: Sequence[ToolSpec],
        budget: ModelCallBudget,
    ) -> ModelResponse:
        ...
```

一次调用需要当前 history、允许使用的工具说明和输出预算。返回值统一打包行动与 token usage：

```text
@dataclass(frozen=True)
class ModelResponse:
    action: Action
    usage: TokenUsage
```

`response_id`、provider 模型名和原始 headers 等字段可能只对具体平台有意义。Adapter 可以在内部使用它们，Kernel 只接收控制循环真正需要的 `action` 与 `usage`。这样可以把 provider 差异集中在一个位置。

### （一）Protocol

`ModelAdapter` 继承 `Protocol`，主要描述对象需要具备什么能力。类无需显式继承它，只要 `complete()` 的参数和返回类型兼容，mypy 就可以把这个对象视为 `ModelAdapter`。

这是一种带静态检查的鸭子类型。未来的 OpenAI Adapter、其他 provider Adapter 和测试 Fake 都可以接在同一个位置，Kernel 的调用方式保持不变。

### （二）FakeModelAdapter

真实模型不会提前保存未来行动。测试需要稳定地复现“先调用工具，再完成任务”这类路径，所以 `FakeModelAdapter` 保存了一组预设结果：

```text
fake = FakeModelAdapter([
    tool_response,
    final_response,
])
```

它内部使用三个状态：

- `_outcomes` 保存预设的响应或错误。
- `_index` 指向下一次应该读取的位置。
- `calls` 保存每次传入的 history、tools 和 budget。

每次调用时，Fake 先记录参数，再按照 `_index` 取出一个结果并推进位置。`_outcomes` 和 `_index` 只属于测试实现；真实 Adapter 会在每次 `complete()` 时请求 provider。

`calls` 也不是生产轨迹。它是 Fake 提供给测试的观察面，可以验证第二轮模型调用是否收到了第一轮的 `ToolCall` 和 `ToolResult`。记录时把可变序列转换成 tuple，还能避免调用结束后修改原列表，导致历史快照跟着变化。

## 三、错误分类

模型调用失败时，先判断错误来自 provider、模型输出，还是测试实现本身。三种情况的恢复方式不同，不能压成同一个普通字符串。

| 情况 | 统一错误 | 含义 |
| --- | --- | --- |
| provider 返回 HTTP 503 | ModelProviderError | 请求没有得到可用的模型响应 |
| 响应无法转换成合法 Action | InvalidModelOutputError | provider 有响应，但内容不符合 Kernel 动作契约 |
| Fake 没有剩余预设结果 | FakeModelExhaustedError | 测试数据不足或程序调用次数超出预期 |

### （一）Provider 错误

HTTP 503、连接失败和超时都发生在与 provider 通信的过程中。具体 Adapter 应把底层客户端异常转换成 `ModelProviderError`，这样 Kernel 无需依赖某个 HTTP 库的异常类型。

这类错误说明当前没有得到可用响应，不能生成 `Action`。是否重试、退避或结束，后续由 Kernel 的预算与策略决定。

### （二）模型输出错误

Provider 成功返回内容，也不代表内容一定能成为 Kernel Action。例如工具参数的 JSON 解析结果是数组：

```text
[1, 2]
```

它是合法 JSON，却不符合工具参数要求的 object 结构，因此应该转换成 `InvalidModelOutputError`。同一类错误还包括未知 action type、缺少通用字段和空白 `call_id`。

Adapter 只检查通用 Action 契约。假设 `read_file` 收到 `{"path": 123}`，外层仍然可以成为 `ToolCall`；`path` 的业务类型应由 runtime 参数校验或具体工具处理。

### （三）Fake 耗尽

`FakeModelAdapter` 的预设结果耗尽时，会抛出：

```text
FakeModelExhaustedError(
    "fake model has no configured outcome left"
)
```

这个异常通常说明测试只准备了一个结果，控制流程却调用了模型两次。也可能是循环出现了意外路径。它属于测试或程序缺陷，应直接暴露给测试。

如果耗尽时自动返回 `FinalAnswer`，一次未完成的测试就可能显示为正常结束。Fake 没有模型意图，也不能替模型决定终止。

到这里，模型调用路径可以压缩成一条稳定链路：

```text
provider 原始响应
→ Adapter 转换
→ ModelResponse 或统一错误
→ Kernel 控制流程
```

Kernel 使用统一类型组织行动和历史，Adapter 吸收 provider 格式差异，错误类型保留失败来源。后续接入真实模型时，只需要在这个 Interface 后增加具体 Adapter。
