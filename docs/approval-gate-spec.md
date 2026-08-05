# ApprovalGate 人工确认门 — 集成规范

> 给 Claude Code 的执行文档。按 Task 顺序实现。
>
> **创建日期：** 2026-08-05
> **目标：** 将已实现的 `src/orchestrator/gate.py` 接入真实流水线，前端补齐 approve/revise/redo 三操作 UI。
>
> **进度：** Task 1 ✅ | Task 2 ✅ | Task 3 ✅ | Task 4 ✅ | Task 5 ✅ | Task 6 ✅ | Task 7 ✅

---

## 一、现状诊断

### 1.1 已有资产

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/orchestrator/gate.py` | ✅ 完整实现 | `ApprovalGate` 类，三操作 + 超时放行 + WebSocket 通知回调 |
| `docs/design-agent-orchestration.md` §7 | ✅ 设计文档 | 全阶段人工介入的交互设计 |

### 1.2 断裂点（需要补的）

| 位置 | 问题 |
|------|------|
| `src/web/server.py` | **未 import ApprovalGate**，用简陋 `ConfirmRequest`（只有 confirmed/feedback 两个字段） |
| `src/web/server.py:/ws` | WebSocket 只处理 `subscribe` 一种 action，不处理 approve/revise/redo |
| `frontend/src/stores/ws.ts` | 只接收 progress 事件，未处理 `approval_required` |
| `frontend/src/stores/project.ts` | 只有 `confirm()` 一个方法，无 revise/redo 方法 |
| `frontend/src/api/client.ts` | 无 approve/revise/redo API 调用 |
| `frontend/src/views/Strategy.vue` | 只有确认/修改两个按钮，无重做按钮，无超时倒计时 |
| `frontend/src/components/StrategyCard.vue` | popover 内的修改输入框未绑定数据，点了没反应 |

### 1.3 当前流水线确认点

```
用户输入 → [创建项目] → 策略生成 → ⭐策略确认⭐ → 三渠道生成 → 审校 → DONE
```

**只有一个确认点**（策略确认），且只有"确认"和"修改"两种操作，没有"重做"。

---

## 二、目标架构

### 2.1 确认点扩展

每个关键阶段后都插入人工确认门：

```
用户输入 → 策略生成 → ⭐策略确认⭐ → 公众号内容生成 → ⭐公众号确认⭐
                                              → 知乎内容生成 → ⭐知乎确认⭐
                                              → 小红书内容生成 → ⭐小红书确认⭐
                                              → 审校 → ⭐审校确认⭐ → 导出 → DONE
```

**MVP 先做策略确认一个点**（替换现有简陋确认），后续阶段按需加。

### 2.2 三操作语义

| 操作 | 英文 | 含义 | 流水线行为 |
|------|------|------|-----------|
| ✅ 确认 | `approve` | 产出满意，继续 | 进入下一阶段 |
| ✏️ 修改 | `revise` | 方向对但需调整 | 携带 feedback 重新执行当前 Agent |
| 🔄 重做 | `redo` | 完全不对，换思路 | 清空当前产出，重新执行（不传旧内容） |

### 2.3 超时自动放行

- 默认 **5 分钟**（与 gate.py 中 `DEFAULT_TIMEOUT = 300` 一致）
- 超时 → 自动 `approve`，流水线继续，避免死锁
- 前端显示倒计时，到期前 60 秒变红闪烁提醒

### 2.4 交互流程

```
┌─ Agent 产出完成 ─────────────────────────────────────────────────────┐
│                                                                       │
│  1. server 调用 gate.wait_for_approval(client_id, stage, artifact)    │
│  2. gate 生成 pending_request，通过 WebSocket 推 approval_required    │
│  3. 前端收到后显示三按钮 + 倒计时                                      │
│  4. 用户点击按钮 → 前端 ws.send({action:"approve", ...})              │
│  5. server 收到 → gate.handle_user_action() → 唤醒等待协程            │
│  6. 流水线继续（进下一阶段 / 重当前阶段 / 重做当前阶段）               │
│  7. 超时 → gate 自动 APPROVE → 流水线继续                              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 三、改动范围

