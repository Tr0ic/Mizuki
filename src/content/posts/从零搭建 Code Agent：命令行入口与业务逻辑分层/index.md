---
title: "从零搭建 Code Agent：命令行入口与业务逻辑分层"
published: 2026-08-17T15:19:51+08:00
updated: 2026-08-17T15:19:51+08:00
description: "Code Agent 最终需要一个稳定入口：人可以从终端提交任务，其他程序也可以读取输出和退出状态。命令行层负责接收参数与呈现结果，业务层只处理数据。两层分开后，同一套业务逻辑才能被 CLI、测试和后续 Agent 循环共同复用。"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2072702249915125777"
draft: false
pinned: false
---

## 目录

- [一、程序结构](#一程序结构)
- [二、命令行入口](#二命令行入口)
- [三、三个输出通道](#三三个输出通道)
- [四、业务逻辑](#四业务逻辑)
- [五、参数解析](#五参数解析)
- [六、错误边界](#六错误边界)
  - [（一）语法错误](#一语法错误)
  - [（二）业务错误](#二业务错误)
- [七、输出格式](#七输出格式)
- [八、两层测试](#八两层测试)
  - [（一）函数测试](#一函数测试)
  - [（二）黑盒测试](#二黑盒测试)
- [九、Code Agent 的分层](#九code-agent-的分层)

Code Agent 最终需要一个稳定入口：人可以从终端提交任务，其他程序也可以读取输出和退出状态。命令行层负责接收参数与呈现结果，业务层只处理数据。两层分开后，同一套业务逻辑才能被 CLI、测试和后续 Agent 循环共同复用。

本文笔者将使用一个 `profile_cli` 小程序串起 Python 包、`python -m`、`argparse`、`stdout`、`stderr`、退出码、JSON 格式化和测试。

## 一、程序结构

先把代码拆成一个普通 Python 包：

```text
profile_cli/
├── __init__.py
├── __main__.py
├── cli.py
└── core.py
```

每个文件只承担一类职责：

| 文件 | 职责 |
| --- | --- |
| __main__.py | 承接 python -m profile_cli |
| cli.py | 解析参数、选择格式、打印结果、转换 CLI 错误 |
| core.py | 规范化姓名并构造业务数据 |
| __init__.py | 定义包的公共接口，也可以暂时保持简单 |

完整调用链如下：

```text
PowerShell
  → argv
  → profile_cli/__main__.py
  → cli.py: main()
  → core.py: build_profile()
  → stdout / stderr + exit code
```

## 二、命令行入口

一个 `.py` 文件就是模块。包含 `__init__.py` 的目录可以作为普通包使用。运行下面的命令时：

```python
python -m profile_cli --name "Ada Lovelace"
```

Python 会按模块搜索规则找到 `profile_cli` 包，再选择包内的 `__main__.py` 作为顶层入口。

```text
"""Allow execution with ``python -m profile_cli``."""

from .cli import main


raise SystemExit(main())
```

`from .cli` 中的点表示当前包。相对导入依赖包上下文，因此推荐从包的父目录运行 `python -m profile_cli`。直接执行 `profile_cli/cli.py` 时，Python 通常无法确定这个点属于哪个父包。

`__main__.py` 只负责把包入口接到 `main()`。参数解析和输出逻辑继续放在 `cli.py`，业务计算继续放在 `core.py`。

## 三、三个输出通道

命令行程序中有三种容易混淆的“输出”：

| 通道 | 接收者 | 示例 |
| --- | --- | --- |
| return | Python 函数调用者 | return 0 |
| stdout / stderr | 终端或父进程 | print(...)、参数错误 |
| 退出码 | 操作系统或父进程 | 0、2、1 |

`main()` 中的 `return 0` 只会把整数交给调用它的 Python 代码。`raise SystemExit(main())` 再把这个整数转换成进程退出状态。

标准输出和标准错误也是两条独立通道：

- `stdout` 保存正常结果，方便管道或其他程序继续处理；
- `stderr` 保存错误说明，不污染正常数据；
- 退出码只表达成功或失败，不承担详细说明。

例如 JSON 输出必须保持在 `stdout` 中。调用方可以根据退出码先判断命令是否成功，再决定是否解析这段 JSON。

## 四、业务逻辑

`core.py` 只接收 Python 对象并返回 Python 对象，不读取命令行，也不打印内容。

```text
"""Pure profile-building logic."""

from typing import TypedDict


class Profile(TypedDict):
    name: str
    message: str


def normalize_name(raw_name: str) -> str:
    name = " ".join(raw_name.split())
    if not name:
        raise ValueError("name must not be empty!")
    return name


def build_profile(raw_name: str) -> Profile:
    name = normalize_name(raw_name)
    return {
        "name": name,
        "message": f"Welcome, {name}!",
    }
```

无参数的 `split()` 会按连续空白分组，同时忽略字符串两端的空白：

```text
"  Ada   Lovelace  ".split()
# ['Ada', 'Lovelace']
```

再用一个空格连接，姓名就会规范化为 `Ada Lovelace`。

空白字符串在语法上仍是字符串，因此 `argparse` 的 `required=True` 无法识别它。`core.py` 看到规范化结果为空后抛出 `ValueError`，把业务数据不合法这件事明确交给上层。

这层不调用 `parser.error()`，因为它不应该依赖命令行。以后从 HTTP 接口或 Agent 循环调用 `build_profile()` 时，仍然可以复用同一套逻辑。

## 五、参数解析

`argparse` 把原始命令行字符串解析成 Python 对象，同时生成帮助信息并处理基础参数错误。

```text
import argparse
import json
from collections.abc import Sequence

from .core import build_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="profile_cli",
        description="Generate a normalized greeting.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Name to include in the greeting.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "compact-json"),
        default="text",
        help="Output format (default: text).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        profile = build_profile(args.name)
    except ValueError as error:
        parser.error(str(error))

    if args.format == "text":
        output = profile["message"]
    elif args.format == "json":
        output = json.dumps(profile, ensure_ascii=False)
    else:
        output = json.dumps(
            profile,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(output)
    return 0
```

这里几个参数分别守住不同边界：

| 配置 | 作用 |
| --- | --- |
| required=True | 没有传入 --name 时拒绝执行 |
| choices=(...) | 只接受三种输出格式 |
| default="text" | 省略 --format 时选择文本 |
| parse_args(argv) | 解析显式传入的参数；argv=None 时读取真实命令行 |
| parser.error(...) | 输出统一错误信息并以状态码 2 退出 |

让 `main()` 接受可选的 `argv` 很有用。真实运行时不传参数，它会读取命令行；函数测试可以传入列表，不必创建新进程。

## 六、错误边界

参数错误可以分成语法层与业务层。

### （一）语法错误

缺少 `--name` 或传入 `--format xml` 时，`parse_args()` 会直接拒绝输入：

```text
python -m profile_cli --name Ada --format xml
```

结果写入 `stderr`，退出码为 `2`。由于解析阶段已经停止，`build_profile()` 不会执行。

### （二）业务错误

下面的命令提供了 `--name`，所以语法检查可以通过：

```text
python -m profile_cli --name "   "
```

`build_profile()` 规范化姓名后发现结果为空，于是抛出 `ValueError`。`cli.py` 捕获这个可预期错误，再调用 `parser.error()`，最终仍得到一致的 usage、`stderr` 和退出码 `2`。

这条链路可以写成：

```text
空白姓名
  → argparse 接受字符串
  → core.py 抛出 ValueError
  → cli.py 调用 parser.error()
  → stderr + SystemExit(2)
```

`parser.error()` 会写入错误信息并抛出 `SystemExit(2)`。因此错误路径通常拿不到 `main()` 的普通返回值，测试时需要检查 `SystemExit`。

`--help` 属于正常路径。帮助文本写入 `stdout`，进程以 `0` 退出。

## 七、输出格式

业务层返回的数据始终相同：

```text
{
    "name": "Ada Lovelace",
    "message": "Welcome, Ada Lovelace!",
}
```

`text`、`json` 和 `compact-json` 只改变呈现方式，所以只需要修改 `cli.py`。`core.py` 不关心结果最终被打印成哪一种格式。

普通 JSON：

```text
json.dumps(profile, ensure_ascii=False)
{"name": "Ada Lovelace", "message": "Welcome, Ada Lovelace!"}
```

紧凑 JSON：

```text
json.dumps(
    profile,
    ensure_ascii=False,
    separators=(",", ":"),
)
{"name":"Ada Lovelace","message":"Welcome, Ada Lovelace!"}
```

`ensure_ascii=False` 让中文直接保留在输出中。`separators=(",", ":")` 去掉逗号和冒号后的空格，只改变序列化文本，不改变内部数据。

验证紧凑格式时要直接比较字符串。`json.loads()` 会把两种文本都解析成相同的 Python 对象，原来的空格信息随解析过程消失，因此无法证明输出是否紧凑。

## 八、两层测试

### （一）函数测试

直接调用 `main(argv)` 可以快速检查返回值和输出。`StringIO` 创建内存文本缓冲区，`redirect_stdout` 临时把 `print()` 的目标切换到这个缓冲区，`getvalue()` 才负责读取其中的文本。

```text
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from profile_cli.cli import main


class ProfileCliTests(unittest.TestCase):
    def test_text_output_returns_zero(self):
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["--name", "  Ada   Lovelace  "])

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue(),
            "Welcome, Ada Lovelace!\n",
        )

    def test_invalid_format_exits_two(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                main(["--name", "Ada", "--format", "xml"])

        self.assertEqual(caught.exception.code, 2)
        self.assertIn("invalid choice", stderr.getvalue())
```

这里的 `redirect_stdout` 负责改变输出去向，`StringIO` 负责暂存文本。两者职责不能倒置。

### （二）黑盒测试

函数测试没有经过真实的 `python -m` 入口。还需要用子进程验证 `__main__.py`、标准流和进程退出码：

```text
import subprocess
import sys


completed = subprocess.run(
    [
        sys.executable,
        "-m",
        "profile_cli",
        "--name",
        "Ada Lovelace",
        "--format",
        "compact-json",
    ],
    check=False,
    capture_output=True,
    text=True,
)

assert completed.returncode == 0
assert completed.stderr == ""
assert completed.stdout == (
    '{"name":"Ada Lovelace",'
    '"message":"Welcome, Ada Lovelace!"}\n'
)
```

黑盒测试负责整个程序边界，函数测试负责快速定位内部逻辑。两层都通过，才能同时说明业务函数正确、命令行契约也正确。

## 九、Code Agent 的分层

从结构上，这个小程序已经形成了一条可以继续扩展的边界：

```text
__main__.py：进程入口
cli.py：参数与输出协议
core.py：可复用业务逻辑
```

以后把 `build_profile()` 换成 `run_agent()`，分层仍然成立。CLI 负责接收任务、选择输出格式和返回退出状态；core 负责 Agent 循环、工具调用结果和最终业务对象。HTTP 服务或测试也可以直接调用 core，无需模拟命令行。

相关资料：

- [Python 3.12：Modules](https://docs.python.org/3.12/tutorial/modules.html)
- [Python 3.12：__main__](htt<code>ps://doc</code>s.python.org/3.12/library/__main__.html)
- [Python 3.12：Argparse Tutorial](https://docs.python.org/3.12/howto/argparse.html)
- [Python 3.12：argparse](htt<code>ps://doc</code>s.python.org/3.12/library/argparse.html)
- [Python 3.12：json.dumps](htt<code>ps://docs.</code>python.org/3.12/library/json.html#json.dumps)
- [Python 3.12：io.StringIO](htt<code>ps://docs.p</code>ython.org/3.12/library/io.html#io.StringIO)
- [Python 3.12：contextlib.redirect_stdout](htt<code>ps://docs.python.org/3.12/</code>library/contextlib.html#contextlib.redirect_stdout)
- [Python 3.12：subprocess.run](htt<code>ps://docs.pyth</code>on.org/3.12/library/subprocess.html#subprocess.run)
