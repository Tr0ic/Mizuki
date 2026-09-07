---
title: "从零搭建 Code Agent：Tool Registry、Runtime 与权限控制"
published: 2026-09-01T20:33:12+08:00
updated: 2026-09-01T20:33:12+08:00
description: "设计 Code Agent 的工具注册表、运行时与权限策略，说明工具准备、执行、一次性批准和错误转换如何统一管理。"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2078218269295634047"
draft: false
pinned: false
---

## 目录

- [一、模块关系](#一模块关系)
- [二、工具契约](#二工具契约)
  - [（一）ToolSpec](#一toolspec)
  - [（二）ToolDefinition](#二tooldefinition)
- [三、注册与准备](#三注册与准备)
  - [（一）ToolRegistry](#一toolregistry)
  - [（二）prepare 与 execute](#二prepare-与-execute)
- [四、权限策略](#四权限策略)
- [五、一次性批准](#五一次性批准)
  - [（一）拒绝覆盖](#一拒绝覆盖)
  - [（二）只消费一次](#二只消费一次)
  - [（三）批准后的复查](#三批准后的复查)
- [六、统一控制](#六统一控制)
- [七、错误边界](#七错误边界)
- [八、测试与限制](#八测试与限制)

Model Adapter 已经把模型响应转换成 `ToolCall`，接下来还差一步：确认工具并把结果交回模型。

直接根据 `tool_name` 调用 Python 函数，等于把模型生成的字符串接到了本地执行入口。Tool 板块要在中间加上几道明确的检查，让模型保留行动提议权，让运行时掌握实际执行权。

当前实现包含五个 Module：`ToolRegistry`、`ToolRuntime`、`ToolPolicy`、`PendingApprovals` 和 `ToolController`。它们共同完成下面这条链路：

```text
ToolCall
   ↓
查找工具并校验参数
   ↓
PreparedToolCall
   ↓
PolicyDecision
   ├─ allow → 执行 handler → ToolResult
   ├─ ask   → ApprovalRequest
   └─ deny  → 错误 ToolResult
```

## 一、模块关系

Tool 板块面对两类信息。模型需要知道工具叫什么、有什么用途、参数长什么样；运行时还需要参数校验器和真正执行操作的 Python handler。

把这些职责放进同一个函数，会让公开契约、权限判断和实际执行缠在一起。当前实现沿调用顺序拆开：

| Module | 职责 |
| --- | --- |
| ToolRegistry | 保存工具定义，暴露模型可见的 specs，根据名称解析工具 |
| ToolRuntime | 校验工具调用，执行已经准备好的 handler，转换预期错误 |
| ToolPolicy | 根据配置返回 allow / ask / deny |
| PendingApprovals | 保存并一次性消费等待用户确认的请求 |
| ToolController | 按顺序组合准备、Policy、批准与执行 |

最外层只需要调用：

```python
outcome = controller.handle(call)
```

返回值可能是 `ToolResult`，也可能是等待用户处理的 `ApprovalRequest`。调用者无需分别操作 Registry、Runtime 和 Policy。

## 二、工具契约

### （一）ToolSpec

`ToolSpec` 是模型能够看到的工具说明：

```python
@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Mapping[str, object]
```

例如 calculator 可以声明两个整数参数：

```python
ToolSpec(
    name="calculator",
    description="Add exactly two integers named a and b.",
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
        },
        "required": ["a", "b"],
        "additionalProperties": False,
    },
)
```

模型读取这份 Schema 后可以生成结构化参数，但 Schema 本身不会执行校验。模型也可能忽略说明、拼错字段或给出错误类型，所以本地运行时仍要保留权威校验。

### （二）ToolDefinition

`ToolDefinition` 把公开说明与运行时实现绑定：

```python
@dataclass(frozen=True)
class ToolDefinition:
    spec: ToolSpec
    validate_arguments: ToolArgumentValidator
    handler: ToolHandler
```

其中：

- `spec` 提供给模型；
- `validate_arguments` 检查本地执行契约；
- `handler` 完成真正的环境操作。

模型只能取得 `ToolSpec`，拿不到 Python callable。即使模型生成了 `{"tool_name": "calculator"}`，也必须经过 Registry、参数校验和 Policy，才能到达 handler。

## 三、注册与准备

### （一）ToolRegistry

`ToolRegistry` 在初始化时把定义按名称保存：

```python
for definition in definitions:
    name = definition.spec.name
    if name in definitions_by_name:
        raise DuplicateToolError(
            f"duplicate tool name: {name}"
        )
    definitions_by_name[name] = definition
```

重复名称必须立即失败。假如两个 handler 都叫 `read_file`，运行时无法稳定判断应该执行哪一个，覆盖旧值只会把配置错误藏起来。

Registry 对外提供两个入口：

```python
registry.specs
registry.resolve("read_file")
```

`specs` 用于构造模型请求，`resolve()` 用于运行时查找完整定义。未知名称会抛出 `UnknownToolError`，随后由 Runtime 转换成模型可见的错误结果。

### （二）prepare 与 execute

`ToolRuntime` 把查找、校验和执行拆成两步：

```text
prepare(call) → PreparedToolCall | ToolResult
execute(prepared) → ToolResult
```

`prepare()` 先解析工具名称，再调用参数校验器。未知工具或非法参数会直接得到错误 `ToolResult`：

```python
ToolResult(
    call_id=call.call_id,
    content="unknown tool: delete_everything",
    is_error=True,
)
```

通过检查后返回 `PreparedToolCall`，其中保存原调用和对应的 `ToolDefinition`。

这里有一个容易混淆的地方：prepared 只表示“工具存在，参数通过校验”，没有表示“允许执行”。权限判断仍在下一步。这样的拆分给 Policy 留出了一条清楚的 seam：

```text
参数校验完成
    ↓
权限判断
    ↓
实际执行
```

## 四、权限策略

`ToolPolicy` 返回三种决策：

```python
class PolicyAction(StrEnum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"
```

配置可以写成：

```python
ToolPolicy(
    allowed_tools={"read_file"},
    confirmation_required_tools={"apply_patch"},
)
```

此时：

| 工具 | 决策 |
| --- | --- |
| read_file | ALLOW，可以直接执行 |
| apply_patch | ASK，等待用户确认 |
| 其他名称 | DENY，默认拒绝 |

默认拒绝很重要。新增工具如果没有同步权限配置，会停在 `DENY`，不会因为遗漏配置自动获得执行权。

同一个工具也不能同时出现在 allow 和 ask 集合中。初始化时发现重叠会直接抛出 `ValueError`，避免一次调用同时匹配两套互相冲突的规则。

`PolicyDecision` 还会保存非空 `reason`。Controller 可以把拒绝原因放进 `ToolResult`，也可以把确认原因交给用户界面或未来的 EventStore。

## 五、一次性批准

Policy 返回 `ASK` 时，Controller 会创建 `ApprovalRequest`，handler 此时不会执行：

```python
ApprovalRequest(
    approval_id="approval_1",
    call=call,
    reason="tool requires user confirmation",
)
```

请求随后进入 `PendingApprovals`。这里保存的是原始 `ToolCall`，用户批准时才能知道具体允许了哪次调用。

### （一）拒绝覆盖

两个待确认请求不能共用同一个 `approval_id`。如果后来的请求覆盖前一个，用户看到的是读取 README，实际取出的调用却可能已经变成读取其他文件。`add()` 遇到重复 ID 会抛出 `DuplicateApprovalError`，原请求继续保留。

### （二）只消费一次

`resolve()` 使用 `pop()` 取出请求：

```python
request = self._pending.pop(response.approval_id)
```

无论批准还是拒绝，请求都会从待处理集合中消失。同一个响应再次提交时得到 `UnknownApprovalError`，handler 也不会执行第二次。

### （三）批准后的复查

等待确认期间，Registry 或 Policy 可能已经变化。Controller 收到批准后会重新解析工具、重新校验参数，并再次执行 Policy。

如果当前策略已经变成 `DENY`，之前的批准不能覆盖这条硬限制。当前策略仍为 `ASK` 或已经变成 `ALLOW` 时，调用才会进入 Runtime。

## 六、统一控制

`ToolController.handle()` 把前面的 Module 按安全顺序接起来：

```python
preparation = self._runtime.prepare(call)
if isinstance(preparation, ToolResult):
    return preparation

decision = self._policy.decide(preparation.call)

if decision.action is PolicyAction.ALLOW:
    return self._runtime.execute(preparation)

if decision.action is PolicyAction.DENY:
    return ToolResult(
        call_id=preparation.call.call_id,
        content=decision.reason,
        is_error=True,
    )

request = ApprovalRequest(...)
self._pending_approvals.add(request)
return request
```

这条链路中只有两个位置可以到达 `runtime.execute()`：Policy 直接返回 `ALLOW`，或者一次有效批准完成复查。模型输出、未知工具、非法参数、拒绝决定和等待确认都无法直接执行 handler。

`call_id` 会原样进入每个 `ToolResult`。下一轮模型拿到结果后，可以把它与此前的 `ToolCall` 对应起来。

真实 DeepSeek calculator 烟测也经过了这条链路：模型提出带 Provider `call_id` 的 calculator 调用，Controller 允许执行，本地 handler 返回 `42`，结果写回 history 后，模型才生成最终答案。

## 七、错误边界

Tool 板块需要区分“模型可以看到的预期失败”和“程序应该暴露的实现缺陷”。

| 情况 | 处理结果 |
| --- | --- |
| 工具未注册 | 错误 ToolResult |
| 参数校验器抛出 InvalidToolArgumentsError | 错误 ToolResult |
| Policy 返回 DENY | 错误 ToolResult，不执行 handler |
| 用户拒绝批准 | 错误 ToolResult，不执行 handler |
| handler 抛出 ToolExecutionError | 错误 ToolResult |
| handler 抛出意外 AttributeError 等异常 | 原异常继续向上抛出 |

文件不存在、参数无效等情况可以成为下一轮模型的环境反馈。代码内部的 `AttributeError` 通常说明实现有缺陷，如果统一包装成工具错误，Agent 可能继续循环，并把程序崩溃误解成一次普通操作失败。

错误 `ToolResult` 也保留原 `call_id`：

```python
ToolResult(
    call_id="call_3",
    content="file not found",
    is_error=True,
)
```

模型可以根据这份结果调整参数或选择其他工具，Loop 再决定是否继续。

## 八、测试与限制

Tool 板块目前由五组测试覆盖：

| 测试文件 | 主要行为 |
| --- | --- |
| test_tool_registry.py | specs、定义解析、重复名称、未知工具 |
| test_tool_runtime.py | prepare、执行、预期错误转换、意外异常传播 |
| test_tool_policy.py | allow / ask / deny、默认拒绝、冲突配置 |
| test_tool_approval.py | 请求保存、拒绝覆盖、批准和拒绝的一次性消费 |
| test_tool_controller.py | 允许执行、拒绝、等待确认、单次批准执行 |

验证命令：

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider `
    tests\test_tool_registry.py `
    tests\test_tool_runtime.py `
    tests\test_tool_policy.py `
    tests\test_tool_approval.py `
    tests\test_tool_controller.py
```

当前结果为 `21 passed`。整个 Agent Kernel 当前为 `124 passed`，mypy 严格检查 32 个源文件无错误。

现阶段还有几个明确限制：

- Policy 只根据工具名称判断，没有检查路径、参数值和运行环境风险。
- 待确认请求只保存在内存中，进程重启后无法恢复。
- 批准请求、Policy 决策和工具执行尚未写入新的 EventStore。
- 批准后重新校验以及策略变化路径还需要补充集成测试。
- ToolController 尚未接入正式 Agent Loop，目前真实闭环由 smoke 脚本编排。

Tool 板块的核心关系可以压缩成一句话：模型提出 `ToolCall`，Registry 解析能力，Runtime 验证并执行，Policy 决定权限，Approval 保存一次性确认，Controller 保证这些步骤按顺序发生。

相关代码：

- `tool_registry.py`
- `tool_runtime.py`
- `tool_policy.py`
- `tool_approval.py`
- `tool_controller.py`gent Loop，目前真实闭环由 smoke 脚本编排。

Tool 板块的核心关系可以压缩成一句话：模型提出 `ToolCall`，Registry 解析能力，Runtime 验证并执行，Policy 决定权限，Approval 保存一次性确认，Controller 保证这些步骤按顺序发生。

相关代码：

- [`tool_registry.py`](<https://github.com/Mem0rin/Issue-to-Patch-Code-Agent/blob/main/src/code_agent/tool_registry.py>)

- [`tool_runtime.py`](<https://github.com/Mem0rin/Issue-to-Patch-Code-Agent/blob/main/src/code_agent/tool_runtime.py>)

- [`tool_policy.py`](<https://github.com/Mem0rin/Issue-to-Patch-Code-Agent/blob/main/src/code_agent/tool_policy.py>)

- [`tool_approval.py`](<https://github.com/Mem0rin/Issue-to-Patch-Code-Agent/blob/main/src/code_agent/tool_approval.py>)

- [`tool_controller.py`](<https://github.com/Mem0rin/Issue-to-Patch-Code-Agent/blob/main/src/code_agent/tool_controller.py>)
