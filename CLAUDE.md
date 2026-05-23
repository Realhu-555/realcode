# AI Dev Platform — Claude Code 项目规范

## 项目概述
多 Agent 协作的全自动 Web 应用开发平台。用户用自然语言描述想法，系统自动完成需求分析→架构设计→代码生成→测试→打包。

## 技术栈
- **语言**: Python 3.12+
- **编排框架**: LangGraph（Agent 状态机）
- **LLM 层**: 统一调用 DeepSeek V4 + MiniMax 2.7（兼容 OpenAI 格式）
- **包管理**: pip + venv
- **测试**: pytest + pytest-asyncio

## 项目结构
```
ai-dev-platform/
├── src/
│   ├── orchestrator/    # 调度中心（LangGraph 状态图）
│   ├── agents/          # 各专职 Agent（需求/架构/前后端/测试/部署）
│   ├── sandbox/         # 本地代码执行沙箱
│   ├── llm/             # LLM Provider + Prompts
│   ├── web/             # Web 界面（Phase 3）
│   └── utils/           # 配置工具
├── tests/               # 测试代码
├── SPEC.md              # 完整需求规格 & 技术方案
├── requirements.txt     # Python 依赖
└── .env                 # API Key（不入 git）
```

## 编码规范
- **Python 版本**: 3.12+
- **类型注解**: 所有公共函数必须标注参数和返回值类型
- **命名**: 类名 PascalCase，函数/变量 snake_case，常量 UPPER_SNAKE
- **导入顺序**: 标准库 → 第三方 → 项目内部，每组空一行
- **文档字符串**: 每个类和公共方法写三引号 docstring
- **行宽**: 不超过 100 字符
- **禁止**: `from module import *`，魔法数字（用常量）

## 命令
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 运行单个测试
pytest tests/test_e2e_requirement.py::test_requirement_agent_asks_when_vague -v

# 代码检查（如有 ruff）
ruff check src/
```

## Agent 模型分配
| Agent | 模型 | 原因 |
|-------|------|------|
| 需求分析 | MiniMax 2.7 | 中文对话多 |
| 架构师 | DeepSeek V4 | 推理要求高 |
| 后端开发 | DeepSeek V4 | 代码质量最高 |
| 前端开发 | MiniMax 2.7 | 分担压力 |
| 测试 | MiniMax 2.7 | 任务相对简单 |
| 部署/文档 | MiniMax 2.7 | 任务简单 |

## 开发原则
1. **TDD**: 先写测试，确认失败，再写实现，确认通过
2. **测试不过不准走**: 每个功能写完必须跑测试，全绿才算完成。一个红灯都不能留
3. **小步提交**: 每个 Task 完成后立即 git commit
4. **DRY**: 不重复代码，提取公共逻辑
5. **YAGNI**: 只实现当前需要的，不做"以后可能用到"的功能

## 当前阶段
Phase 1 — MVP：跑通"用户输入想法 → 需求分析 Agent → 产出 PRD"
按 SPEC.md 中的 6 个 Task 顺序实现
