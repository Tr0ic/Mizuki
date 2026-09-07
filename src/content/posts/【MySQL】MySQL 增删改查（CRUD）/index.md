---
title: "【MySQL】MySQL 增删改查（CRUD）"
published: 2026-07-13T22:23:42+08:00
updated: 2026-07-13T22:23:44+08:00
description: "整理 MySQL 中 INSERT、SELECT、UPDATE 和 DELETE 的基本语法，涵盖条件、排序、去重与分页查询。"
tags: ["MySQL", "数据库"]
category: "MySQL"
author: "Mem0rin"
sourceLink: "https://blog.csdn.net/2501_93882415/article/details/162850480"
draft: false
pinned: false
---

## 目录

- [1. 新增：INSERT](#1-新增insert)
- [2. 查询：SELECT](#2-查询select)
  - [2.1 基本查询](#21-基本查询)
  - [2.2 去重与排序](#22-去重与排序)
  - [2.3 条件查询](#23-条件查询)
  - [2.4 分页查询](#24-分页查询)
- [3. 修改：UPDATE](#3-修改update)
- [4. 删除：DELETE](#4-删除delete)
- [5. 总结](#5-总结)

> 画师：竹取工坊![画师：竹取工坊](../_assets/csdn-c5298a62a7dd5233.jpeg)  
>  大佬们好！我是Mem0rin！现在正在准备自学转码。  
>  如果我的文章对你有帮助的话，欢迎关注我的主页[Mem0rin](https://blog.csdn.net/2501_93882415?spm=1010.2135.3001.10640)，一起进步！

---

---

本文使用 ChatGPT 进行二次整理。

数据库基本层级：

> 服务器 → 数据库 → 数据表 → 数据行（记录）→ 列（字段）

CRUD 分为新增、查询、修改和删除四类操作。

---

## 1. 新增：INSERT

```sql
-- 插入一行数据
INSERT INTO student (id, name)
VALUES (1, '张三');

-- 按字段顺序插入全部数据
INSERT INTO student
VALUES (2, '李四', 80, 85, 90);

-- 插入多行数据
INSERT INTO student (id, name)
VALUES
    (3, '赵六'),
    (4, '王五');
```

字符串使用英文单引号，字段和值要一一对应。批量插入通常比逐条插入效率更高。（网络通信、SQL执行、事务等）

---

## 2. 查询：SELECT

### 2.1 基本查询

```sql
-- 查询全部字段，数据量很多 => 磁盘和网络资源负担
SELECT *
FROM exam; 

-- 查询指定字段，减少不必要的网络开销
SELECT id, name, chinese
FROM exam;

-- 使用表达式和别名，不修改表内的数据
SELECT id, name, chinese + math + english AS total
FROM exam;
```

### 2.2 去重与排序

```sql
-- 去除重复值
SELECT DISTINCT chinese
FROM exam;

-- 按总分降序排列
SELECT id, name, chinese + math + english AS total
FROM exam
ORDER BY total DESC;

-- 按多个字段排序
SELECT id, name, chinese, math
FROM exam
ORDER BY math DESC, chinese ASC;
```

`ASC` 为升序，`DESC` 为降序，默认使用升序。

### 2.3 条件查询

#### 2.3.1 比较运算符

| 运算符 | 含义 | 示例说明 |
| --- | --- | --- |
| = | 等于 | 判断两个值是否相等 |
| > | 大于 | 左侧值大于右侧值 |
| >= | 大于等于 | 左侧值大于或等于右侧值 |
| < | 小于 | 左侧值小于右侧值 |
| <= | 小于等于 | 左侧值小于或等于右侧值 |
| != 或 <> | 不等于 | 判断两个值是否不相等 |
| <=> | NULL 安全等于 | 两边均为 NULL 时结果为真 |

```sql
-- 查询英语成绩等于 80 的记录
SELECT *
FROM exam
WHERE english = 80;

-- 使用 NULL 安全等于运算符查询英语成绩为 NULL 的记录
SELECT *
FROM exam
WHERE english <=> NULL;
```

#### 2.3.2 范围、集合、空值和模糊匹配运算符表

| 运算符 | 含义 | 示例说明 |
| --- | --- | --- |
| BETWEEN … AND … | 判断是否位于闭区间内 | 包含左右边界 |
| NOT BETWEEN … AND … | 判断是否不在指定区间内 | BETWEEN 的否定形式 |
| IN (…) | 判断值是否属于指定集合 | 相当于多个等值条件的组合 |
| NOT IN (…) | 判断值是否不属于指定集合 | IN 的否定形式 |
| IS NULL | 判断是否为空值 | 不能使用等号代替 |
| IS NOT NULL | 判断是否为非空值 | 排除 NULL |
| LIKE | 模糊匹配 | 百分号匹配任意长度字符，下划线匹配一个字符 |
| NOT LIKE | 模糊匹配的否定形式 | 查询不满足指定模式的内容 |

```sql
-- 查询语文成绩在 60 到 80 之间的记录，包含 60 和 80
SELECT *
FROM exam
WHERE chinese BETWEEN 60 AND 80;

-- 查询学号属于指定集合的记录
SELECT *
FROM exam
WHERE id IN (1, 2, 3);

-- 判断数值 1 是否位于集合中，结果为真
SELECT 1 IN (1, 2, 3);

-- 查询姓名第二个字符为“明”的记录
SELECT *
FROM exam
WHERE name LIKE '_明%';
```

LIKE 中的通配符：

| 通配符 | 含义 |
| --- | --- |
| % | 匹配零个或多个任意字符 |
| _ | 匹配一个任意字符 |

#### 2.3.3 逻辑运算符表

| 运算符 | 含义 | 说明 |
| --- | --- | --- |
| AND | 逻辑与 | 所有条件都成立时结果为真 |
| OR | 逻辑或 | 至少一个条件成立时结果为真 |
| NOT | 逻辑非 | 对条件结果取反 |

```sql
select * from exam where chinese > 80 and english > 80;
select * from exam where chinese > 80 or math > 70 and english > 80;
```

逻辑运算符优先级为 `NOT > AND > OR`。

### 2.4 分页查询

```sql
-- 查询前 n 条记录
SELECT *
FROM exam
LIMIT n;

-- 跳过 s 条，再查询 n 条
SELECT *
FROM exam
LIMIT n OFFSET s;

-- 查询第 3 页，每页 10 条
SELECT *
FROM exam
ORDER BY id
LIMIT 10 OFFSET 20;
```

---

## 3. 修改：UPDATE

```sql
-- 修改指定学生的数学成绩
UPDATE exam
SET math = 100
WHERE name = '张三';

-- 将语文成绩低于 50 分的记录乘以 2
UPDATE exam
SET chinese = chinese * 2
WHERE chinese < 50;

-- 修改总分最低的三条记录
UPDATE exam
SET math = math + 30
WHERE chinese IS NOT NULL
  AND math IS NOT NULL
  AND english IS NOT NULL
ORDER BY chinese + math + english ASC
LIMIT 3;
```

没有 `WHERE` 时会修改整张表。

---

## 4. 删除：DELETE

```sql
-- 删除指定学生的记录
DELETE FROM exam
WHERE name = '张三';

-- 删除英语成绩最低的三条记录
DELETE FROM exam
WHERE english IS NOT NULL
ORDER BY english ASC
LIMIT 3;
```

没有 `WHERE` 时会删除表中全部记录。实际项目中也常使用逻辑删除：

```sql
-- 将记录标记为已删除
UPDATE exam
SET delete_state = 1
WHERE id = 1;
```

---

## 5. 总结

```sql
-- 1.新增
insert into table_name (列名, 列名...) values (值, 值);
-- 2.查询
select * from table_name; -- 全部查询
select column_name, column_name... from table_name; -- 指定列查询
select column_name/expr as 别名 -- 使用别名
	where column_name/expr 比较|逻辑运算符 --排序查询
	order by colunm/expr/别名 asc/desc --条件查询
	limit n offset s; -- 分页查询（从 s 开始往后 n 个）
select distinct column_name, column_name... from table_name; --去重查询
select * from table_name where column_name like '%值_'; --模糊查询
-- 3.更新
update table_name set column_name = value where ... order by ... asc/desc limit n;
-- 4.删除
delete from table_name where ... order by ... asc|desc limit n;
```
