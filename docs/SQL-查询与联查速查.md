# SQL 速查 — 基础语句 / 查询操作 / 多表联查（通用版）

> 用途：通用的 SQL 速查手册，与具体业务无关，示例使用经典电商表（用户/订单/商品）。
> 版本：v2.0（通用版）｜ 日期：2026-08-25 ｜ 适用：SQLite 语法为主，兼容大部分数据库（MySQL/PostgreSQL 差异处已注明）。

---

## 0. 示例表（先建这三张表）

```sql
-- 用户表
CREATE TABLE users (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  email      TEXT UNIQUE,
  age        INTEGER,
  city       TEXT,
  created_at TIMESTAMP
);

-- 订单表（user_id 关联 users.id）
CREATE TABLE orders (
  id         INTEGER PRIMARY KEY,
  user_id    INTEGER NOT NULL,
  product    TEXT,
  amount     REAL,
  status     TEXT,           -- pending / paid / shipped / cancelled
  created_at TIMESTAMP
);

-- 商品表（订单明细也可关联，这里演示多对一）
CREATE TABLE products (
  id       INTEGER PRIMARY KEY,
  name     TEXT,
  category TEXT,
  price    REAL,
  stock    INTEGER
);
```

示例数据（可自行插入，或用你自己的数据替换表名/字段）：

```sql
INSERT INTO users (name, email, age, city, created_at) VALUES
  ('张三', 'zhangsan@example.com', 28, '北京', '2025-01-10 10:00:00'),
  ('李四', 'lisi@example.com', 35, '上海', '2025-02-01 09:30:00'),
  ('王五', 'wangwu@example.com', 22, '广州', '2025-02-20 14:00:00'),
  ('赵六', 'zhaoliu@example.com', 40, '北京', '2025-03-05 11:00:00');

INSERT INTO orders (user_id, product, amount, status, created_at) VALUES
  (1, '键盘', 299.0, 'paid', '2025-03-01 10:00:00'),
  (1, '鼠标', 129.0, 'shipped', '2025-03-10 12:00:00'),
  (2, '显示器', 1299.0, 'paid', '2025-03-12 15:00:00'),
  (3, '键盘', 299.0, 'cancelled', '2025-03-15 09:00:00'),
  (4, '耳机', 499.0, 'paid', '2025-03-20 18:00:00');
```

---

## 1. 基础语句（DDL / DML）

### 1.1 建表 / 删表 / 改表

```sql
-- 用途：新建表（IF NOT EXISTS 可重复执行不报错）
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);

-- 用途：删除表
-- ⚠ 危险：会连同数据一起删除，且不可恢复
DROP TABLE IF EXISTS users;

-- 用途：给表加一列
ALTER TABLE users ADD COLUMN phone TEXT;
```

### 1.2 插入

```sql
-- 用途：插入一条记录
INSERT INTO users (name, email, age, city, created_at)
VALUES ('张三', 'zs@example.com', 28, '北京', '2025-01-10 10:00:00');

-- 用途：一次插入多条
INSERT INTO users (name, email, age) VALUES
  ('李四', 'ls@example.com', 35),
  ('王五', 'ww@example.com', 22);

-- 用途：不存在则插入、存在则更新（UPSERT）
-- ⚠ 注意：ON CONFLICT(字段) 依赖唯一键/主键；excluded 代表「本次准备插入的新值」
INSERT INTO users (id, name, email) VALUES (1, '张三改', 'zs@example.com')
ON CONFLICT(id) DO UPDATE SET name = excluded.name;
```

### 1.3 更新 / 删除

```sql
-- 用途：按条件更新
UPDATE users SET city = '深圳' WHERE id = 3;

-- 用途：按条件删除
DELETE FROM users WHERE age < 20;

-- ⚠ 危险：不带 WHERE 会更新/删除全表，执行前先 SELECT COUNT(*) 确认影响行数
SELECT COUNT(*) FROM users WHERE age < 20;   -- 先看有几条
-- DELETE FROM users WHERE age < 20;         -- 确认无误后再执行
```

---

## 2. 查询操作（SELECT 进阶）

### 2.1 基础过滤与排序

```sql
-- 用途：按多个条件过滤 + 排序 + 分页
SELECT id, name, age, city FROM users
WHERE age >= 18
  AND city IN ('北京', '上海')
  AND name LIKE '张%'                    -- 模糊匹配：张开头
  AND created_at BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY age DESC                        -- 倒序（DESC），升序用 ASC（默认）
LIMIT 10 OFFSET 0;                       -- 每页 10 条，第 1 页
```

常用条件操作符：

```sql
-- = / != / < / <= / > / >=         比较
-- LIKE '%xx%'                       包含；LIKE 'xx%' 以 xx 开头；_ 匹配单个字符
-- IN (1,2,3)                       在集合内
-- BETWEEN a AND b                   闭区间
-- IS NULL / IS NOT NULL             判空（不能用 = NULL）
-- AND / OR / NOT                    逻辑
```

