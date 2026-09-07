---
title: "[自用]Rust速通day3：引用和结构体/操作系统并发初步"
published: 2026-03-05T22:03:57+08:00
updated: 2026-03-05T22:03:59+08:00
description: "因此reference指向了一个无效的String，编译器不允许这样的事情发生。乱序执行：本身是单核的事情，期望的是A指令->B指令，但是现在重排顺序乱了，没有依赖关系的话乱了就乱了。强内存模型（×86）：指令机架构，规定了很强的内存序，不需要额外添加一些指令去完成内存集的保证。一个引用的生命周期是从创建到最后一次使用为止，因此在不可变引用之后创建可变引用是可行的。是不能使用的，因为移动了数据，但如果是上面的赋值，只复用。单核的简单做法：禁止切换和调度，某种意义上的上锁。解构：（必须指明结构体的类型）"
tags: ["操作系统", "Rust"]
category: "操作系统"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/158704764"
draft: false
pinned: false
---

## 目录

- [引用](#引用)
  - [悬垂指针](#悬垂指针)
- [结构体](#结构体)
  - [C结构体](#c结构体)
  - [元组结构体：（没有命名字段）](#元组结构体没有命名字段)
  - [类单元结构体](#类单元结构体)

## 引用

1.任意给定的时间只能有一个可变引用或者多个不可变引用

2.引用必须总是有效的

不能在拥有不可变引用的时候创建可变引用  
一个引用的生命周期是从创建到最后一次使用为止，因此在不可变引用之后创建可变引用是可行的

```rust
let mut s = String::from("hello");
let r1 = &s; // 没问题
let r2 = &s; // 没问题
println!("{r1} and {r2}");
// 此位置之后 r1 和 r2 不再使用
let r3 = &mut s; // 没问题
println!("{r3}");
```

### 悬垂指针

Rust不会有悬垂指针

```rust
fn main() {
	let reference_to_nothing = dangle();//返回一个字符串的引用
}
fn dangle() -> &String {//返回值是一个字符串的引用
	let s = String::from("hello");//创建字符，生命周期是自定义函数的作用域
	&s//返回字符串的引用
}//此时s销毁！
//危险！
```

因为所有权还在s手上，但是s已经销毁了！因此reference指向了一个无效的String，编译器不允许这样的事情发生。

解决办法是直接返回整个字符串即可

```rust
fn main() {
    let str = dangle();
}
fn dangle -> String {
    let s = String::from("hello");
    s
}
```

这样所有权就转移到了str手中

## 结构体

可变与否是整个结构体的

### C结构体

定义：

```rust
struct User {
	 active: bool,
	 username: String,
	 email: String,
	 sign_in_count: u64,
}
```

创建实例：

```rust
fn main(){
	let user1 = User {
		 active: true,
		 username: String::from("someusername123"),
		 email: String::from("someone@example.com"),
		 sign_in_count: 1,
 	};
}
```

获取特定值可以用点号，比如`user1.email`

字段初始化简写：

```rust
fn bulid_user(email:String, username:String) {
    User{
        active: true,
        username,
        //因为email字段和email参数有相同的名称，因此只需编写email而不是email:email
        email,
        sign_in_count: 1,
    }


}
```

结构体更新语法：（使用旧实例的大部分值但改变其部分值）

```rust
fn main() {
    // -- snip --
    
    let user2 = User {
        active: user1.active,
        username: user1.username,
        email: String::from("another@example.com"),
        sign_in_count: user1.sign_in_count,
    }
}

//优化为：

fn main() {
    // -- snip --
    
    let user2 = User {
        email: String::from("another@example.com"),
        ..user1
    }
}
```

这相当于赋值的`=`，更新之后的`user1`是不能使用的，因为移动了数据，但如果是上面的赋值，只复用`user1`的`active`和`sign_in_count`的话，由于具有`Copy trait`属性，因此`user1`仍然有效。

### 元组结构体：（没有命名字段）

定义：

```rust
struct Color(i32, i32, i32);
struct Point(i32, i32, i32);
fn main() {
    let black = Color(0, 0, 0);
    let origin = Point(0, 0, 0);
}
```

解构：（必须指明结构体的类型）

```rust
let Point(x, y, z) = origin;//必须指明是Point
```

访问单独的值：`.`

### 类单元结构体

类似于元组的`unit`：`()`，没有任何字段

定义：

```rust
struct UnitLikeStruct;
```

Rust中的基本线程操作

在线程中使用Mutex

Rust中线程间通信

并发共享虚拟异步

单核：

执行流：栈帧和cpu寄存器存储的执行记录

上下文切换：并发因此不是一个执行流一口气走到底。

要在两个执行流中分时间分配CPU，执行流的切换

单核的简单做法：禁止切换和调度，某种意义上的上锁

多核更加复杂《深入理解计算机体系结构》

CPU core-L1 catch-L2 catch-簇-L3 catch -memory

乱序执行和强弱内存模型

乱序执行：本身是单核的事情，期望的是A指令->B指令，但是现在重排顺序乱了，没有依赖关系的话乱了就乱了

在多核情况问题暴露更加明显

多核心一个观察者观察另一个核心的修改顺序的时候容易暴露问题

强弱内存模型：

强内存模型（×86）：指令机架构，规定了很强的内存序，不需要额外添加一些指令去完成内存集的保证

弱内存（Arm、RISC-V）：需要手动添加保证

dmb、dsb、lsb
