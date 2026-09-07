---
title: "[MySQL]约束"
published: 2026-07-19T16:00:19+08:00
updated: 2026-07-19T16:00:21+08:00
description: "整理 MySQL 的非空、唯一、默认值、主键、自增和外键约束，并对比字段级与表级写法。"
tags: ["MySQL", "数据库"]
category: "MySQL"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/163021169"
draft: false
pinned: false
---

## 目录

- [一、约束概述](#一约束概述)
  - [（一）通用语法](#一通用语法)
  - [（二）常用约束](#二常用约束)
- [二、基本字段约束](#二基本字段约束)
  - [（一）通用语法](#一通用语法-1)
  - [（二）示例](#二示例)
- [三、主键约束( UNIQUE + NOT NULL )](#三主键约束-unique-not-null)
  - [（一）通用语法](#一通用语法-2)
  - [（二）自增类型（ AUTO_INCREMENT ）](#二自增类型-auto_increment)
  - [（三）示例](#三示例)
- [四、外键约束](#四外键约束)
  - [（一）通用语法](#一通用语法-3)
  - [（二）示例](#二示例-1)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，一起进步！

---

---

文本使用 ChatGPT 进行二次整理。

约束用于限制表中数据的取值，保证数据的完整性和正确性。把常见校验交给数据库完成，可以减少人工检查和程序判断。

## 一、约束概述

### （一）通用语法

约束可以直接写在字段后，也可以作为表级约束统一定义。

```sql
-- 在字段后定义约束
CREATE TABLE table_name (
    column_name data_type constraint
);

-- 使用表级约束
CREATE TABLE table_name (
    column1 data_type,
    column2 data_type,
    CONSTRAINT constraint_name constraint (column1, column2)
);
```

### （二）常用约束

| 约束 | 作用 |
| --- | --- |
| `NOT NULL` | 字段必须有值，不能存储 `NULL` |
| `UNIQUE` | 字段值不能重复（eg. 身份证号） |
| `DEFAULT` | 未赋值时使用默认值 |
| `PRIMARY KEY` | 唯一标识一条记录，相当于非空（NOT NULL）且唯一（UNIQUE） |
| `FOREIGN KEY` | 保证当前表的值能在关联表中找到 |
| `CHECK` | 保证字段值满足指定条件 |

MySQL 8.0.16 起开始真正执行 `CHECK` 约束；更早版本只解析语法而不进行校验。具体说明可参考 [MySQL 官方文档](https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html)。

## 二、基本字段约束

### （一）通用语法

```sql
-- 非空约束
column_name data_type NOT NULL

-- 唯一约束
column_name data_type UNIQUE

-- 默认值约束
column_name data_type DEFAULT default_value

-- 检查约束
column_name data_type CHECK (condition)
```

`NOT NULL` 适合姓名、编号等必填字段；`UNIQUE` 适合学号、身份证号等不能重复的字段；`DEFAULT` 用于提供缺失值。

### （二）示例

```sql
-- 创建学生表并添加常用约束
CREATE TABLE student (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL DEFAULT '无名氏',
    sn INT NOT NULL UNIQUE,
    age INT CHECK (age >= 0)
);

-- 查看表结构
DESC student;

-- 不指定 id，由数据库自动生成
INSERT INTO student (name, sn, age)
VALUES ('张三', 10001, 20);
```

## 三、主键约束(`UNIQUE` + `NOT NULL`)

### （一）通用语法

```sql
-- 单列主键
CREATE TABLE table_name (
    id BIGINT PRIMARY KEY
);

-- 复合主键
CREATE TABLE table_name (
    column1 data_type,
    column2 data_type,
    PRIMARY KEY (column1, column2)
);
```

一张表只能有一个主键，但主键可以由多个字段组成。主键会增加少量写入校验开销，但能保证每条记录可以被唯一标识，因此这样的性能消耗是可以承担的。

### （二）自增类型（`AUTO_INCREMENT`）

`AUTO_INCREMENT` 通常与整数主键配合使用。插入数据时可以省略主键字段，由数据库负责维持逐渐的增长。删除记录、回滚事务或手动指定主键后，自增值可能不连续。

### （三）示例

```sql
-- 创建
create table student (
	id bigint not primary key auto_increment, -- 设定主键
	name varchar(50) default '无名氏',
	sn int not null unique
);
-- 查看表
desc student
-- 插入 NULL 报错
insert into student values (NULL, '张三', 10001); -- 不具体指定主键列的值，数据库执行自增操作
insert into student values ('李四'， 10002); -- 数据库自己执行自增操作
insert into student values (100, '王五', 10003); -- 手动指定主键值，后续主键从 101 开始

-- 创建复合主键，只有 id 和 name 的组合不能重复
CREATE TABLE account (
    id BIGINT,
    name VARCHAR(20),
    email VARCHAR(50),
    PRIMARY KEY (id, name)
);

-- 两组主键组合不同，可以正常插入
INSERT INTO account (id, name, email)
VALUES
    (1, '张三', 'zs@example.com'),
    (1, '李四', 'ls@example.com');
```

## 四、外键约束

### （一）通用语法

```sql
-- 当前表的字段引用关联表中的字段
FOREIGN KEY (column_name)
REFERENCES referenced_table (referenced_column)
```

外键通常引用另一张表的主键或 `UNIQUE` 字段。插入子表数据时，被引用的值必须已存在；存在关联数据时，也不能直接删除对应的父表记录。

### （二）示例

```sql
-- 创建班级表
CREATE TABLE class (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL
);

-- 创建学生表，并让 class_id 引用班级编号
CREATE TABLE student_detail (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    class_id BIGINT,
    FOREIGN KEY (class_id) REFERENCES class (id)
);

-- 先插入班级，再插入对应的学生
INSERT INTO class (name)
VALUES ('101班'), ('102班');

INSERT INTO student_detail (name, class_id)
VALUES ('张三', 1), ('李四', 2);
```

如果插入不存在的 `class_id`，或直接删除仍被学生记录引用的班级，数据库会拒绝该操作。
