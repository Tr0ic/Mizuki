---
title: "[自用][操作系统]线程"
published: 2026-03-10T22:28:50+08:00
updated: 2026-03-10T22:28:53+08:00
description: "记录 Rust 线程的创建、数据传递、作用域线程与线程局部存储，并说明所有权和生命周期对并发代码的约束。"
tags: ["操作系统"]
category: "操作系统"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/158893781"
draft: false
pinned: false
---

创建线程和在线程间传递数据

`std::thread::spawn` 创建一个新线程

`move` 闭包捕获变量的所有权

`JoinHandle::join()` 等待线程完成并获取返回值

```
## 高级线程操作
//! - **线程睡眠**：`thread::sleep` 暂停当前线程。
//! - **线程本地存储**：`thread_local!` 宏定义每个线程独有的静态变量。
//! - **线程命名**：`Builder::name` 为调试目的分配名称。
//! - **线程优先级**：通过 `thread::Builder` 设置（依赖平台）。
//! - **线程池**：像 `rayon` 这样的库管理线程复用。
//! - **线程通信**：使用 `std::sync::mpsc`（多生产者单消费者）或第三方 crate（例如 `crossbeam`）。
//! - **共享状态**：`Arc<Mutex<T>>` 或 `Arc<RwLock<T>>` 安全地在线程间共享可变数据。
//! - **同步原语**：`Barrier` 同步多个线程，`Condvar` 实现条件变量。
//! - **线程暂停与唤醒**：`thread::park` 阻塞线程，`unpark` 唤醒它，适用于自定义调度。
//! - **获取当前线程句柄**：`thread::current()`。
//! - **作用域线程**：`crossbeam::scope` 或标准库的 `thread::scope`（Rust 1.63+）允许线程借用栈上的数据而无需 `move`。
//!
//! Rust 通过所有权系统以及 `Send` 和 `Sync` trait 在编译时防止数据竞争。
//! 实现了 `Send` 的类型可以跨线程边界传递。
//! 实现了 `Sync` 的类型可以同时被多个线程引用。
//! 大多数 Rust 标准类型都是 `Send + Sync`；例外情况包括 `Rc<T>`（非原子引用计数）和裸指针。
```

`thread::Builder`给线程分配名字和设置栈的大小。

```rust
let builder = thread::Builder::new()
         .name("my-worker".into())
         .stack_size(32 * 1024); // 32 KiB
```

```rust
use std::thread;

//假设线程不会创建失败

fn named_thread_example() {

   let builder = thread::Builder::new()

     .name("my-worker".into())//名字

     .stack_size(32 * 1024); // 32 KiB分配栈大小



   let handle = builder.spawn(|| {

     println!("Hello from thread: {:?}", thread::current().name());

     42

   }).unwrap();//spawn返回Result<JoinHandle<T>, io::Error>，unwrap()把JoinHandle传递给父进程



   let result = handle.join().unwrap();
    //handle.join()等待子进程结束，返回Result<T, Box<dyn Any + Send>>，如果创建成功，join()返回OK(42)，如果不成功，返回Err
    //unwrap()会导致当前线程panic

   println!("Thread returned: {}", result);
}
```

作用域线程（scoped threads）：借用函数栈的变量但不会把数据所有权move进去。

```rust
use std::thread;

 fn scoped_thread_example() {
     let a = vec![1, 2, 3];
     let b = vec![4, 5, 6];

     let (sum_a, sum_b) = thread::scope(|s| {
         let h1 = s.spawn(|| a.iter().sum::<i32>());//创建一个进程，必须在scope的作用域内销毁，可以引用局部变量。
         let h2 = s.spawn(|| b.iter().sum::<i32>());
         (h1.join().unwrap(), h2.join().unwrap())//直接提取join()的值，如果没有则报错
     });

     // `a` and `b` are still accessible here.
     println!("sum_a = {}, sum_b = {}", sum_a, sum_b);
}
```

作用域线程是可以引用局部变量的，但是spawn线程引用的变量必须具有``static`属性（也就是全局静态数据）。因为在spawn创建的是独立线程，在局部变量销毁的时候线程可能还没有结束。

```rust
fn f() {
    let x = 10;

    thread::spawn(|| {
        println!("{}", x); // 借用 x
    });

} // x 在这里销毁，但线程可能还没结束
```

如果`x`销毁之后线程还没结束，那么有关x的引用就会变成悬垂指针，Rust编译器不会通过编译。

线程局部存储：同一个“变量名”在不同线程里其实各有一份独立的数据，互不影响。

```rust
use std::cell::RefCell;//RefCell的作用是：即使外面拿到的是不可变引用，也能在运行时进行可变借用
use std::thread;

thread_local! {//定义线性局部变量的宏
    static THREAD_ID: RefCell<usize> = RefCell::new(0);//每一个线程都有自己独立的THREAD_ID,初始值为0，static表示每个线程各自拥有的一份静态局部存储。
}

fn thread_local_example() {
    THREAD_ID.with(|id| {//调用函数访问线程的ID并且把它传给闭包使用，id是THREAD_ID的引用
        *id.borrow_mut() = 1;//borrow_mut() 会从 RefCell 里借出一个可变引用，*解引用把usize改成1
    });//主线程先把自己的THREAD_ID设为1

    let handle = thread::spawn(|| {//创建子进程
        THREAD_ID.with(|id| {
            *id.borrow_mut() = 2;
        });
        THREAD_ID.with(|id| println!("Thread local value: {}", *id.borrow()));//不可变引用的解引用
    });

    handle.join().unwrap();//正常结束拿出来值，panic则err

    THREAD_ID.with(|id| println!("Main thread value: {}", *id.borrow()));
}
```
