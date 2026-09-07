---
title: "[自用]Rust速通day4：结构体，枚举和字符串"
published: 2026-03-07T08:15:50+08:00
updated: 2026-03-07T08:15:53+08:00
description: "的封装，因此一个英文字母的长度是一个字节，但对于其他字符比如中文，一个中文对应的长度就是两个字节，那么进行索引的话，事实上从Rust的角度，有三种方式访问字符串：字节、标量值、字节簇（最接近于字母的概念）方法是定义在结构体上下文的，和函数类似，具有返回值和参数，并且第一个参数总是。可以用字符串切片slice切取部分字符，但是需要注意的是如果对中文字符尝试。就不会反映出有效的信息。IP地址要么是IPV4要么是IPV6，可以枚举出所有可能的情况。如果我们遇到一个更大的结构体需要更加易读的输出的话，可以使用。"
tags: ["Rust"]
category: "Rust"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/158768167"
draft: false
pinned: false
---

## 目录

  - [结构体打印调试信息：](#结构体打印调试信息)
  - [方法语法](#方法语法)
- [枚举](#枚举)
  - [引入](#引入)
  - [枚举值](#枚举值)
- [字符串](#字符串)
  - [创建实例](#创建实例)
  - [更新字符串](#更新字符串)
  - [索引字符串](#索引字符串)
  - [遍历字符串](#遍历字符串)

原文本来源于Rust官方文档及翻译，感谢开源。

### 结构体打印调试信息：

1.在`{}`中加入`:?`指示符告诉`println！`我想要使用`Debug`的输出格式

2.加上外部属性`#[derive(Debug)]`派生`Debug` trait

```rust
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}
fn main() {
    let rect1 = Rectangle {
        width: 30,
        height: 50,
    };
    println!("rect1 is {rect1:?}");
}
```

结果是`rect1 is Rectangle { width: 30, height: 50 }`

如果我们遇到一个更大的结构体需要更加易读的输出的话，可以使用`:#?`指示符

输出如下：

```
$ cargo run
 Compiling rectangles v0.1.0 (file:///projects/rectangles)
 Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.48s
 Running `target/debug/rectangles`
rect1 is Rectangle {
 width: 30,
 height: 50,
}
```

还可以用`dbg!`宏来定义，处于篇幅不多叙述。

### 方法语法

方法是定义在结构体上下文的，和函数类似，具有返回值和参数，并且第一个参数总是`self`。

为了让函数定义在结构体的上下文，我们需要一个`impl`块，并把所有的方法都移动到`impl`大括号中，形式如下：

```rust
#[derive(Debug)]
struct Rectangle {
    width: u32,
    height: u32,
}
impl Rectangle {
    fn area(&self) -> u32 {
       self.width * self.height
    }
}
fn main() {
    let rect1 = Rectangle {
        width: 30,
        height: 50,
    };
    println!(
        "The area of the rectangle is {} square pixels.",
        rect1.area()
    );
}
```

`area`函数中`&self`其实是`self: &Self`的缩写，相当于借用了`Self`的实例，比如`rect1.area()`的`self`指的就是`rect1`，相当于`rect: &Rectangle`，如果需要改变实例内容的话则需要改成`&mut self`

多参数：

```rust
impl Rectangle {
    fn area(&self) -> u32 {
        self.width * self.height
    }
    fn can_hold(&self, other: &Rectangle) -> bool {
        self.width > other.width && self.height > other.height
    }
}
```

## 枚举

### 引入

IP地址要么是IPV4要么是IPV6，可以枚举出所有可能的情况。

因此我们定义一个`IpAddrKind`枚举来表现这个概念，其中的`V4`和`V6`称为枚举的变体

定义如下：

```rust
enum IpAddrKind{
    V4,
    V6,
}
```

于是我们得到了一个自定义数据类型。

### 枚举值

创建实例：

```rust
let four = IpAddrKind::V4;
let six = IpAddrKind::V6;
```

我们还可以定义一个接收任何`IpAddrKind`类型参数的函数：

```rust
fn rount(ip_kind: IpAddrKind) {}
route(IpAddrKind::V4);
route(IpAddrKind::V6);
```

我们现在没有存储实际IP地址数据的方法，只知道它的类型，我们可以用结构体实现这一功能：

```rust
enum IpAddrKind {
    V4,
    V6,
}
struct IpAddr {
    kind: IpAddrKind,
    address: String,
}
let home = IpAddr {
    kind: IpAddrKind::V4,
    address: String::from("127.0.0.1"),
};
```

这样的方法把`kind`和`address`通过结构体绑定起来，这样就与值相关联了

但是有更简洁的方法：

```rust
enum IpAddr{
    V4(String),
    V6(String),
}

let home = IpAddr::V4(String::from("127.0.0.1"));
```

这相当于把美剧变体的名字变成了构建枚举实例的构造函数。

还有另一个优势是每个变体可以处理不同的数据类型：

甚至结构体和另一个结构体也可以放进去

```rust
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
    ChangeColor(i32, i32, i32),
}
```

这就类似于四个结构体:

```rust
struct QuitMessage; // 类单元结构体
struct MoveMessage {
    x: i32,
    y: i32,
}
struct WriteMessage(String); // 元组结构体
struct ChangeColorMessage(i32, i32, i32); // 元组结构体
```

枚举的match示例：

```rust
match message{
    Message::ChangeColor(x, y, z) => self.change_color((x, y, z)),
    Message::Quit => self.quit(),
    Message::Echo(str) => self.echo(str),
    Message::Move(Point{x, y}) => self.move_position(Point{x, y }),
}
```

## 字符串

### 创建实例

```rust
let mut s = String::new();//空字符串

//from函数从字符串字面值创建带有初始值的字符串
let mut s = String::from("initial contents");

let data = "initial contents";

let s = data.to_string();

let s = "initial contents".to_string();
```

### 更新字符串

#### 附加字符串

`push_str`:附加字符串（slice）

```rust
let mut s = String::from("foo");
s.push_str("bar");
```

并且不会转移所有权，s2还是可以正常使用的。

`push`:附加字符

```rust
let mut s = String::from("lo");
s.push('l');
```

s将会包含`lol`

#### 拼接字符串

`+`:

```rust
 let s1 = String::from("Hello, ");
 let s2 = String::from("world!");
 let s3 = s1 + &s2; // 注意 s1 被移动了，不能继续使用
```

加法的操作实际上调用了`add`函数，函数签名类似于：

```rust
fn add(self, s: &str) -> String {
```

此时`s1`发生移动，因此`s1`不再有效。

`format!`:

```rust
let s1 = String::from("tic");
let s2 = String::from("tac");
let s3 = String::from("toe");
let s = format!("{s1}-{s2}-{s3}");
```

### 索引字符串

在Rust中，尝试用索引语法访问`String`的一部分，会出现无效代码：

```rust
let s1 = String::from("hi");
let h = s1[0];
```

这是因为在Rust中字符串是一个`Vec<u8>`的封装，因此一个英文字母的长度是一个字节，但对于其他字符比如中文，一个中文对应的长度就是两个字节，那么进行索引的话，`s1[0]`就不会反映出有效的信息。因此Rust从一开始就不会允许这种代码通过编译。

事实上从Rust的角度，有三种方式访问字符串：字节、标量值、字节簇（最接近于字母的概念）

比如用梵文书写的印度语单词 “नमस्ते”，

字节：

```
[224, 164, 168, 224, 164, 174, 224, 164, 184, 224, 165, 141, 224, 164, 164, 224, 165, 135]
```

这也是计算机最终会存储的数据

标量值：

```
['न', 'म', 'स', '्', 'त', 'े']
```

字节簇：

```
["न", "म", "स्", "ते"]
```

可以用字符串切片slice切取部分字符，但是需要注意的是如果对中文字符尝试`&hello[0..1]`的话同样会报错。

### 遍历字符串

最好的办法是首先明确需要的是字节还是字符

#### 字符chars()

对 “Зд” 调用 chars 方法会将其分开并返回两个 char 类型的值，接着就 可以遍历其结果来访问每一个元素了：

```rust
for c in "Зд".chars() {
    println!("{c}");
}
```

就会把字符一一打印出来

#### 字节bytes()

会返回原始字节：

```rust
for c in "Зд".byte() {
    println!("{c}");
}
```
