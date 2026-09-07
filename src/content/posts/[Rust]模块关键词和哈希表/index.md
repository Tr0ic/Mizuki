---
title: "[Rust]模块关键词和哈希表"
published: 2026-03-09T20:55:04+08:00
updated: 2026-03-09T20:55:43+08:00
description: "画师：竹取工坊大佬们好！我是Mem0rin！现在正在准备自学转码。如果我的文章对你有帮助的话，欢迎关注我的主页，欢迎互三，一起进步！"
tags: ["Rust"]
category: "Rust"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/158851437"
draft: false
pinned: false
---

## 目录

- [模块](#模块)
  - [一、 pub ：公有化](#一-pub-公有化)
  - [二、 as 提供新名称：](#二-as-提供新名称)
  - [三、使用外部包：](#三使用外部包)
- [HashMap](#hashmap)
  - [一、新建哈希map：](#一新建哈希map)
  - [二、访问哈希map的值：](#二访问哈希map的值)
  - [三、所有权：](#三所有权)
  - [四、更新哈希map:](#四更新哈希map)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，欢迎互三，一起进步！

## 模块

### 一、`pub`：公有化

```rust
mod front_of_house {
    pub mod hosting {
        //这里的pub是让这个模块公有化，也就是说可以通过 crate::front_of_house::hosting::访问模块中的元素
        pub fn add_to_waitlist() {}//但是模块内部的元素是否公有化仍然是需要pub关键字指明的，并且我们知道这样是合理的，因为这样我们对模块内部的元素哪些需要公开，哪些需要私有有更精准的把控。
    }
}
pub fn eat_at_restaurant() {
    // 绝对路径
    crate::front_of_house::hosting::add_to_waitlist();
    // 相对路径
    front_of_house::hosting::add_to_waitlist();
}
```

**结构体和枚举的公有化**：

我们也可以用pub来设计公有的结构体和枚举，如果我们在结构体的定义前加入了`pub`关键词，那么结构体就是公有的，但是内部的字段仍然是私有的，也要通过`pub`来控制哪些要公有哪些要私有。（比如QQ你可以选择公开自己的性别生日，但是不会公开身份证号（（。

super：从父模块开始的相对路径

```rust
fn deliver_order() {}

mod back_of_house {
    fn fix_incorrect_order() {
        cook_order();
        super::deliver_order();
    }
    
    fn cook_order() {}
}
```

依然是作用域的概念，`super`关键字把路径的起点返回到了父模块的作用域，比如上面的代码本来在模块`back_of_house`的作用域内，super返回到了crate作用域，从而就可以直接访问`deliver_order()`了。

### 二、 `as`提供新名称：

```rust
use std::fmt::Result;
use std::io::Result as IoResult
```

### 三、使用外部包：

#### 1.在*Cargo.toml*加入对应依赖

```
rand = "0.8.5"
```

#### 2.用`use`引入：

```rust
use rand::Rng

fn main() {
    let secret_number = rand::thread_rng().gen_range(1..=100);
}
```

#### 嵌套路径：

```rust
use std::cmp::Ordering;
use std::io;
//等价于
use std::{cmp::Ordering, io};

use std::io;
use std::io::Write;
//等价于
use std::io::{self, Write};
```

## HashMap

相当于py的字典，不同的是哈希表也是同质的，也就是所有的键都得是一个类型，所有的值也得是一个类型。

### 一、新建哈希map：

```rust
use std::collections::HashMap;
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.insert(String::from("Yellow"), 50);
```

### 二、访问哈希map的值：

#### `get`

```rust
use std::collections::HashMap;
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.insert(String::from("Yellow"), 50);
let team_name = String::from("Blue");
let score = scores.get(&team_name).copied().unwrap_or(0);
```

#### for循环遍历：

```rust
use std::collections::HashMap;

let mut scores = HashMap::new();

scores.insert(String::from("Blue"), 10);
scores.insert(String::from("Yellow"), 50);

for (key, value) in &scores {
    println!("{key}: {value}");
}
```

### 三、所有权：

对于像 `i32` 这样的实现了 `Copy trait` 的类型，其值可以拷贝进哈希 map。对于像 `String` 这样拥有所有权的值，其值将被移动而哈希 map 会成为这些值的所有者。

```rust
use std::collections::HashMap;

let field_name = String::from("Favorite color");
let field_value = String::from("Blue");

let mut map = HashMap::new();
map.insert(field_name, field_value);
// 这里 field_name 和 field_value 不再有效，
// 尝试使用它们看看会出现什么编译错误！
```

因为涉及所有权的转移，因此在调用`insert`之后，`field_name`, `field_value`将不能使用。

如果将值的引用插入哈希map中，这些值本身不会移动到哈希map中，但至少要保证但是这些引用指向的值在哈希 map 有效时也是有效的。

### 四、更新哈希map:

#### 1.覆盖：对同一个键用两次`insert`即可

#### 2.只在键尚未存在时插入键值对：（如果键存在不进行任何操作，如果不存在则连同值一起插入）

方法是调用`entry`API，返回值是一个枚举`Entry`，代表了可能存在也可能不存在的值。

`Entry`的`or_insert`方法在键对应的值存在的时候会返回键的可变引用，不存在则把参数插入。

```rust
use std::collections::HashMap;
let mut scores = HashMap::new();
scores.insert(String::from("Blue"), 10);
scores.entry(String::from("Yellow")).or_insert(50);
scores.entry(String::from("Blue")).or_insert(50);
println!("{scores:?}");
```

`or_insert`返回的可变引用可以用于更新旧值，具体如下：

```rust
use std::collections::HashMap;

let text = "hello world wonderful world";

let mut map = HashMap::new();
for word in text.split_whitespace() {
    let count = map.entry(word).or_insert(0);
    *count += 1;
}

println!("{map:?}");
```
