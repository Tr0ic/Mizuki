---
title: "从零搭建 Code Agent：HTTP、配置与日志"
published: 2026-08-18T13:12:18+08:00
updated: 2026-08-18T13:12:18+08:00
description: "梳理 Code Agent 远程调用中的 HTTP 客户端、超时、错误分类、环境配置和日志边界，并串联完整调用链。"
tags: ["Agent", "Python", "人工智能"]
category: "AI Agent"
author: "Mem0rin"
sourceLink: "https://zhuanlan.zhihu.com/p/2073033536626546645"
draft: false
pinned: false
---

## 目录

- [一、HTTP 请求与响应](#一http-请求与响应)
- [二、HTTPX 客户端](#二httpx-客户端)
- [三、错误分层](#三错误分层)
- [四、超时](#四超时)
- [五、配置与秘密](#五配置与秘密)
- [六、日志](#六日志)
- [七、模块边界](#七模块边界)
- [八、调用链](#八调用链)

Code Agent 需要调用模型接口、搜索工具和其他远程服务。这些调用大多通过 HTTP 完成，API 地址和密钥来自运行环境，诊断信息还要进入日志。本文希望把这三个环节串联起来，从而解释一次远程调用从哪里开始、错误在哪里出现、哪些信息可以输出。

## 一、HTTP 请求与响应

**HTTP** 是客户端和服务器之间的一套通信规则，可以先把它看作一次跨网络的函数调用：客户端提交输入，服务器处理后返回结果。

```text
客户端程序 ──请求──> 服务器
客户端程序 <──响应── 服务器
```

一个 HTTP 请求主要由方法、URL、请求头和可选的请求体组成。例如创建一份用户资料：

```text
POST /profiles?lang=zh HTTP/1.1
Host: api.example.com
Accept: application/json
Content-Type: application/json

{"name": "Ada"}
```

| 部分 | 示例 | 含义 |
| --- | --- | --- |
| 方法 | POST | 对资源执行的操作 |
| 路径 | /profiles | 要访问的资源 |
| 查询参数 | lang=zh | 附加的筛选或配置条件 |
| 请求头 | Accept、Content-Type | 消息的附加信息 |
| 请求体 | {"name": "Ada"} | 提交给服务器的数据 |

`Accept` 表示客户端希望收到什么格式，`Content-Type` 表示当前消息正文采用什么格式。

服务器处理完成后可能返回：

```text
HTTP/1.1 201 Created
Content-Type: application/json

{"id": 42, "name": "Ada"}
```

响应包含状态码、响应头和可选的响应体。状态码来自服务器；连接尚未建立时，也就没有 HTTP 状态码。

JSON 和 HTTP 属于不同层次。HTTP 负责传输，JSON 是正文可能采用的一种数据格式。响应体也可以是普通文本、HTML、图片或者空内容。

## 二、HTTPX 客户端

HTTPX 把请求的各个部分映射成 Python 参数：

```text
response = client.get(
    "https://api.example.com/profiles/42",
    params={"lang": "zh"},
    headers={"Accept": "application/json"},
)
```

提交 JSON 时使用 `json` 参数：

```text
response = client.post(
    "https://api.example.com/profiles",
    json={"name": "Ada"},
)
```

收到响应后，可以读取状态码并解析正文：

```text
print(response.status_code)
data: object = response.json()
```

这里把 `data` 标成 `object`，因为合法 JSON 不一定是字典。数组、数字、字符串、布尔值和 `null` 同样可以单独构成合法 JSON。

调用 `response.json()` 只能证明正文能够按 JSON 解析。数据是不是字典、是否存在 `name`、`name` 是否为字符串，还需要程序继续验证。

```text
import json
import logging

import httpx


logger = logging.getLogger(__name__)


class ProfileResponseError(ValueError):
    """Raised when a profile API response has an invalid format."""


def fetch_profile_name(client: httpx.Client, url: str) -> str:
    logger.debug("requesting profile path=%s", url)
    response = client.get(url)
    logger.debug(
        "received profile status=%s",
        response.status_code,
    )

    response.raise_for_status()

    try:
        data: object = response.json()
    except json.JSONDecodeError as exc:
        raise ProfileResponseError(
            "response must be valid JSON"
        ) from exc

    if not isinstance(data, dict):
        raise ProfileResponseError(
            "response must be a JSON object"
        )

    name = data.get("name")
    if not isinstance(name, str):
        raise ProfileResponseError(
            "response name must be string"
        )

    return name
```

`fetch_profile_name()` 接收已经创建好的 `Client`。API 地址、认证信息和超时由调用方组装，网络模块只处理请求、状态码和响应结构。

## 三、错误分层

一次远程调用会依次经过这些阶段：

```python
读取配置
→ 建立连接
→ 发送请求
→ 读取响应
→ 检查状态码
→ 解析JSON
→ 验证数据结构
→ 执行业务逻辑
```

阶段不同，错误的含义也不同：

| 场景 | 错误类型 | 是否已有 HTTP 响应 |
| --- | --- | --- |
| 连接失败、读取超时 | httpx.RequestError | 通常没有完整响应 |
| 返回 401、500 | httpx.HTTPStatusError | 有 |
| 返回 200，正文是 HTML | ProfileResponseError | 有 |
| 返回 200 和 {"name": 42} | ProfileResponseError | 有 |
| 姓名是空白字符串 | 业务层 ValueError | 有 |

收到 `4xx` 或 `5xx` 说明服务器已经返回响应。`4xx` 通常表示认证、参数或请求方式等客户端输入存在问题；`5xx` 表示服务器处理失败。要把非成功状态转换成异常，需要主动调用：

```text
response.raise_for_status()
```

状态码通过后还不能直接信任正文。`200` 只说明 HTTP 层成功，非法 JSON、字段缺失和错误字段类型仍需在响应边界处理。

CLI 最后把异常映射成稳定的进程行为：

```text
参数或配置错误 → stderr + SystemExit(2)
网络、状态或服务响应错误 → stderr + return 1
成功 → stdout + return 0
```

## 四、超时

服务器没有及时响应时，客户端不能无限等待。HTTPX 区分连接、读取、写入和连接池四类超时，当前先关注连接和读取：

```text
timeout = httpx.Timeout(
    5.0,
    connect=2.0,
    read=5.0,
)
```

`connect=2.0` 限制建立连接的等待时间。`read=5.0` 限制等待下一块响应数据的时间。第一个 `5.0` 是其他未单独指定项的默认值。

超时在创建客户端时统一配置：

```text
with httpx.Client(
    base_url=settings.api_url,
    timeout=timeout,
) as client:
    name = fetch_profile_name(client, "/profile/42")
```

`with` 结束时会关闭客户端及其连接资源。`Client` 还能复用连接，并让多个请求共享基础地址、请求头和超时设置。

## 五、配置与秘密

API 地址和密钥属于运行配置。密钥不适合写进代码仓库，也不适合作为普通命令行参数传入，因为命令历史、进程列表和错误报告都可能留下痕迹。

配置模块可以从环境变量读取并完成验证：

```text
import os
from collections.abc import Mapping
from dataclasses import dataclass, field


DEFAULT_API_URL = "https://api.example.test"


class ConfigurationError(ValueError):
    """Raised when application configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    api_url: str
    api_key: str = field(repr=False)


def load_settings(
    env: Mapping[str, str] | None = None,
) -> Settings:
    source = os.environ if env is None else env

    api_key = source.get("PROFILE_API_KEY")
    if api_key is None or not api_key.strip():
        raise ConfigurationError("PROFILE_API_KEY is required")

    api_url = source.get("PROFILE_API_URL", DEFAULT_API_URL)
    if not api_url.strip():
        raise ConfigurationError(
            "PROFILE_API_URL must not be empty"
        )

    return Settings(api_url=api_url, api_key=api_key)
```

`source.get()` 找不到密钥时返回 `None`，空字符串则仍然是 `str`。因此先用 `is None` 判断缺失，再用 `not api_key.strip()` 判断空字符串和纯空白字符串。

`field(repr=False)` 可以阻止 `repr(settings)` 直接展示密钥：

```text
Settings(api_url='https://api.example.test')
```

这只保护对象的默认展示。密钥仍然存在于内存中，显式访问 `settings.api_key`、打印认证头或记录完整环境变量都会泄露它。`.env` 文件同样要加入 `.gitignore`。

## 六、日志

CLI 的输出经常还会交给其他程序继续解析，因此需要分清两个通道：

```text
stdout：程序承诺交付的数据
stderr：诊断信息和日志
```

如果 JSON 输出中混入一行日志，`json.loads()` 就会失败。Python 的 `logging.basicConfig()` 默认创建写向 stderr 的处理器，适合由 CLI 入口统一配置：

```text
import logging


logger = logging.getLogger(__name__)


if arg.verbose:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(name)s: %(message)s",
    )

logger.debug(
    "selected profile source=%s",
    "remote" if arg.profile_id is not None else "local",
)
```

库模块只获取自己的 logger：

```text
logger = logging.getLogger(__name__)
```

全局日志级别和格式由 `cli.py` 决定，`http_client.py` 不调用 `basicConfig()`。这样同一个网络模块被 CLI、测试或其他应用导入时，可以服从调用方的日志策略。

日志也不能记录完整请求头：

```text
# 会暴露Authorization中的API key
logger.debug("request headers=%s", client.headers)
```

更合适的内容是请求路径、响应状态和耗时等诊断字段。使用 `%s` 参数还能把字符串格式化交给日志系统：

```text
logger.debug("requesting profile path=%s", url)
```

## 七、模块边界

当前程序拆成了四个主要部分：

| 模块 | 职责 |
| --- | --- |
| config.py | 读取并验证环境变量，生成 Settings |
| http_client.py | 发送请求、检查状态、解析并验证响应 |
| core.py | 规范化姓名并构造业务结果 |
| cli.py | 解析参数、组装依赖、配置日志、输出结果和退出码 |

服务器返回 `" Ada Lovelace "` 时，网络层只确认它是字符串，业务层再规范化为 `"Ada Lovelace"`。异常同样沿着边界向上传递，直到 CLI 把它转换成适合命令行的输出。

这种划分还留下了两个宽松入口：`load_settings(env)` 可以接收指定映射，`main(..., transport=...)` 可以接收指定 HTTP 传输层。生产环境使用真实环境变量和网络，验证代码可以传入受控对象。

## 八、调用链

远程模式的完整执行顺序如下：

```text
PowerShell
→ python -m profile_cli --profile-id 42
→ __main__.py
→ cli.main()
→ argparse解析参数
→ config.load_settings()
→ 创建带认证头和超时的httpx.Client
→ http_client.fetch_profile_name()
→ core.build_profile()
→ stdout/stderr
→ 操作系统退出码
```

本地模式会跳过配置和 HTTP：

```text
--name Ada
→ cli.py
→ core.py
→ stdout
→ exit 0
```

远程调用的主线到这里已经闭合：HTTP 负责传输，配置模块提供运行参数，网络边界验证外部数据，业务层处理姓名，CLI 维护输出协议，日志留下诊断信息且不暴露秘密。

相关资料：

- [HTTPX QuickStart](https://www.python-httpx.org/quickstart/)
- [HTTPX Timeouts](https://www.python-httpx.org/advanced/timeouts/)
- [HTTPX Exceptions](https://www.python-httpx.org/exceptions/)
- [Python Logging HOWTO](https://docs.python.org/3.12/howto/logging.html)[QuickStart - HTTPX](https://www.python-httpx.org/quickstart/)[Python Logging HOWTO](https://docs.python.org/3.12/howto/logging.html)[Exceptions - HTTPX](https://www.python-httpx.org/exceptions/)[Python Logging HOWTO](https://docs.python.org/3.12/howto/logging.html)[QuickStart - HTTPX](https://www.python-httpx.org/quickstart/)[Python Logging HOWTO](https://docs.python.org/3.12/howto/logging.html)