### 2.2 去重 / 别名 / 计算列

```sql
-- 用途：去重查看有哪些城市
SELECT DISTINCT city FROM users;

-- 用途：别名（AS）+ 计算列
SELECT name, age AS 年龄, age + 10 AS age_10y_later FROM users;
```

### 2.3 聚合与分组

```sql
-- 用途：统计每个城市的人数（GROUP BY 分组 + COUNT 聚合）
SELECT city, COUNT(*) AS cnt
FROM users
GROUP BY city
ORDER BY cnt DESC;

-- 用途：分组后过滤（HAVING，作用于分组结果）
SELECT city, COUNT(*) AS cnt
FROM users
GROUP BY city
HAVING COUNT(*) >= 2;

-- 用途：常用聚合函数一起看
SELECT
  COUNT(*)             AS total_rows,
  COUNT(DISTINCT city) AS city_cnt,
  MIN(age)             AS min_age,
  MAX(age)             AS max_age,
  AVG(age)             AS avg_age,
  SUM(age)             AS sum_age
FROM users;

-- ⚠ 注意：SELECT 的列要么是 GROUP BY 的分组列，要么是聚合函数
--   MySQL 宽松允许，PostgreSQL/SQLite 严格会报错
```

### 2.4 子查询

```sql
-- 用途：标量子查询——查「比平均年龄大」的用户
SELECT name, age FROM users
WHERE age > (SELECT AVG(age) FROM users);

-- 用途：IN 子查询——查「下过单的用户」（子查询返回一列值）
SELECT name FROM users
WHERE id IN (SELECT DISTINCT user_id FROM orders);

-- 用途：EXISTS 存在性判断——查「有已支付订单的用户」
-- ⚠ 注意：EXISTS 只判断存在与否，性能通常优于 IN 大列表
SELECT name FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.user_id = u.id AND o.status = 'paid'
);
```

### 2.5 窗口函数（分组排名 / 分组取前 N）

```sql
-- 用途：按金额排名（RANK 同值并列，跳号）
SELECT id, user_id, amount,
       RANK() OVER (ORDER BY amount DESC) AS rk
FROM orders;

-- 用途：分组取前 N——每个用户金额最高的订单（常用套路）
-- 思路：窗口内按 user_id 分组排序给行号，外层过滤 rn=1
SELECT * FROM (
  SELECT o.*,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rn
  FROM orders o
) WHERE rn = 1;

-- 用途：分组累计（SUM OVER）、取上一条（LAG）
SELECT id, user_id, amount,
       SUM(amount) OVER (PARTITION BY user_id)        AS user_total,
       LAG(amount) OVER (ORDER BY id)                 AS prev_amount
FROM orders;

-- ⚠ 注意：窗口函数的结果不能用 WHERE 直接过滤（WHERE 先于窗口执行），需包一层子查询
```

### 2.6 CASE 条件逻辑

```sql
-- 用途：按状态打标签，用于统计/展示
SELECT id, product, amount,
  CASE
    WHEN status = 'paid'      THEN '已支付'
    WHEN status = 'shipped'   THEN '已发货'
    WHEN status = 'cancelled' THEN '已取消'
    ELSE '处理中'
  END AS status_label
FROM orders;

-- 用途：条件聚合——统计各状态下单量
SELECT
  SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)      AS paid_cnt,
  SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_cnt
FROM orders;
```

---

## 3. 多表联查（JOIN）

### 3.1 INNER JOIN（两边都匹配才返回）

```sql
-- 用途：用户 + 订单，只返回「有订单」的用户行
-- 说明：JOIN 默认就是 INNER JOIN
SELECT u.name, o.id AS order_id, o.product, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id
ORDER BY u.name, o.id;

-- 等价写法
SELECT u.name, o.product
FROM users u
JOIN orders o ON u.id = o.user_id;
```

### 3.2 LEFT JOIN（保留左表全部，右表无匹配则为 NULL）

```sql
-- 用途：所有用户及其订单（没下过单的用户也会出现，订单列为 NULL）
SELECT u.name, o.id AS order_id, o.product
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
ORDER BY u.id;
```

**易错点**：过滤右表条件放 `WHERE` 会把 LEFT JOIN 变成内连接效果：

```sql
-- ❌ 错误：o.status 放 WHERE，会把「没订单/其他状态」的用户行删掉，退化成 INNER JOIN
SELECT u.name, o.product
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.status = 'paid';

-- ✅ 正确：过滤条件放 ON，先连接再保留左表全部行
SELECT u.name, o.product
FROM users u
LEFT JOIN orders o ON u.id = o.user_id AND o.status = 'paid';
```

### 3.3 RIGHT / FULL OUTER JOIN

