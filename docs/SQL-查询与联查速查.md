# SQL 速查 — 基础语句 / 查询操作 / 多表联查

> 用途：项目开发与数据排查时的 SQL 速查，示例全部基于本项目 `long_term_memory.db` 的真实表。
> 版本：v1.0 ｜ 日期：2026-08-25 ｜ 适用：SQLite（其他数据库语法大同小异）。

---

## 0. 项目数据库说明

本项目核心库为 `long_term_memory.db`（SQLite，已被 `.gitignore` 忽略，不入库）。当前表清单：

| 表 | 关键字段 | 用途 |
|---|---|---|
| `lessons` | `id, project_id, agent_name, category, lesson, created_at` | GIS 任务经验（跨会话记忆） |
| `lesson_embeddings` | `lesson_id, embedding, created_at` | lesson 的向量（n-gram 哈希 256 维） |
| `user_preferences` | `key, value, confidence, updated_at` | 用户偏好（如 `settings:v1`） |
| `user_models` | `id, user_key, label, provider, model, base_url, api_key, capabilities, created_at` | 用户自定义模型（Settings 模块） |
| `projects` | `id, name, idea, status, quality_score, review_rounds, token_used, created_at` | 通用项目记录 |
| `content_projects` | 营销内容项目字段 | 旧营销模块留存 |

**连接方式（Windows）**

Python（推荐）：
```python
import sqlite3
con = sqlite3.connect(r"H:\ai-dev-platform\long_term_memory.db")
con.row_factory = sqlite3.Row          # 让查询结果可按列名访问
rows = con.execute("SELECT * FROM lessons LIMIT 5").fetchall()
for r in rows:
    print(r["id"], r["agent_name"], r["lesson"][:40])
```

命令行（若装有 sqlite3）：
```bash
sqlite3 long_term_memory.db
.tables            # 列表
.schema lessons    # 查看建表语句
```

---

## 1. 基础语句（DDL / DML）

### 1.1 建表 / 删表

```sql
CREATE TABLE IF NOT EXISTS lessons (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  agent_name TEXT NOT NULL,
  category TEXT,                -- success / failure / preference / bug
  lesson TEXT,
  created_at TIMESTAMP
);

DROP TABLE IF EXISTS lessons;   -- 删除表（慎用）
ALTER TABLE lessons ADD COLUMN score REAL;  -- 加列
```

### 1.2 插入

```sql
INSERT INTO lessons (id, project_id, agent_name, category, lesson, created_at)
VALUES ('abc123', 'session1', 'gis_assistant:user1', 'success', 'GIS 任务完成：xxx', 1785600000.0);

-- 批量插入（多值）
INSERT INTO lessons (id, agent_name, category, lesson, created_at) VALUES
  ('a1', 'gis_assistant:user1', 'success', 'xxx', 1785600000.0),
  ('a2', 'gis_assistant:user1', 'bug', 'yyy', 1785600100.0);

-- 不存在才插入 / 存在则更新（UPSERT）
INSERT INTO lessons (id, agent_name, category, lesson, created_at)
VALUES ('abc123', 'gis_assistant:user1', 'success', '新内容', 1785600000.0)
ON CONFLICT(id) DO UPDATE SET lesson = excluded.lesson;
```

### 1.3 更新 / 删除

```sql
UPDATE lessons SET category = 'preference' WHERE id = 'abc123';
DELETE FROM lessons WHERE created_at < 1700000000.0;
-- 注意：UPDATE / DELETE 不带 WHERE 会作用于全表
```

---

## 2. 查询操作（SELECT 进阶）

### 2.1 基础过滤与排序

```sql
SELECT id, agent_name, lesson FROM lessons
WHERE agent_name = 'gis_assistant:user1'
  AND category IN ('success', 'preference')
  AND lesson LIKE '%缓冲区%'                    -- 模糊匹配
  AND created_at BETWEEN 1700000000 AND 1800000000
  AND lesson NOT LIKE '%失败%'
ORDER BY created_at DESC                        -- 倒序
LIMIT 10 OFFSET 0;                              -- 分页
```

### 2.2 聚合与分组

```sql
-- 每个用户每种类别的 lesson 数量
SELECT agent_name, category, COUNT(*) AS cnt
FROM lessons
GROUP BY agent_name, category
HAVING COUNT(*) >= 3                            -- 分组后过滤（HAVING）
ORDER BY cnt DESC;

-- 常用聚合
SELECT
  COUNT(*)        AS total,
  COUNT(DISTINCT agent_name) AS users,
  MIN(created_at) AS first_ts,
  MAX(created_at) AS last_ts,
  AVG(confidence) AS avg_conf
FROM user_preferences;
```

### 2.3 子查询

```sql
-- 找出「比该用户平均时间晚」的 lesson
SELECT * FROM lessons l
WHERE l.created_at > (
  SELECT AVG(created_at) FROM lessons
  WHERE agent_name = l.agent_name
);

-- EXISTS：只查有偏好记录的用户 lesson
SELECT * FROM lessons l
WHERE EXISTS (
  SELECT 1 FROM user_preferences p
  WHERE p.key = 'settings:v1'
    AND p.value LIKE '%' || l.agent_name || '%'
);
```

### 2.4 窗口函数（排名 / 分组取前 N）

```sql
-- 每个用户最近一条 lesson（ROW_NUMBER 取分组内第 1 名）
SELECT id, agent_name, lesson, created_at FROM (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY agent_name ORDER BY created_at DESC) AS rn
  FROM lessons
) WHERE rn = 1;

-- 累计 / 排名
SELECT id, agent_name, created_at,
       RANK()       OVER (ORDER BY created_at DESC) AS rk,
       SUM(1)       OVER (PARTITION BY agent_name)  AS user_total,
       LAG(created_at) OVER (ORDER BY created_at)   AS prev_ts
FROM lessons;
```

