---
title: "[自用]Rust速通day5：包、crate和use"
published: 2026-03-08T22:27:04+08:00
updated: 2026-03-08T22:27:06+08:00
description: "梳理 Rust 中包、crate 与模块的关系，并说明如何用 use 简化路径和组织作用域。"
tags: ["Rust"]
category: "Rust"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/158812856"
draft: false
pinned: false
---

## 目录

- [模块](#模块)
  - [包和Crate](#包和crate)
  - [use将路径引入作用域](#use将路径引入作用域)

## 模块

### 包和Crate

首先介绍crate，由于Rust官方文档讲述过于晦涩，我只讲述自己的理解：

crate本身是一个抽象的概念，可以理解成是实现特定功能的集合，有多个`.rs`文件组成。

crate分为两种：二进制crate和库crate，

二进制crate中必须包含一个`main`函数来定义程序被执行的时候需要做的事，可以被编译成可执行程序，一个包内有可以有多个二进制crate。

而库crate则是实现功能并提供api接口，提供了**能给多个项目复用的功能**，一个包内只能有一个。

一个包内至少包含一个crate（不管是库还是二进制）。

**根**是crate构建的入口，在运行指令`cargo build`之后，会从根开始构建起整个**模块树**。

接下来会用一个例子来详细说明：

我现在需要构造一个智能家具系统，文件结构如下：

```
smart_home/                      # 包根目录
├── Cargo.toml                   # 包配置文件
└── src/                         # 源代码目录
    ├── lib.rs                    # 库 crate 的根
    ├── device.rs                 # 库 crate：设备通用接口
    ├── temperature.rs            # 库 crate：温度传感器相关功能
    ├── logger.rs                 # 库 crate：日志功能
    ├── main.rs                   # 二进制 crate "smart_home" 的根
    ├── ac_control.rs             # 二进制 crate "smart_home" 的私有模块：空调控制
    ├── fridge_control.rs         # 二进制 crate "smart_home" 的私有模块：冰箱控制
    └── bin/                      # 存放其他二进制 crate 的根文件
        ├── mobile_app.rs          # 二进制 crate "mobile_app" 的根
        ├── mobile_app/            # mobile_app 的私有模块目录
        │   ├── ui.rs              # mobile_app 的私有模块：界面
        │   └── notify.rs          # mobile_app 的私有模块：通知
        ├── web_dashboard.rs       # 二进制 crate "web_dashboard" 的根
        └── web_dashboard/         # web_dashboard 的私有模块目录
            ├── charts.rs          # web_dashboard 的私有模块：图表
            └── auth.rs            # web_dashboard 的私有模块：认证
```

里面有三个二进制crate：`smart_home`、`mobile_app`、`web_dashboard`，分别负责智能家居的总调控，手机app功能实现，网页功能实现，并且构建了库crate，包含多个模块文件。每个crate都有自己的根。（通常`main.rs`是主程序的根，`lib.rs`是库crate的根，其他二进制crate的根统一储存在文件夹`src/bin/`内，并且每一个`src/bin`下的文件都会被编译成一个独立的二进制crate）

`smart_home`以根`main.rs`开始，再通过文件内的`mod`声明查找对应的文件并纳入模块树中，类似于：

```rust
// src/main.rs

mod ac_control  // 告诉编译器存在一个 ac_control 模块，它将在 ac_control.rs 或 ac_control/mod.rs 中定义
mod fridge_control
mod device //引入 库crate 的 device 模块
```

**这些模块共同构成了一个实现家具控制的功能集合，也就是二进制crate。**

在实际的实现过程中，如果一个模块（比如目录中的`device`文件）同时被另一个二进制 crate 通过 `mod` 引入，那么它们会在那个二进制 crate 中**被再次编译**，形成两份独立的代码副本。这可不是我们想要看到的。

因此我们在二进制crate之外还有库crate，能让我们把共享代码放在库crate中，然后让二进制 crate 通过依赖来使用，而不是直接复制模块文件，从而实现**功能的复用**。

### use将路径引入作用域

`use`的作用可以理解为是**快捷方式**，通过创建一个快捷方式把特定的模块导入到“桌面”，也就是作用域中。这样我们就不用写繁琐的前缀了，可以直接使用。例如以下代码:

```rust
mod front_of_house {
    pub mod hosting {
        pub fn add_to_waitlist() {}
    }
}
use crate::front_of_house::hosting;
pub fn eat_at_restaurant() {
    hosting::add_to_waitlist();
}
```

如果没有`use`的话，我们就需要写`crate::front_of_house::hosting::add_to_waitlist()`。

你可以理解成他其实是在crate的作用域中创建了一个虚拟的`mod hosting`。

但是注意`use`只能创建`use`所在的特定作用域的捷径，也就是说，如果把`eat_at_restaurant()`移动到子模块`customer`中，就到了另一个作用域，因此无法访问`hosting::add_to_waitlist()`。

解决方法是在子模块中重新使用use构造捷径。就像这样：

```rust
mod front_of_house {
    pub mod hosting {
        pub fn add_to_waitlist() {}
    }
}
use crate::front_of_house::hosting;
mod customer {
    pub fn eat_at_restaurant() {
        use crate::front_of_house::hosting;
        hosting::add_to_waitlist();
    }
}
```

另一个解决方法是使用`pub use`重新导出，这样子导出的模块会暴露在所有作用域下：

```rust
mod front_of_house {
    pub mod hosting {
        pub fn add_to_waitlist() {}
    }
}
pub use crate::front_of_house::hosting;
mod customer {
    pub fn eat_at_restaurant() {
        hosting::add_to_waitlist();
    }
}
```

当你代码的内部结构与调用你代码的程序员所想象的结构不同时，重导出会很有用。例如，在这个餐馆的比喻中，经营餐馆的人会想到“前台”和“后台”。但顾客在光顾一家餐馆时，可能不会以这些术语来考虑餐馆的各个部分。使用 pub use，我们可以使用一种结构编写代码，却将 不同的结构形式暴露出来。这样做使我们的库井井有条，也使开发这个库的程序员和调用这个库的程序员都更加方便。

你可能会有这样的疑惑：如果我要用函数`add_to_waitlist()`的话，为什么我不用`use crate::front_of_house::hosting::add_to_waitlist()`直达，然后直接使用函数呢？

原因是因为这不符合习惯，上面展示的写法可以**清晰地区分函数是不是在本地定义的**，同时也可以让路径的重复度减小。另一方面，使用`use`引入结构体、枚举以及其他项的时候，习惯是指定他们的完整路径，比如以下把`HashMap`结构体引入二进制crate作用域的做法：

```rust
use std::collections::HashMap;
fn main() {
    let mut map = HashMap::new();
    map.insert(1, 2);
}
```
