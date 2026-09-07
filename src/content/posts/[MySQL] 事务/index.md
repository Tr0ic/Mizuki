---
title: "[MySQL] 事务"
published: 2026-08-13T20:35:58+08:00
updated: 2026-08-13T20:36:00+08:00
description: "先来看一个转账的情景，转账至少有两步：一个账户扣款，另一个账户收款。如果扣款成功后程序突然出错，只留下前一半操作，账就对不上了。在数据库中，会采用一个叫事务的方式处理这种业务，事务会把一组相关操作封装成一个整体。整组操作成功时执行COMMIT，任一步失败时由应用执行ROLLBACK，不让数据停在“只做了一半”的状态。"
tags: ["MySQL", "数据库"]
category: "MySQL"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163733410"
draft: false
pinned: false
---

## 目录

- [一、事务与 ACID](#一事务与-acid)
- [二、提交与回滚](#二提交与回滚)
  - [（一）控制语句](#一控制语句)
  - [（二）成绩修改](#二成绩修改)
- [三、隔离级别](#三隔离级别)
  - [（一）四个级别](#一四个级别)
  - [（二）查看与设置](#二查看与设置)
- [四、并发异常](#四并发异常)
  - [（一）脏读](#一脏读)
  - [（二）不可重复读](#二不可重复读)
  - [（三）幻读](#三幻读)
- [五、脏读实验](#五脏读实验)
- [六、快照读与 Next-Key Lock](#六快照读与-next-key-lock)
  - [（一）普通一致性读](#一普通一致性读)
  - [（二）锁定读](#二锁定读)

先来看一个转账的情景，转账至少有两步：一个账户扣款，另一个账户收款。如果扣款成功后程序突然出错，只留下前一半操作，账就对不上了。

在数据库中，会采用一个叫事务的方式处理这种业务，事务会把一组相关操作封装成一个整体。整组操作成功时执行 `COMMIT`，任一步失败时由应用执行 `ROLLBACK`，不让数据停在“只做了一半”的状态。

## 一、事务与 ACID

这个整体通常用 ACID 四个特性来描述：

| 特性 | 含义 |
| --- | --- |
| 原子性（Atomicity） | 事务中的操作共同提交或共同回滚，不留下只完成一部分的结果 |
| 一致性（Consistency） | 事务前后的数据满足数据库约束和业务规则 |
| 隔离性（Isolation） | 并发事务可以交错运行，但相互可见的结果受到隔离级别约束 |
| 持久性（Durability） | 事务成功提交后，结果能够在故障恢复后保留下来 |

原子性解决“做一半”的问题。回到转账场景，扣款和收款要么一起成功，要么一起撤销。

一致性还需要正确的 SQL、数据库约束和业务逻辑共同维护。事务可以保证两条语句一起提交，却无法把错误的金额计算自动改对。

隔离性也不要求事务排队一个接一个执行。事务仍然可以并发交错，隔离级别负责限制它们能看到彼此的哪些结果。

持久性从成功提交开始计算。已经回滚的修改不会持久保存，实际的故障恢复能力还会受到日志刷盘配置和存储设备影响。

## 二、提交与回滚

### （一）控制语句

InnoDB 事务最常用的控制语句只有几条：

```sql
START TRANSACTION;
COMMIT;
ROLLBACK;
```

`START TRANSACTION` 开启事务，也可以写成 `BEGIN`。`COMMIT` 提交当前事务，`ROLLBACK` 撤销当前事务中尚未提交的修改。

### （二）成绩修改

`score` 表中 `id = 1` 的成绩原本是 90。第一段把它改成 99，再执行回滚：

```sql
BEGIN;

UPDATE score
SET score = 99
WHERE id = 1;

ROLLBACK;

SELECT id, score
FROM score
WHERE id = 1;
```

查询结果仍然是 90，说明尚未提交的修改已经撤销。

第二段执行相同修改，再提交：

```sql
BEGIN;

UPDATE score
SET score = 99
WHERE id = 1;

COMMIT;

SELECT id, score
FROM score
WHERE id = 1;
```

查询得到 99，提交后的修改保留下来。

MySQL 默认开启 `autocommit`。没有显式事务时，每条成功执行的语句会作为单独的事务提交，之后再执行 `ROLLBACK` 已经无法撤销。使用 `START TRANSACTION` 后，当前事务会持续到 `COMMIT` 或 `ROLLBACK`，结束后恢复原来的自动提交状态。

```sql
SELECT @@SESSION.autocommit;
```

这里讨论的是 InnoDB 上的 DML。部分 DDL 会触发隐式提交，不能把所有 SQL 都理解成可以随时回滚。

## 三、隔离级别

### （一）四个级别

多个事务同时读写数据时，隔离级别规定一个事务能看到另一个事务走到了哪一步。

InnoDB 支持四种隔离级别：

| 隔离级别 | 普通读取的基本行为 | 可能出现的异常 |
| --- | --- | --- |
| `READ UNCOMMITTED` | 可以读到其他事务尚未提交的数据 | 脏读、不可重复读、幻读 |
| `READ COMMITTED` | 每次一致性读读取该语句开始前已经提交的数据 | 不可重复读、幻读 |
| `REPEATABLE READ` | 同一事务中的普通一致性读复用第一次读取建立的快照 | InnoDB 中还要结合读类型理解幻读 |
| `SERIALIZABLE` | 对冲突访问施加更强的约束 | 避免前三种异常，等待通常更多 |

InnoDB 默认使用 `REPEATABLE READ`。隔离约束逐级增强后，并发现象会减少，冲突访问也更容易等待；实际性能还取决于数据范围、读写比例和冲突程度。

`SERIALIZABLE` 追求的结果是让冲突操作表现出可串行化的顺序。访问互不冲突数据的事务仍可并发执行，不需要让整个数据库一次只运行一个事务。

### （二）查看与设置

全局值决定后续新连接的默认级别，会话值属于当前连接：

```sql
SELECT @@GLOBAL.transaction_isolation;
SELECT @@SESSION.transaction_isolation;
```

设置当前连接后续事务的隔离级别，可以写：

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

设置后续新连接的全局默认值，需要相应的管理权限：

```sql
SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

`GLOBAL` 不会改变已经建立的连接，`SESSION` 也不会改变正在进行的事务。做双会话实验时，最好在两个连接中分别执行 `SET SESSION ...`，再开始事务。

如果直接给系统变量赋值，包含空格的级别名称要改用连字符：

```sql
SET SESSION transaction_isolation = 'REPEATABLE-READ';
```

`SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` 使用空格。两种语法不要混在一起。

## 四、并发异常

脏读、不可重复读和幻读看起来都像“前后查询不一样”，但变化发生的位置不同。

### （一）脏读

事务 A 修改了数据，还没有提交；事务 B 已经读到了这个结果。如果 A 随后回滚，B 刚才看到的值从未真正提交，这就是 **脏读**。

拿抄作业举例，脏读相当于抄了别人写到一半的答案。对方还可能把它划掉重写，这份答案并不可靠。

### （二）不可重复读

事务 A 第一次读取某一行后，事务 B 修改这行并提交；A 再次读取时发现值变了，这就是 **不可重复读**。

不可重复读抄到的是对方正式提交的答案，内容真实存在，只是两次查看时版本不同。它关注的是同一行的值发生变化。

### （三）幻读

事务 A 按同一个范围条件查询两次，期间事务 B 插入、删除，或者更新了会进入或离开查询范围的行并提交，第二次结果集中的行发生变化，这就是 **幻读**。

继续用作业来想：手头那张答案没有被改，但别人又塞进一份符合条件的作业，或者拿走一份。变化落在结果集里有哪些行。

用一句话来区分的话：脏读读到了未提交数据；不可重复读关注同一行的值；幻读关注同一范围中的行集合。

## 五、脏读实验

下面给出不依赖全局配置的复现写法，两个连接分别设置当前会话的隔离级别。

会话 A 开启事务并插入一名学生，先不提交：

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;

INSERT INTO student (name, class_id)
VALUES ('test', 3);
```

会话 B 使用相同隔离级别查询：

```sql
SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
START TRANSACTION;

SELECT id, name, class_id
FROM student
WHERE name = 'test';
```

此时 B 能看到 A 尚未提交的 `test`。接着回到 A：

```sql
ROLLBACK;
```

B 再执行相同查询，`test` 已经消失。第一次查询读到了一行从未提交、最终又被撤销的数据，脏读就发生在这里。

`READ COMMITTED` 是能够避免脏读的最低隔离级别。

## 六、快照读与 Next-Key Lock

### （一）普通一致性读

`REPEATABLE READ` 下的幻读不能只写一个简单的“存在”或“解决”，还要区分普通一致性读和锁定读。

在 `REPEATABLE READ` 下，普通 `SELECT` 默认采用非锁定一致性读。同一事务中的第一次一致性读建立快照，后续普通一致性读继续读取这个快照。其他事务随后提交的插入、更新和删除不会直接进入这份快照。

因此，同一事务两次执行相同的普通范围 `SELECT` 时，后提交的新行通常不会在第二次查询中突然出现。

### （二）锁定读

`SELECT ... FOR SHARE`、`SELECT ... FOR UPDATE`、`UPDATE` 和 `DELETE` 需要处理较新的数据状态，也会设置锁，不能直接套用普通快照读的结论。

在 `REPEATABLE READ` 下，范围搜索通常会锁住实际扫描到的索引范围。**Next-Key Lock** 由索引记录锁和该记录前的间隙锁组成，可以阻止其他事务向已锁定的范围插入新行。

具体锁住哪里，取决于查询条件、使用的索引和扫描范围。通过唯一索引精确查找唯一记录时，通常只锁索引记录；普通一致性读也不会因为处于 `REPEATABLE READ` 就自动加 Next-Key Lock。