```sql
-- 用途：RIGHT JOIN（保留右表全部）——把两表交换位置用 LEFT JOIN 即可
-- 示例：右表 orders 全部保留（等价于以 orders 为主表）
SELECT u.name, o.product
FROM orders o
LEFT JOIN users u ON u.id = o.user_id;

-- 用途：FULL OUTER JOIN（两边全保留）——SQLite/MySQL 不支持，用两个 LEFT JOIN 求并集
SELECT u.name, o.product
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
UNION
SELECT u.name, o.product
FROM orders o
LEFT JOIN users u ON u.id = o.user_id;

-- ⚠ 注意：PostgreSQL 原生支持 FULL OUTER JOIN，直接写即可
```

### 3.4 自连接（同一张表关联自己）

```sql
-- 用途：找「比自己年龄小」的用户组合（笛卡尔过滤）
SELECT a.name AS elder, b.name AS younger
FROM users a
JOIN users b ON a.age > b.age
ORDER BY a.age DESC;

-- 用途：找每人的「上一条订单」（同表比时间）
SELECT cur.id AS cur_order, cur.user_id,
       (SELECT MAX(prev.created_at) FROM orders prev
        WHERE prev.user_id = cur.user_id
          AND prev.created_at < cur.created_at) AS prev_time
FROM orders cur;
```

### 3.5 UNION（纵向合并）与 UNION ALL

```sql
-- 用途：把两段查询结果上下合并、去重
SELECT name FROM users
UNION                       -- 去重
SELECT product FROM orders;

-- 用途：不去重合并（更快）
SELECT city FROM users
UNION ALL                   -- 不去重，保留重复行
SELECT city FROM users;

-- ⚠ 注意：UNION 要求两段 SELECT 的列数一致、类型兼容
```

### 3.6 三表联查实战

```sql
-- 场景：订单明细场景 users + orders + products 三表
-- 假设订单表有 product_id（这里简化为 product 名字段，按需改列名）
SELECT u.name          AS 用户,
       o.id            AS 订单号,
       o.product       AS 商品,
       p.category      AS 商品类别,
       o.amount        AS 金额,
       o.status        AS 状态
FROM orders o
LEFT JOIN users u    ON u.id = o.user_id
LEFT JOIN products p ON p.name = o.product
WHERE o.status = 'paid'
ORDER BY o.amount DESC;

-- 用途：按用户聚合订单金额（JOIN + GROUP BY 组合）
SELECT u.name, COUNT(o.id) AS order_cnt, SUM(o.amount) AS total_amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
HAVING SUM(o.amount) >= 100
ORDER BY total_amount DESC;
```

---

## 4. 实用小技巧

```sql
-- 用途：只看表结构（各数据库语法不同）
-- SQLite:   .schema users
-- MySQL:    DESCRIBE users;  或  SHOW CREATE TABLE users;
-- PostgreSQL: \d users

-- 用途：查询计划/性能排查（看是否走索引）
-- SQLite:   EXPLAIN QUERY PLAN SELECT ...;
-- MySQL:    EXPLAIN SELECT ...;

-- 用途：事务包裹（批量写操作）
-- SQLite:   BEGIN; ... COMMIT;   回滚用 ROLLBACK;
-- MySQL/PostgreSQL: BEGIN; ... COMMIT; / ROLLBACK;

-- 用途：限制影响行数（部分数据库支持，SQLite/MySQL 支持 LIMIT，PostgreSQL 用 UPDATE ... WHERE ... LIMIT 不支持，改用子查询）
DELETE FROM orders WHERE status = 'cancelled' LIMIT 100;
```

---

## 5. 易错点清单

1. `LEFT JOIN` 的右表过滤条件放 `WHERE` → 退化成内连接（应放 `ON`）；
2. `GROUP BY` 后 SELECT 列必须是分组列或聚合函数（MySQL 宽松，PostgreSQL/SQLite 严格）；
3. `UPDATE` / `DELETE` 忘带 `WHERE` → 全表生效，先 `SELECT COUNT(*)` 确认；
4. 判空用 `IS NULL`，不是 `= NULL`；
5. SQLite/MySQL 不支持 `FULL OUTER JOIN`、`RIGHT JOIN`（MySQL 8 才支持 RIGHT），用 LEFT + UNION 模拟；
6. SQLite 字符串拼接用 `||`，MySQL 用 `CONCAT()`，PostgreSQL 用 `||` 或 `CONCAT()`；
7. 窗口函数不能直接 `WHERE` 过滤，要包子查询；
8. 日期字段建议统一存 `DATE`/`TIMESTAMP` 类型，别存字符串，否则比较大小会出错；
9. 大表查询尽量在 `WHERE`/`JOIN ON` 的字段上建索引；
10. 一条 SQL 里 `LIMIT` 和 `OFFSET` 过大时性能差，大数据量考虑游标/分页键。