### 3.1 后端改动

**文件：`src/web/server.py`**

| 改动 | 说明 |
|------|------|
| 引入 `ApprovalGate` | `from src.orchestrator.gate import ApprovalGate, UserAction` |
| 初始化 gate 实例 | 全局单例，设置 `notify_callback` 指向 `ws_manager.broadcast` |
| 改造 `confirm_strategy` 路由 | 拆成两步：(1) agent 产出后 await gate.wait_for_approval；(2) 用户操作由 WebSocket 路由到 gate.handle_user_action |
| 新增 WebSocket action 处理 | 在 `/ws` 端点中处理 `action: "approve"/"revise"/"redo"` 消息 |

**文件：`src/orchestrator/gate.py`（微调）**

| 改动 | 说明 |
|------|------|
| `notify_callback` 签名适配 | 当前签名 `Callable[[str, dict], Awaitable[None]]`，需确认和 ws_manager.broadcast 兼容 |

### 3.2 前端改动

| 文件 | 改动 |
|------|------|
| `frontend/src/stores/ws.ts` | 新增 `approvalRequired` 事件状态 + `sendApprovalAction()` 方法 |
| `frontend/src/stores/project.ts` | 新增 `approve()` / `revise()` / `redo()` actions |
| `frontend/src/api/client.ts` | 新增 `submitApproval()` API 函数（或通过 WebSocket） |
| `frontend/src/components/ApprovalPanel.vue` | **新文件**：三按钮 + 倒计时 + 修改意见输入框 |
| `frontend/src/components/StrategyCard.vue` | 简化：去掉 popover，改用 ApprovalPanel |
| `frontend/src/views/Strategy.vue` | 引入 ApprovalPanel 替代手动确认逻辑 |
| `frontend/src/views/Preview.vue` | 预留后续阶段确认点插入位置 |

### 3.3 不变的文件

- `src/orchestrator/gate.py`：核心逻辑不改，只可能微调回调签名
- `src/orchestrator/state.py`：状态定义不变
- `src/agents/*.py`：Agent 逻辑不变
- 其他前端组件：不动

---

## 四、详细 Task 分解

### Task 1: 后端 — ApprovalGate 接入 server.py

**目标：** `server.py` 中引入 `ApprovalGate`，替代 `ConfirmRequest`。

**文件：`src/web/server.py`**

**具体改动：**

1. **导入 gate 模块**
   ```python
   from src.orchestrator.gate import ApprovalGate, UserAction
   ```

2. **全局初始化**
   ```python
   approval_gate = ApprovalGate(timeout=300)
   approval_gate.set_notify_callback(ws_manager.broadcast)
   ```

3. **改造 `confirm_strategy` 路由** — 当前逻辑是直接执行 confirm → 生成，改为先等待审批：
   - 删除 `/confirm-strategy` POST 路由
   - 在 `create_project` 中，策略生成完成后调用 `await approval_gate.wait_for_approval(...)`
   - 根据返回的 `ApprovalResult` 决定下一步：
     - `APPROVE` → 继续生成
     - `REVISE` → 带 feedback 重新执行策略 Agent
     - `REDO` → 清空策略，重新执行

4. **WebSocket `/ws` 新增 action 处理**
   ```python
   # 在现有的 while True 循环中，新增处理：
   action = data.get("action")
   if action in ("approve", "revise", "redo"):
       request_id = data.get("request_id")
       feedback = data.get("feedback") if action == "revise" else None
       approval_gate.handle_user_action(
           request_id=request_id,
           action=UserAction(action),
           feedback=feedback,
       )
   ```

5. **新增进度推送类型**：推送 `approval_required` 事件时需要包含 `request_id`，前端才能回传。

**验证标准：**
- 创建项目 → 策略生成后 → 后端暂停在 `wait_for_approval`
- 通过 WebSocket 发送 `{"action": "approve", "request_id": "..."}` → 流水线继续
- 通过 WebSocket 发送 `{"action": "revise", "request_id": "...", "feedback": "加强安全"}` → 策略 Agent 重新执行
- 不发送任何操作 → 5 分钟后自动通过
- 发送 `{"action": "redo", "request_id": "..."}` → 策略清空重做

