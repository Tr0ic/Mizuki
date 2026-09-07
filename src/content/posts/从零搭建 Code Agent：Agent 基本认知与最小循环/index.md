---
title: "从零搭建 Code Agent：Agent 基本认知与最小循环"
published: 2026-08-16T18:09:06+08:00
updated: 2026-08-16T18:09:07+08:00
description: "目录"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2072383147002566533"
draft: false
pinned: false
---

## 目录

- [一、三个基本概念](#一三个基本概念)
  - [（一）LLM](#一llm)
  - [（二）固定工作流](#二固定工作流)
  - [（三）Agent](#三agent)
- [二、Agent 的组成](#二agent-的组成)
- [三、最小数据流](#三最小数据流)
- [四、动作与观察](#四动作与观察)
  - [（一）动作](#一动作)
  - [（二）观察](#二观察)
  - [（三）最终答案](#三最终答案)
- [五、循环模拟](#五循环模拟)
- [六、停止条件](#六停止条件)
- [七、Code Agent 的对应关系](#七code-agent-的对应关系)

## 一、三个基本概念

### （一）LLM

**LLM** 是经过大量文本训练的语言模型。它接收上下文并生成输出，本身不会直接读取文件、执行命令或访问网络。

模型当然可以输出下面这段内容：

```text
{
  "type": "tool",
  "name": "calculator",
  "arguments": {"x": 12, "y": 7}
}
```

这只是一个结构化提议。是否允许调用、参数是否有效、工具能否执行，都要由模型外部的程序处理。

### （二）固定工作流

**固定工作流** 的步骤由开发者提前确定。例如：

```text
LLM 提取关键词 → 搜索数据库 → LLM 生成摘要
```

这里虽然调用了两次 LLM，也经过了搜索，下一步仍由代码预先安排。程序可以有分支、循环和异常处理，这些结构不会自动把工作流变成 Agent。

判断时只需要追问一个问题：运行过程中，模型能否根据新的观察结果选择下一步动作？如果每条路径都已经写进程序，它更接近固定工作流。

模型自己选择一次工具，已经拥有一定的行动决定权，可以称为单步工具调用 Agent。它还没有把观察送回模型进行第二次决策，因此没有形成多步 Agent Loop。

### （三）Agent

**Agent** 是一个能够理解任务、选择行动并与环境交互的系统。模型拥有的是提议权：根据任务和观察选择 `action`，或者提出 `final`。真正的执行权和终止权仍留在控制程序中。

把 LLM 比作大脑、工具比作四肢时，中间还缺少一套神经与控制系统。Agent 控制程序负责实现循环，把模型、工具和环境连接起来，同时限制每个动作的权限与预算。

Agent 可以概括为：

```text
Agent = 模型决策 + 控制程序 + 工具 / 环境 + 观察反馈
```

## 二、Agent 的组成

Agent 是整个功能系统，Agent 控制程序只是其中负责协调与约束的部分。这个控制程序也常被称为 runtime，即运行时。

| 组成 | 主要职责 | 边界 |
| --- | --- | --- |
| 模型 | 读取任务和历史，提出 action 或 final | 不能直接制造环境事实 |
| 控制程序 | 解析、校验、授权、调用工具、记录历史、执行停止条件 | 不能把模型的文字当成工具已经成功 |
| 工具 | 接收已经校验的参数并执行具体功能 | 只负责自己的调用范围 |
| 环境 | 文件系统、终端、网络、数据库等真实状态 | 变化必须通过可检查结果体现 |
| 观察 | 把工具结果或错误统一反馈给模型 | 应标明成功、失败及来源 |

这里最容易混淆的是“谁发现错误”和“谁拒绝执行”。以不存在的工具名为例，工具根本不会被调用。控制程序检查工具注册表后发现错误，拒绝这次动作，再生成失败观察交给模型。

同样，模型输出“文件已经修改”也不能证明环境发生了变化。只有文件工具的返回结果、Git diff 或测试退出码，才能作为环境事实。

## 三、最小数据流

一次多步 Agent 调用可以拆成下面这条链路：

```text
用户任务
  ↓
Agent 控制程序
  ↓  任务 + 历史 + 工具说明
模型
  ↓  action 或 final
Agent 控制程序
  ↓  校验后的工具名与参数
工具 / 环境
  ↓  原始结果或异常
Agent 控制程序
  ↓  统一格式的 observation
模型
  ↓  下一个 action 或 final
Agent 控制程序
  ↓
结果或停止错误
```

各阶段传递的内容并不相同：

| 方向 | 传递内容 |
| --- | --- |
| 用户 → 控制程序 | 任务需求 |
| 控制程序 → 模型 | 用户输入、历史、观察、工具描述和约束 |
| 模型 → 控制程序 | 结构化动作或最终答案 |
| 控制程序 → 工具 | 已通过校验的工具名和参数 |
| 工具 → 控制程序 | 原始结果或异常 |
| 控制程序 → 模型 | 统一格式的观察结果 |

模型看到的是控制程序整理后的上下文。工具返回的原始对象可能很大，也可能包含异常、退出码或敏感内容，控制程序需要先把它转换成模型能够继续处理的观察。

## 四、动作与观察

### （一）动作

`action` 表示模型建议采取的行动，通常至少包含动作类型、工具名和参数：

```text
{
  "type": "tool",
  "name": "calculator",
  "arguments": {"x": 12, "y": 7}
}
```

控制程序收到动作后，应先检查：

1. `type` 是否属于允许的类型；
2. 工具是否已经注册；
3. 参数结构和类型是否符合 schema；
4. 当前权限是否允许这次操作；
5. 步数、时间和费用预算是否充足。

例如模型传来 `{"x": "twelve"}`，而工具要求 `x` 为数字，错误会在函数调用前被发现。工具函数不会进入执行阶段，控制程序直接生成失败观察。

### （二）观察

工具成功时，原始结果会被包装成成功观察：

```text
{
  "type": "observation",
  "ok": true,
  "content": 84
}
```

工具内部发生网络超时，也应回到同一条反馈链路：

```text
{
  "type": "observation",
  "ok": false,
  "content": "network timeout"
}
```

错误没有被删除，也没有悄悄变成成功。模型收到失败观察后，可以提出重试、改用其他工具或结束任务。能否重试以及最多重试几次，仍要服从控制程序的预算。

### （三）最终答案

`final` 表示模型认为任务已经完成，并建议结束循环：

```text
{
  "type": "finish",
  "answer": "84，大于 80"
}
```

它依然是一项提议。控制程序识别该类型后，才会退出循环并把答案交给用户。

## 五、循环模拟

下面用假模型和本地计算器模拟一次完整循环。假模型先提出工具调用，收到观察后再提出最终答案。

```python
class FakeModel:
    def next(self, history):
        last_event = history[-1]

        if last_event["type"] == "task":
            return {
                "type": "tool",
                "name": "calculator",
                "arguments": {"x": 12, "y": 7},
            }

        if last_event["type"] == "observation" and last_event["ok"]:
            result = last_event["content"]
            return {
                "type": "finish",
                "answer": f"{result}，大于 80",
            }

        return {
            "type": "finish",
            "answer": "计算失败",
        }


def calculator(x, y):
    return x * y


def run_agent(model, tools, task, max_steps=4):
    history = [{"type": "task", "content": task}]

    for _ in range(max_steps):
        action = model.next(history)
        print("ACTION:", action)

        if action["type"] == "finish":
            return action["answer"]

        name = action.get("name")
        if action["type"] != "tool" or name not in tools:
            observation = {
                "type": "observation",
                "ok": False,
                "content": "invalid action",
            }
            history.extend([action, observation])
            continue

        try:
            result = tools[name](**action["arguments"])
            observation = {
                "type": "observation",
                "ok": True,
                "content": result,
            }
        except Exception as error:
            observation = {
                "type": "observation",
                "ok": False,
                "content": str(error),
            }

        print("OBSERVATION:", observation)
        history.extend([action, observation])

    raise RuntimeError("step budget exhausted")


answer = run_agent(
    model=FakeModel(),
    tools={"calculator": calculator},
    task="计算 12 × 7，并判断结果是否大于 80。",
)
print("FINAL:", answer)
```

运行结果会经历两轮模型决策：

```text
ACTION: {'type': 'tool', 'name': 'calculator', 'arguments': {'x': 12, 'y': 7}}
OBSERVATION: {'type': 'observation', 'ok': True, 'content': 84}
ACTION: {'type': 'finish', 'answer': '84，大于 80'}
FINAL: 84，大于 80
```

计算器返回 `84` 后不能直接结束，因为工具只完成了动作。这个结果要先作为观察进入历史，再由模型决定如何解释结果。最后，控制程序识别 `finish` 并结束循环。

这段代码只保留循环骨架。真实项目还需要补充参数 schema、权限、超时、调用 ID、脱敏日志和更细的异常类型。

## 六、停止条件

Agent 至少要有软停止与硬停止两类出口。

| 停止类型 | 触发者 | 示例 |
| --- | --- | --- |
| 正常完成 | 模型提出，控制程序执行 | finish / final |
| 步数耗尽 | 控制程序 | max_steps |
| 总时间耗尽 | 控制程序 | 总超时 |
| 费用耗尽 | 控制程序 | token 或费用上限 |
| 策略拒绝 | 控制程序 | 越权路径、危险命令 |
| 不可恢复错误 | 控制程序 | 环境损坏、关键依赖缺失 |

模型可以判断“答案已经足够”，却不能保证自己一定停下。最大步数、总超时和费用上限必须由普通程序客观检查。超过预算时，即使模型还想继续，控制程序也要强制终止并返回明确原因。

## 七、Code Agent 的对应关系

把计算器替换成代码工具，就得到 Code Agent 的基本轮廓：

| 通用结构 | Code Agent 中的实现 |
| --- | --- |
| 任务 | 修复错误、实现功能、解释代码 |
| 动作 | 搜索、读取、编辑、运行测试 |
| 工具 | 文件系统、终端、补丁工具、Git |
| 环境 | 仓库、依赖、操作系统、测试进程 |
| 观察 | 文件内容、命令输出、diff、退出码 |
| 停止 | 完成、预算耗尽、策略拒绝、人工取消 |

这也是为什么模型说“测试通过”还不够。控制程序需要真的运行测试工具，把 stdout、stderr 和退出码包装成观察，再交给模型决定下一步。

相关资料：

- [Hugging Face Agents Course：Introduction to Agents](https://huggingface.co/learn/agents-course/zh-CN/unit1/introduction)
- [Hugging Face Agents Course：Actions](https://huggingface.co/learn/agents-course/zh-CN/unit1/actions)
- [Hugging Face Agents Course：Observations](https://huggingface.co/learn/agents-course/zh-CN/unit1/observations)
- [ReAct：Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)[ReAct：Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