### 2.5 CASE 条件逻辑

```sql
SELECT id, lesson,
  CASE
    WHEN lesson LIKE '%失败%' THEN 'bad'
    WHEN lesson LIKE '%成功%' THEN 'good'
    ELSE 'other'
  END AS verdict
FROM lessons;
```

---

## 3. 多表联查（JOIN）

### 3.1 INNER JOIN（两边都匹配）

```sql
-- lesson + 它的向量（有向量才算）
SELECT l.id, l.lesson, length(e.embedding) AS emb_len
FROM lessons l
INNER JOIN lesson_embeddings e ON l.id = e.lesson_id;
```

### 3.2 LEFT JOIN（保留左表全部，右表可空）

```sql
-- 所有 lesson，没向量的也显示
SELECT l.id, l.agent_name, l.lesson,
       CASE WHEN e.lesson_id IS NULL THEN '无向量' ELSE '有向量' END AS emb_status
FROM lessons l
LEFT JOIN lesson_embeddings e ON l.id = e.lesson_id;
```

**易错点**：过滤右表条件放 `WHERE` 会把 LEFT JOIN 变成 INNER 效果，应放 `ON`：
```sql
-- 错误：会把没有该偏好的用户行删掉
LEFT JOIN user_preferences p ON l.agent_name = p.agent_name
WHERE p.key = 'settings:v1';

-- 正确：先按条件连，再取全部左表行
LEFT JOIN user_preferences p
  ON l.agent_name = p.agent_name AND p.key = 'settings:v1';
```

### 3.3 RIGHT / FULL OUTER JOIN（SQLite 不支持，用 LEFT + UNION 模拟）

```sql
-- RIGHT JOIN（保留右表全部）≈ 交换表顺序的 LEFT JOIN
SELECT * FROM user_preferences p
LEFT JOIN lessons l ON l.agent_name = p.agent_name;

-- FULL OUTER JOIN（两边全保留）≈ 两个 LEFT JOIN 求并集
SELECT l.id, p.key
FROM lessons l
LEFT JOIN user_preferences p ON l.agent_name = p.agent_name
UNION
SELECT l.id, p.key
FROM user_preferences p
LEFT JOIN lessons l ON l.agent_name = p.agent_name;
```

### 3.4 自连接（同一张表关联自己）

```sql
-- 每条 lesson 的「前一条」：找比它早的最新一条
SELECT a.id AS cur, a.created_at,
       (SELECT MAX(b.created_at) FROM lessons b
        WHERE b.agent_name = a.agent_name AND b.created_at < a.created_at) AS prev_ts
FROM lessons a;
```

### 3.5 UNION（纵向合并去重）与 UNION ALL

```sql
SELECT agent_name, 'lesson' AS src FROM lessons
UNION                                    -- 去重
SELECT agent_name, 'pref'   AS src FROM user_preferences;

SELECT agent_name, 'lesson' AS src FROM lessons
UNION ALL                                -- 不去重，更快
SELECT agent_name, 'pref'   AS src FROM user_preferences;
```

### 3.6 三表联查实战

```sql
-- 每个用户的自定义模型 + 其成功 lesson 数量 + 是否有偏好设置
SELECT m.user_key,
       COUNT(DISTINCT m.id)               AS model_cnt,
       COUNT(DISTINCT l.id)               AS lesson_cnt,
       MAX(p.value)                       AS settings_json
FROM user_models m
LEFT JOIN lessons l ON l.agent_name = m.user_key
LEFT JOIN user_preferences p ON p.key = 'settings:v1'
GROUP BY m.user_key
HAVING lesson_cnt >= 1
ORDER BY lesson_cnt DESC;
```

---

## 4. 项目实操示例（可直接跑）

### 4.1 查最近 10 条 GIS 经验

```python
import sqlite3
con = sqlite3.connect(r"H:\ai-dev-platform\long_term_memory.db")
con.row_factory = sqlite3.Row
rows = con.execute(
    "SELECT agent_name, category, substr(lesson, 1, 60) AS brief, created_at "
    "FROM lessons ORDER BY created_at DESC LIMIT 10"
).fetchall()
for r in rows:
    print(r["created_at"], r["agent_name"], r["brief"])
```

### 4.2 某个用户的所有偏好与模型

```sql
SELECT 'pref' AS kind, key, value FROM user_preferences
WHERE key = 'settings:v1'
UNION ALL
SELECT 'model', id, label || ' @ ' || base_url FROM user_models
WHERE user_key = 'gis_assistant:user1';
```

### 4.3 清理三个月前的旧经验（维护脚本常用）

```sql
DELETE FROM lessons WHERE created_at < strftime('%s', 'now', '-3 months');
```

---

## 5. 易错点清单

1. `LEFT JOIN` 右表过滤条件放 `WHERE` → 变内连接（放 `ON`）；
2. `GROUP BY` 后 SELECT 的列必须是分组列或聚合函数（MySQL 宽松，其他库报错）；
3. `UPDATE` / `DELETE` 忘带 `WHERE` → 全表生效；
4. SQLite 不支持 `RIGHT JOIN` / `FULL OUTER JOIN` / `SELECT DISTINCT ON`，用 LEFT + UNION 模拟；
5. 字符串拼接用 `||`（SQLite），不是 `+`；
6. 布尔值用 `1/0`，不是 `true/false`；
7. 日期建议存时间戳（REAL/INTEGER），比较直接用数值，不要存字符串；
8. 大批量删除/更新先 `BEGIN; ... COMMIT;` 包裹，或先 `SELECT COUNT(*)` 确认影响行数。