---

### Task 2: 后端 — 通知回调适配

**目标：** 确保 `ApprovalGate` 的 `notify_callback` 和 `ws_manager.broadcast` 签名兼容。

**文件：`src/orchestrator/gate.py`（微调）**

当前回调签名：
```python
callback: Callable[[str, dict], Awaitable[None]]  # (client_id, data)
```

`ws_manager.broadcast` 签名：
```python
async def broadcast(self, project_id: str, event: dict)  # (project_id, event)
```

**问题：** gate 传 `client_id`，broadcast 要 `project_id`。且 broadcast 只推给订阅了该 project 的客户端。

**方案：** 在 `set_notify_callback` 时用 lambda 适配：
```python
async def notify_approval(client_id: str, data: dict):
    project_id = data.get("project_id")  # 需要 data 中包含 project_id
    await ws_manager.broadcast(project_id, data)

approval_gate.set_notify_callback(notify_approval)
```

**验证标准：**
- 策略完成后，订阅了该 project 的 WebSocket 客户端收到 `{"type": "approval_required", "request_id": "...", ...}`

---

### Task 3: 前端 — WebSocket Store 扩展

**目标：** `wsStore` 能接收 `approval_required` 事件并发送 approve/revise/redo 操作。

**文件：`frontend/src/stores/ws.ts`**

**具体改动：**

1. **新增事件类型接口**
   ```typescript
   export interface ApprovalRequiredEvent {
     type: "approval_required"
     request_id: string
     project_id: string
     stage: string
     artifact: {
       full_content: string
       summary: string
       version: number
     }
     timeout: number
   }
   ```

2. **新增状态**
   ```typescript
   const currentApproval = ref<ApprovalRequiredEvent | null>(null)
   ```

3. **`onMessage` 中处理 `approval_required` 消息**：解析后存入 `currentApproval`

4. **新增 `sendApprovalAction` 方法**
   ```typescript
   function sendApprovalAction(requestId: string, action: "approve" | "revise" | "redo", feedback?: string) {
     if (!ws) return
     ws.send(JSON.stringify({
       action,
       request_id: requestId,
       feedback,
     }))
     currentApproval.value = null
   }
   ```

5. **新增 `clearApproval` 方法**

6. **导出：** `currentApproval`, `sendApprovalAction`, `clearApproval`

**验证标准：**
- 后端推送 `approval_required` → `wsStore.currentApproval` 有值
- 调用 `sendApprovalAction("xxx", "approve")` → WebSocket 发出正确消息
- 发完后 `currentApproval` 被清空

---

### Task 4: 前端 — ApprovalPanel 审批面板组件

**目标：** 可复用的审批 UI 组件，显示三按钮 + 倒计时。

**文件：`frontend/src/components/ApprovalPanel.vue`（新建）**

**Props：**
```typescript
{
  stage: string           // 当前阶段名称，如 "策略"
  content: string         // 待审批内容（Markdown/纯文本）
  requestId: string       // 审批请求 ID
  timeoutSeconds: number  // 剩余超时秒数（从 approval_required 事件获取）
}
```

**Emits：**
```typescript
{
  approve: []
  revise: [feedback: string]
  redo: []
}
```

**UI 规范（参考设计文档 §7.3）：**

```
┌──────────────────────────────────────────────┐
│  ✅ 策略文档已生成（v1）          ⏱ 4:32    │
│                                              │
│  [内容预览区域（max-h-[300px] overflow-y）]   │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ ✅ 确认    │ │ ✏️ 修改    │ │ 🔄 重做   │     │
│  └──────────┘ └──────────┘ └──────────┘     │
│                                              │
│  修改意见（选"修改"时展开）：                  │
│  ┌──────────────────────────────────┐        │
│  │                                  │        │
│  └──────────────────────────────────┘        │
│                                    [发送]     │
└──────────────────────────────────────────────┘
```

