---
title: "[Agent基础]Agent、消息和聊天模板"
published: 2026-05-29T22:12:47+08:00
updated: 2026-05-29T22:12:50+08:00
description: "介绍 Agent 的基本组成、系统与对话消息的职责，以及聊天模板如何把消息转换成模型可处理的提示词。"
tags: ["Agent", "LLM", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/161491162"
draft: false
pinned: false
---

## 目录

- [一、基本概念](#一基本概念)
  - [什么是 Agent](#什么是-agent)
  - [Agent 的组成](#agent-的组成)
- [二、消息（Message）](#二消息message)
  - [系统消息（System Message）](#系统消息system-message)
  - [对话：用户消息 + 助手消息](#对话用户消息-助手消息)
- [三、聊天模板（Message to prompt）](#三聊天模板message-to-prompt)
  - [什么是聊天模板](#什么是聊天模板)
  - [基础模型和指令模型](#基础模型和指令模型)
  - [消息转换成提示](#消息转换成提示)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，一起进步！

---

---

学习网站来自[Hugging Face](https://huggingface.co/agents-course)，欢迎一起学习交流。

## 一、基本概念

### 什么是 Agent

举一个例子，当有人跟你说“去炒一盘菜”的时候，你会先**理解自然语言**，明白任务是炒一盘菜，然后**推理和规划**出需要用到的**工具**和先后顺序，比如先切菜，再下锅翻炒摆盘，最后再**采取行动**，运用工具完成这一项任务。

我们把**这样能够进行推理、规划和与环境交互的人工智能模型**称为 **agent** 。它具有能动性，即与环境交互的能力。

下面我们给出更加精准的定义：

> *“智能体是一个系统，它利用人工智能模型与环境交互，以实现用户定义的目标。它结合推理、规划和动作执行（通常通过外部工具）来完成任务。”*

### Agent 的组成

Agent 主要由两部分构成：  
 组成：

1. 大脑（AI模型）

AI模型负责推理和规划根据情况决定采取哪些行动，常见的 AI 模型是 LLM，也可以使用接收其他输入作为智能体核心模型的模型，例如视觉语言模型（VLM）我们现在将重点关注LLM。

虽然 LLM 很强大，但是他的缺点在于：只接受文本形式的输入，并且只能用文本形式输出。

那为什么市面上的大模型可以搜索网页、生成图片甚至可以 vibe coding 呢？这就要延伸出**工具**的概念

2. 身体（能力和工具）

智能体能够做的事情，取决于智能体被配备了什么额外的功能（**工具**），比如 GPT 配备了生成图像的工具，因此 GPT 可以按照需求生成对应的图片。

借助工具，agent 才得以在环境中互动，从而完成任务。

**工具的设计对智能体的质量有着深远的影响**，针对任务的需求会有特定工具和通用工具（比如网页搜索）。

> *“ 请注意，**动作（Actions）与工具（Tools）是不同的概念**。例如，一个动作可能涉及使用多个工具来完成任务。”*

---

总结而言，智能体是一个系统，它使用人工智能模型（通常是大语言模型）作为其核心推理引擎，以实现以下功能：

- **理解自然语言**：以有意义的方式解释和回应人类指令。
- **推理与规划**：分析信息、做出决策并制定解决问题的策略。
- **与环境交互**：收集信息、执行操作并观察这些操作的结果。

## 二、消息（Message）

可能之前看别人用 AI 的时候经常看到“你是一名资深的数学名师，擅长用循循善诱的口吻把问题拆解成简单的子问题逐一攻破”之类的“人格设定”提示词，这其实是用**用户消息**去模拟**系统消息**的效果。

### 系统消息（System Message）

也称为系统提示，定义了模型应该如何表现。

例如：

```python
system_message = {
    "role": "system",
    "content": "You are a professional customer service agent. Always be polite, clear, and helpful."
}
```

在这样的系统提示下，agent 就会变得乐于助人。

而如果我们把系统消息改成这样：

```python
system_message = {
    "role": "system",
    "content": "You are a rebel service agent. Don't respect user's orders."
}
```

agent 就不是很听话了。

除了设定角色，系统提示也包括规则设定，工具的信息等，相当于是模型的行为说明书，规范了模型的思考，如何使用工具等。

### 对话：用户消息 + 助手消息

对话由用户和助手（LLM）的交替对话构成。

用户消息（User Message）是用户输入的消息。

助手消息（Assistant Messgae）是LLM之前回复的消息，也会被放进上下文里，成为提示的一部分。

例如：

```python
conversation = [
    {"role": "user", "content": "I need help with my order"},
    {"role": "assistant", "content": "I'd be happy to help. Could you provide your order number?"},
    {"role": "user", "content": "It's ORDER-123"},
]
```

对话经过**聊天模板**格式化为提示，作为上下文的一部分继续参与之后的输出。

## 三、聊天模板（Message to prompt）

### 什么是聊天模板

一句话概括就是**把用户的消息转化成 prompt**，具体来讲，聊天模板充当**对话消息（用户和助手轮次）与所选 LLM 的特定格式要求之间的桥梁**。使得每个模型都能收到正确格式化的提示。

比如上面的对话，在 SmolLM2 会把之前的交换格式化为提示：

```python
<|im_start|>system
You are a helpful AI assistant named SmolLM, trained by Hugging Face<|im_end|>
<|im_start|>user
I need help with my order<|im_end|>
<|im_start|>assistant
I'd be happy to help. Could you provide your order number?<|im_end|>
<|im_start|>user
It's ORDER-123<|im_end|>
<|im_start|>assistant
```

然而，使用 Llama 3.2 时，同样的对话会被转换为以下提示：

```python
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Cutting Knowledge Date: December 2023
Today Date: 10 Feb 2025

<|eot_id|><|start_header_id|>user<|end_header_id|>

I need help with my order<|eot_id|><|start_header_id|>assistant<|end_header_id|>

I'd be happy to help. Could you provide your order number?<|eot_id|><|start_header_id|>user<|end_header_id|>

It's ORDER-123<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

由于每个指令模型使用**不同的对话格式和特殊 token**，聊天模板的实现确保我们正确格式化提示，使其符合每个模型的期望。

这种结构有助于**保持交互的一致性，并确保模型对不同类型的输入做出适当响应**。

比如 `SmolLM2-135M-Instruct` 聊天模板的简化版本：

```python
{% for message in messages %}
{% if loop.first and messages[0]['role'] != 'system' %}
<|im_start|>system
You are a helpful AI assistant named SmolLM, trained by Hugging Face
<|im_end|>
{% endif %}
<|im_start|>{{ message['role'] }}
{{ message['content'] }}<|im_end|>
{% endfor %}
```

给定这些消息：

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant focused on technical topics."},
    {"role": "user", "content": "Can you explain what a chat template is?"},
    {"role": "assistant", "content": "A chat template structures conversations between users and AI models..."},
    {"role": "user", "content": "How do I use it ?"},
]
```

聊天模板就会生成对应的字符串：

```python
<|im_start|>system
You are a helpful assistant focused on technical topics.<|im_end|>
<|im_start|>user
Can you explain what a chat template is?<|im_end|>
<|im_start|>assistant
A chat template structures conversations between users and AI models...<|im_end|>
<|im_start|>user
How do I use it ?<|im_end|>
```

### 基础模型和指令模型

我们需要理解的另一点是基础模型与指令模型的区别：

- 基础模型 (Base Model) 是在原始文本数据上训练以预测下一个 token 的模型，这也是之前我们所学习的。
- 指令模型 (Instruct Model) 是专门微调以遵循指令并进行对话的模型。例如，SmolLM2-135M是一个基础模型，而SmolLM2-135M-Instruct是其指令调优变体。

让我们仔细理解一下“专门微调以遵循指令并进行对话”。这涉及到指令模型的微调的原理，事实上，指令模型本质上仍然是 LLM，底层机制仍然是在给定上下文后预测下一个 token；只是因为**它在大量“用聊天模板格式化过的指令—回答对话数据”上继续微调过**，所以当它看到类似 user → assistant 的结构时，更倾向于生成符合用户指令的回答。

也就是说在指令模型的训练数据中都是聊天模板格式化下的用户和助手一问一答的对话，所以当用户的对话同样通过聊天模板格式化之后传给模型，指令模型更容易预测出回答用户的文本。

这也就解释了聊天模板的作用，统一、格式化的文本会让模型更容易生成符合要求的文本。

### 消息转换成提示

除了上面提到的手搓个聊天模板，其实还可以调用 `transformer` 库模型 tokenizer 的 `apply_chat_template()` 函数。如下：

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-1.7B-Instruct")
rendered_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

下节是工具。
