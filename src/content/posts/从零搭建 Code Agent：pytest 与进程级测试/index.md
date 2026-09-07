---
title: "从零搭建 Code Agent：pytest 与进程级测试"
published: 2026-08-23T20:37:29+08:00
updated: 2026-08-23T20:37:29+08:00
description: "超时、 401、 500、非法 JSON、缺少密钥和日志泄露都需要稳定复现，因此自动测试是必要的。"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2074957973772821322"
draft: false
pinned: false
---

## 目录

- [一、测试层次](#一测试层次)
- [二、pytest 基础](#二pytest-基础)
- [三、输出与日志](#三输出与日志)
- [四、参数化与异常](#四参数化与异常)
- [五、HTTP 传输替身](#五http-传输替身)
- [六、进程级测试](#六进程级测试)
- [七、子进程边界](#七子进程边界)
- [八、阶段结果](#八阶段结果)

超时、`401`、`500`、非法 JSON、缺少密钥和日志泄露都需要稳定复现，因此自动测试是必要的。

## 一、测试层次

这个 CLI 使用两层测试：

```text
函数级测试
→ 直接调用main(argv)
→ 快速覆盖成功和失败分支

进程级测试
→ subprocess启动python -m profile_cli
→ 检查真实入口、模块导入、输出流和退出码
```

函数级测试适合覆盖大量边界，因为它运行快，还能注入环境变量和 HTTP 传输层。进程级测试会创建新的 Python 进程，速度较慢，也更容易受到解释器和工作目录影响，所以只保留少量关键闭环。

局部测试通过不能自动证明整体入口正确，这正是进程级冒烟测试仍然存在的原因。

## 二、pytest 基础

pytest 默认发现符合命名规则的文件和函数：

```text
# test_profile.py

def test_profile_output() -> None:
    ...
```

一个测试通常可以按 Arrange、Act、Assert 阅读：

```text
def test_remote_profile_outputs_normalized_greeting(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange：准备受控的HTTP响应
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"name": "  Ada   Lovelace  "},
        )

    # Act：执行CLI公开接口
    exit_code = main(
        ["--profile-id", "42"],
        env={"PROFILE_API_KEY": "test-secret"},
        transport=httpx.MockTransport(handler),
    )

    # Assert：检查退出码和两个输出流
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Welcome, Ada Lovelace!\n"
    assert captured.err == ""
```

测试从公开入口 `main()` 进入，真实经过参数解析、配置、HTTP 客户端、响应校验、业务逻辑和输出。只有网络传输被换成受控实现。

## 三、输出与日志

`capsys` 是 pytest 提供的 fixture。测试函数声明这个参数后，pytest 会注入捕获对象：

```text
captured = capsys.readouterr()

captured.out  # stdout
captured.err  # stderr
```

`readouterr()` 会取得调用前已经捕获的内容，随后继续捕获。这样就能验证成功结果进入 stdout，参数错误和诊断信息进入 stderr。

日志使用另一个 fixture：`caplog`。

```text
def test_remote_log_does_not_leak_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="profile_cli")

    main(
        ["--profile-id", "42", "--verbose"],
        env={"PROFILE_API_KEY": "test-secret"},
        transport=httpx.MockTransport(handler),
    )

    assert "requesting profile path=/profile/42" in caplog.text
    assert "received profile status=200" in caplog.text
    assert "test-secret" not in caplog.text
```

`capsys` 检查程序的输出协议，`caplog` 检查 logging 产生的记录。两者关注的通道不同。

## 四、参数化与异常

相同测试逻辑需要验证多组数据时，可以使用参数化：

```text
@pytest.mark.parametrize("status_code", [401, 500])
def test_remote_profile_reports_http_status_error(
    status_code: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    ...
```

上面的函数会生成两个独立测试用例。`401` 和 `500` 共享执行流程，但各自拥有单独的结果和失败报告。

命令行解析错误需要用 `pytest.raises()` 捕获：

```text
with pytest.raises(SystemExit) as exc_info:
    main([])

assert exc_info.value.code == 2
```

`main([])` 会在 `argparse` 内抛出 `SystemExit(2)`，不会返回整数 `2`。缺少 `--name` 和 `--profile-id`、同时提供两个互斥参数，都在 `parse_args()` 阶段结束。

业务运行错误采用另一条路径：

```text
缺少API key
→ ConfigurationError
→ parser.error()
→ SystemExit(2)

服务器返回500
→ HTTPStatusError
→ CLI捕获
→ stderr
→ return 1
```

## 五、HTTP 传输替身

真实接口会受到网络、服务状态和测试数据影响。HTTPX 的 `MockTransport` 接受一个 handler，用它替换真正的网络传输：

```text
真实环境：HTTPX → 操作系统网络 → 远程服务器
测试环境：HTTPX → MockTransport → handler
```

handler 就像一个很小的假服务器：

```text
def handler(request: httpx.Request) -> httpx.Response:
    assert request.method == "GET"
    assert request.url.path == "/profile/42"
    assert (
        request.headers["Authorization"]
        == "Bearer test-secret"
    )

    return httpx.Response(
        200,
        json={"name": "Ada"},
    )
```

它接收 HTTPX 真实构造的请求，再返回预设响应。`main()`、`load_settings()`、`fetch_profile_name()` 和 `build_profile()` 仍然真实运行。

失败路径也可以立即产生：

```text
def handler(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout(
        "simulated read timeout",
        request=request,
    )
```

这种超时不会真的等待五秒。它验证的是异常能否沿调用链传递并转换成稳定的 CLI 错误。真实超时数值仍由 `httpx.Client` 的配置负责。

## 六、进程级测试

直接调用 `main()` 无法覆盖 `python -m profile_cli` 的启动过程。`subprocess.run()` 可以从操作系统进程边界执行 CLI：

```text
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_success_from_process() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "profile_cli",
            "--name",
            "Ada Lovelace",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == "Welcome, Ada Lovelace!\n"
    assert result.stderr == ""
```

几个参数分别解决不同问题：

| 参数 | 作用 |
| --- | --- |
| sys.executable | 使用当前测试进程的 Python 解释器 |
| cwd | 固定子进程工作目录，使包能够被找到 |
| capture_output=True | 捕获 stdout 和 stderr |
| text=True | 以字符串形式读取输出 |
| timeout=5 | 防止子进程长期卡住 |
| check=False | 保留非零退出码，由测试自行断言 |

不设置 `cwd` 时，子进程继承父进程的工作目录。从 `agent-foundations` 启动时，Python 无法在当前目录找到 `profile_cli`；进入 `cli-rebuild` 后才能正常导入。显式传入 `cwd` 可以消除这种偶然性。

## 七、子进程边界

`subprocess.run()` 的结果需要分层判断：

```text
程序无法启动
→ FileNotFoundError

程序启动后超时
→ subprocess.TimeoutExpired

程序结束且退出码非零
→ check=False：返回CompletedProcess
→ check=True：抛出CalledProcessError

退出码为0但stdout不是约定的JSON
→ 调用方的输出解析或业务数据错误
```

执行命令时优先使用参数列表和 `shell=False`：

```text
subprocess.run(
    [sys.executable, "-m", "profile_cli", "--name", user_input],
    shell=False,
)
```

这和 MySQL 参数化查询的思路很接近：固定程序结构，外部输入占据一个明确的数据位置。包含空格或 `&` 的姓名仍然是一个参数，shell 不会把其中内容重新解释成管道、重定向或下一条命令。

参数列表只隔离 shell 语法，目标程序仍会解析自己的选项。Code Agent 的工具执行器还需要限制允许的程序和参数、验证工作目录、设置超时、控制环境变量并限制输出大小。

## 八、阶段结果

当前测试覆盖了这些路径：

```text
本地姓名成功
远程资料成功
缺少或冲突的输入来源
缺少API key
读取超时
401与500
非法JSON
空白远程姓名
日志不泄露密钥
模块入口与进程退出码
```

完整验证命令：

```text
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
..\.venv\Scripts\python.exe -m mypy profile_cli tests
```

结果为：

```text
18 passed
Success: no issues found in 9 source files
```

这套测试已经覆盖函数、网络传输和操作系统进程三个边界。进入 Agent Loop 后，模型提议、工具执行、观察结果和退出原因也可以沿用同一思路：外部依赖可替换，公开行为可断言，失败路径能够稳定复现。

相关资料：

- [pytest 输出捕获](https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html)
- [pytest 日志捕获](https://docs.pytest.org/en/stable/how-to/logging.html)
- [pytest 参数化](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [HTTPX Transports](https://www.python-httpx.org/advanced/transports/)
- [Python subprocess](https://docs.python.org/3.12/library/subprocess.html)
