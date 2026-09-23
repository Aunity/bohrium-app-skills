# Orchestration Contract

本契约把 Bohrium App 生命周期建模为“一个主 Agent 控制，多名短生命周期 Worker 执行”。仓库文件是长期记忆；聊天内容和 Worker 自述不是完成证据。

## 主 Agent 边界

主 Agent（Orchestrator）负责：

- 读取和核对 durable state；
- 计算当前可执行任务；
- 分配文件和外部资源锁；
- 生成 Worker 任务信封并监督执行；
- 检查结果、安排独立复核、推进 gate；
- 更新 `workflow-state.json`，产生下一条精确动作；
- 在需要费用、平台变更、产品决定或人工登录时停在 checkpoint。

主 Agent 默认不实现适配器，也不执行 Bohrium 外部变更。它可以做只读检查、状态合并和轻量验证。Worker 不得继续创建子 Agent；所有任务都由主 Agent直接派发和回收。

## 单写者与锁

| 对象 | 唯一写入者 |
| --- | --- |
| `docs/bohrium/workflow-state.json` | 主 Agent |
| `docs/bohrium/release-record.json` | 当前唯一 Release Operator |
| `docs/bohrium/handoffs/<task-id>.md` | 对应 Worker，仅新建不覆盖 |
| 源码、Schema、测试、文档 | 获得精确路径锁的 Worker |
| Node、镜像、Job、App、License、公开状态 | 当前唯一 Release Operator |

同一路径不能有两个写 Worker。只读 Worker 可以共享输入。所有平台 mutation 共用一个全局锁；一次授权只覆盖一个写明 exact target、effect、cost、rollback 和 evidence 的动作。

## 启动与恢复

每次主 Session 都执行同一启动协议：

1. 读取 `workflow-state.json`、`release-record.json`、`app-brief.md` 和最新 handoff。
2. 检查 `state_revision`、Git 状态、源码 revision，以及相关 artifact/schema hash。
3. 校验状态和发布记录结构；不能证明的值保持 `null`、`unknown` 或 `pending`。
4. 对账 active assignment、active mutation、已有文件变化和不可变资源 ID。
5. 上游身份变化时，将真正依赖它的下游 gate 置回 `pending`，保留旧证据并标记 stale。

恢复规则：

- Worker 有结果文件：校验后进入 ingest；
- 只有局部文件变化：标记 `partial`，复核后用新 attempt 重派；
- 无结果且无变化：标记 `abandoned`，释放路径锁后重派；
- CPU Node 创建明确失败：停止并报告，不自动重试或改选另一 Node；
- Node、Image、Job 或 App 状态不确定：先查询同一 request 或 ID；
- snapshot 超时：按唯一 tag 恢复，禁止再次创建；
- Job 等待超时：恢复同一 Job ID，禁止重新提交；
- 外部对象无法唯一解析：进入 `blocked`，不猜测、不执行新 mutation。

## 主循环

```text
BOOT
  读取、校验并恢复 durable state
RECONCILE
  核对事实、证据 freshness、身份变化和外部对象
PLAN
  从阶段 DAG 计算 ready tasks，分配路径锁和 mutation 锁
DISPATCH
  持久化 assignment，再创建 fork_turns="none" 的 Worker
MONITOR
  收集结果；中断或超时时按已有文件/ID 恢复
INGEST
  验证 baseline、diff、hash、测试、证据和权限边界
REVIEW
  对代码变更和 gate 候选安排独立 Reviewer
COMMIT
  主 Agent递增 state_revision，写状态和下一动作
LOOP
  继续 ready task，或停在用户授权/人工 checkpoint/完成态
```

dispatch 前必须先把 task ID、attempt、owner、baseline revision、路径锁和授权范围写入状态。Worker 返回不能直接把 gate 升为 `passed`；主 Agent只能在证据和独立复核满足退出条件后推进阶段。

## Worker 创建规则

Worker 必须使用 `fork_turns="none"`。不要把完整聊天历史传给它；在 prompt 中明确仓库路径、必读文件和任务信封，使 Worker 只依赖 durable state。

任务信封至少包含：

```json
{
  "schema": "bohrium-agent-task/v1",
  "task_id": "S3-adapter-a1",
  "attempt": 1,
  "workflow_revision": 7,
  "role": "adapter",
  "stage": "S3",
  "objective": "one bounded outcome",
  "repository_root": "/workspace/project",
  "required_skills": ["bohrium-develop-app"],
  "source_identity": {"revision": "...", "sha256": null, "dirty": true},
  "inputs": {"app_brief": "docs/bohrium/app-brief.md"},
  "allowed_write_paths": ["bohrium/src/"],
  "forbidden_write_paths": ["docs/bohrium/workflow-state.json"],
  "authorized_external_actions": [],
  "exit_gates": [{"id": "adapter.local_tests", "required": true, "criterion": "tests pass", "evidence_required": ["test log"]}],
  "evidence_directory": "docs/bohrium/evidence/S3",
  "created_at": "2026-08-26T00:00:00Z"
}
```

Worker prompt 必须写明：不得扩展范围、不得 spawn、不得猜平台身份、不得显示秘密、不得修改状态文件，以及遇到冲突时返回主 Agent。

## Worker 返回契约

Worker 的最终结果必须包含：

```json
{
  "schema": "bohrium-agent-result/v1",
  "task_id": "S3-adapter-a1",
  "attempt": 1,
  "workflow_revision": 7,
  "role": "adapter",
  "stage": "S3",
  "status": "passed",
  "summary": "...",
  "source_identity": {"before": {"revision": "...", "sha256": null, "dirty": true}, "after": {"revision": "...", "sha256": null, "dirty": true}, "matches_task_spec": true},
  "files_changed": [],
  "commands": [],
  "external_mutations": [],
  "gates": [{"id": "adapter.local_tests", "required": true, "status": "passed", "evidence": ["docs/bohrium/evidence/S3/tests.log"], "reason": "tests passed"}],
  "facts": [],
  "decisions_needed": [],
  "blockers": [],
  "risks": [],
  "next_actions": [],
  "secret_review": {"performed": true, "findings": 0, "evidence_path": "docs/bohrium/evidence/S3/secret-scan.txt"}
}
```

Worker 状态只使用 `passed`、`partial`、`blocked` 或 `failed`；其中 `passed` 只表示该任务信封的退出条件满足。只有主 Agent可以把阶段状态提升为 `passed`。

## Skill 路由

- Discovery、Adapter、本地验收和工程 Reviewer：`$bohrium-develop-app`
- CPU Node 镜像组装、不可变镜像测试、App、License、API 和发布：`$bohrium-release-app`
- App-specific Skill：`$bohrium-create-app-skill`；需要初始化或修改 Skill 包时再使用 `$skill-creator`

主 Agent在任务信封和 prompt 中显式点名所需 Skill。不要让一个 Worker 同时跨越开发、发布和 Skill 化权限边界。

## 提升 gate 的最低条件

主 Agent只在以下条件全部满足后提升 gate：

1. Worker baseline 与当前状态仍兼容；
2. 实际文件和平台读回与结果声明一致；
3. 每个 passed gate 都有命令、UTC 时间、身份、结果和证据引用；
4. 独立 Reviewer 已通过；
5. 无越权修改、秘密泄露或未解决冲突；
6. 更高层 gate 没有被低层测试替代。

当没有 ready task 时，主 Agent必须明确返回 `awaiting_authority`、`awaiting_human`、`blocked` 或完成边界，例如 `image-ready; app acceptance pending`。