**行为：**
- 倒计时：`timeoutSeconds` 为正时从当前值倒数到零，剩 60 秒时变红 + 脉冲动画
- "确认"按钮 → `emit('approve')`
- "修改"按钮 → 展开输入框，输入后点发送 → `emit('revise', feedback)`
- "重做"按钮 → 弹确认对话框（`n-modal` 或 `n-popconfirm`）"确定要重做吗？当前产出将被丢弃" → `emit('redo')`
- 超时归零 → 自动 `emit('approve')`
- 加载态：按钮 disabled + spinner

**倒计时实现：**
```typescript
const countdown = ref(props.timeoutSeconds)
const isExpiring = computed(() => countdown.value <= 60)
const displayTime = computed(() => {
  const m = Math.floor(countdown.value / 60)
  const s = countdown.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

onMounted(() => {
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
      emit('approve')
    }
  }, 1000)
})

onUnmounted(() => clearInterval(timer))
```

**验证标准：**
- 组件正常渲染三按钮 + 倒计时
- 点击确认 → approve 事件触发
- 点击修改 → 输入框展开 → 输入内容 → 发送 → revise 事件触发（带 feedback）
- 点击重做 → 确认框 → 确认 → redo 事件触发
- 倒计时到 0 → 自动 trigger approve
- 倒计时 < 60 秒 → 红色闪烁

---

### Task 5: 前端 — Store + API 集成

**目标：** `projectStore` 和 `api/client.ts` 支持三操作。

**文件：`frontend/src/api/client.ts`**

新增（如果通过 HTTP 而非 WebSocket 走审批）：

```typescript
export async function submitApproval(
  projectId: string,
  action: "approve" | "revise" | "redo",
  feedback?: string,
) {
  const { data } = await client.post(`/content-projects/${projectId}/approval`, {
    action,
    feedback,
  })
  return data
}
```

**但 MVP 优先用 WebSocket 走审批**（因为需要实时双向通信），HTTP 方式作为 fallback 保留。

**文件：`frontend/src/stores/project.ts`**

新增方法：
```typescript
function approve() { wsStore.sendApprovalAction(currentRequestId, "approve") }
function revise(feedback: string) { wsStore.sendApprovalAction(currentRequestId, "revise", feedback) }
function redo() { wsStore.sendApprovalAction(currentRequestId, "redo") }
```

**验证标准：**
- `approve()` → WebSocket 发出 `{"action":"approve","request_id":"..."}`
- `revise("改一下")` → WebSocket 发出 `{"action":"revise","request_id":"...","feedback":"改一下"}`
- `redo()` → WebSocket 发出 `{"action":"redo","request_id":"..."}`

---

### Task 6: 前端 — Strategy 页面集成 ApprovalPanel

**目标：** 用 `ApprovalPanel` 替换 `Strategy.vue` + `StrategyCard.vue` 中的简陋确认。

**文件：`frontend/src/views/Strategy.vue`**

改动：
- 引入 `ApprovalPanel` 组件
- 监听 `wsStore.currentApproval`，有值时显示 ApprovalPanel
- 不再直接调用 `projectStore.confirm()`，改为通过 ApprovalPanel events → wsStore.sendApprovalAction

**文件：`frontend/src/components/StrategyCard.vue`**

改动：
- 移除外层 confirm/modify 按钮
- 改为纯内容展示卡片（标题 + 策略文本 + loading）
- 去掉 n-popover（原修改输入框移到 ApprovalPanel）

**验证标准：**
- 策略页面渲染 ApprovalPanel
- 三按钮功能正常
- 倒计时可见
- 修改输入框可用
- 超时自动通过后跳转预览页

---

### Task 7: 端到端测试

**目标：** 自动化测试覆盖审批流程。

**文件：`tests/integration/test_approval_gate.py`（新建）**

**测试用例：**

```python
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from src.orchestrator.gate import ApprovalGate, UserAction, ApprovalResult


class TestApprovalGate:
    """ApprovalGate 单元测试"""

    def test_approve_action(self):
        gate = ApprovalGate()
        result = gate.handle_user_action("test:strategy:1", UserAction.APPROVE)
        assert result.action == UserAction.APPROVE
        assert result.approved is True

    def test_revise_action(self):
        gate = ApprovalGate()
        result = gate.handle_user_action("test:strategy:1", UserAction.REVISE, "改一下")
        assert result.action == UserAction.REVISE
        assert result.feedback == "改一下"
        assert result.approved is False

    def test_redo_action(self):
        gate = ApprovalGate()
        result = gate.handle_user_action("test:strategy:1", UserAction.REDO)
        assert result.action == UserAction.REDO
        assert result.approved is False

    @pytest.mark.asyncio
    async def test_timeout_auto_approve(self):
        gate = ApprovalGate(timeout=0.1)
        artifact = {"full_content": "test", "summary": "", "version": 1}
        result = await gate.wait_for_approval("test_client", "strategy", artifact)
        assert result.action == UserAction.APPROVE
        assert result.approved is True

    @pytest.mark.asyncio
    async def test_user_action_wakes_wait(self):
        gate = ApprovalGate(timeout=30)
        artifact = {"full_content": "test", "summary": "", "version": 1}

        async def user_acts():
            await asyncio.sleep(0.1)
            gate.handle_user_action("test:strategy:1", UserAction.APPROVE)

        result_task = asyncio.create_task(
            gate.wait_for_approval("test", "strategy", artifact)
        )
        await user_acts()
        result = await result_task

        assert result.action == UserAction.APPROVE
```

**文件：`tests/integration/test_approval_websocket.py`（新建）**

**测试用例：**
- WebSocket 连接 → 创建项目 → 收到 `approval_required` 事件
- 发送 `approve` action → 流水线继续
- 发送 `revise` action → 策略重新生成
- 发送 `redo` action → 策略清空重建

**验证标准：**
- `pytest tests/ -v -k "approval"` 全部通过
- 覆盖 approve/revise/redo/超时四种场景
- WebSocket 集成测试通过

---

## 五、组件树变更

```
前端组件结构（变更后）：

views/Strategy.vue
├── ProgressTimeline.vue          （不变）
├── StrategyCard.vue              （简化：纯内容展示，去按钮）
└── ApprovalPanel.vue             【新建：三按钮 + 倒计时】

views/Preview.vue                 （预留 ApprovalPanel 插入点）
├── ProgressTimeline.vue
├── ContentPanel.vue
├── ReviewReport.vue
└── ApprovalPanel.vue             【预留：审校确认】
```

## 六、实现顺序

```
Task 1 (后端 gate 接入)     ← 核心，必须先做
    ↓
Task 2 (回调适配)           ← 与 Task 1 强依赖
    ↓
Task 3 (ws Store 扩展)      ← 需 Task 1 完成后端才能联调
    ↓
Task 4 (ApprovalPanel 组件)  ← 可独立开发，用 mock 数据
    ↓
Task 5 (Store + API 集成)   ← 依赖 Task 3 + Task 4
    ↓
Task 6 (Strategy 页面集成)   ← 依赖 Task 4 + Task 5
    ↓
Task 7 (端到端测试)         ← 依赖全部
```

---

## 七、边界情况

| 场景 | 处理 |
|------|------|
| 用户关闭页面 | `ws_manager.disconnect` 清理连接，`ApprovalGate` 继续等超时 |
| WebSocket 断连重连 | 重连后重新 subscribe project，但不会重发 `approval_required`（gate 的 pending 一次性消费） |
| 用户连续点多次确认 | 前端按钮点击后立即 disabled，后端 `handle_user_action` 检查 `status == "waiting"` 才处理 |
| 超时后用户才操作 | `handle_user_action` 找不到 pending → 返回无操作 |
| Revise 后 LLM 产出又需要确认 | 正常循环：revise → agent re-run → 新的 `wait_for_approval` |
| Redo 后 LLM 产出又需要确认 | 同上 |
| 多个项目同时运行 | gate 用 `client_id:stage:version` 做 request_id，天然隔离 |

---

## 八、后续扩展

Phase 1 先完成策略阶段的三操作确认。后续可扩展：

- 公众号/知乎/小红书内容生成后各加一个确认点
- 审校报告确认点
- 增加"跳过确认"设置（高级用户不需要每步确认）
- 审批历史记录（存储每次 approve/revise/redo 操作到 SQLite）
