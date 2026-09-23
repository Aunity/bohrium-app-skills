# Stage DAG and Worker Routing

阶段状态保留 S0–S12，主 Agent按依赖 gate 调度，不把它当成必须由一个 Worker 顺序跑完的脚本。

## DAG

```text
S0 Bootstrap
     ↓
S1 Product / science / license discovery
     ↓
S2 CLI / runtime / fixture inventory
     ↓
                                  S3 Adapter / Form / Result
                                   ├─ adapter code
                                   ├─ schema
                                   ├─ tests and fixtures
                                   └─ bilingual docs
                                              ↓ join + review
                                         S4 Local Acceptance
                                              ↓
                                         S5 CPU Node Assembly
                                              ↓
                                         S6 Immutable Image
                                              ↓
                                         S7 Image Runtime Tests
                                              ↓
                                         S8 Live App Save
                                              ↓
                                         S9 App Page Test
                                              ↓
           license + security + science gates ──→ S10 API / Publication
                                                       ↓
                                                S11 App-specific Skill
                                                       ↓
                                                   S12 Closeout
```

`workflow-state.json` 中的顶层 `depends_on` 是 gate 顺序。主 Agent可以把阶段拆成只读调查、离线准备和 live mutation 子任务，但只有顶层依赖满足后才能通过该阶段。

## 阶段契约

| 阶段 | 主要产物或证据 | Worker / Skill | 退出边界 |
| --- | --- | --- | --- |
| S0 | 源码基线、dirty 状态、初始 state/ledger | 主 Agent；必要时只读 Worker | 基线和下一动作明确 |
| S1 | 用户任务、App 形态、科学/License/安全限制 | Discovery / `$bohrium-develop-app` | 产品契约已确认 |
| S2 | 真实 CLI、绝对路径、版本、资源、成功/失败 fixture | Runtime Discovery / `$bohrium-develop-app` | 公共操作均有真实样例 |
| S3 | adapter、Schema、结果/provenance、测试和文案 | Adapter / `$bohrium-develop-app` | 实现候选可独立复核 |
| S4 | 单测、真实 CLI、JSON replay、Preview、secret scan | Reviewer / `$bohrium-develop-app` | `local-ready` |
| S5 | CPU Node identity、CLI share 传输、安装路径和 snapshot hygiene | Runtime / `$bohrium-release-app` | `node-ready`（仅表示镜像内容已组装） |
| S6 | 新不可变 tag、image ID/digest、rollback image | Release Operator / `$bohrium-release-app` | 候选镜像 available |
| S7 | 同一不可变镜像的运行测试、结果/manifest/log 下载 | Release Operator / `$bohrium-release-app` | `image-ready` |
| S8 | 私有 App/version、保存的镜像/入口/Schema/资源/双语资料 | Release Operator；人工控制台 checkpoint | live config 已读回 |
| S9 | 真实 App 页最小任务、条件字段、上传、结果下载 | Release Operator + Reviewer | `app-ready` |
| S10 | License、安全、科学、API E2E、公开和回滚门禁 | Release Operator / `$bohrium-release-app` | `api-ready`/`release-ready` |
| S11 | plan/schema/job lifecycle 客户端与真实最小 E2E | Skillizer / `$bohrium-create-app-skill` | `skill-ready` |
| S12 | 最终 ledger、限制、回滚、资源状态和运维说明 | 主 Agent + Reviewer | 精确完成边界 |

## 可以并行

- S1 中的产品、科学、License 和安全调查；S2 中不同公共操作的 CLI、运行时与 fixture 盘点。
- S3 中写入路径互不重叠的 adapter、Schema、测试 fixture 和双语文案。
- S4 的 lint、单测、Schema 审查和 secret scan；集成结论由 Reviewer 汇总。
- S3 完成后准备 S8 的离线控制台填写包。
- S1/S4 后提前调查 S10 的 License、安全和科学门禁。
- S3 后创建 S11 的离线 contract、`plan` 和 mock 草稿，远端命令保持 fail closed。
- 平台 mutation 执行期间，可并行不写 ledger、不依赖 mutation 结果的只读工作。

并行任务必须有不同 `allowed_write_paths`，且不能共享外部 mutation 锁。

## 必须串行

```text
S5 CPU Node transfer/install/cleanup
  → S6 snapshot/build image
  → S7 immutable-image runtime tests
  → S8 live App save
  → S9 App page test
  → S10 License/API/publication mutation
```

同一镜像 tag、同一 Job 是否重试、同一 App version、License、价格和公开状态的操作不得并行。App key、Schema、结果和 API 未稳定前，不得启用 S11 远端命令。

## Human 和 Authority Checkpoint

以下情况主 Agent停止调度依赖任务：

- 创建/停止 Node、远端安装、构建或快照镜像；
- 提交/终止 Job；
- 创建或修改 App、License、价格、公开状态；
- 覆盖持久化数据或下载目标；
- 登录、验证码、需要用户产品决定或无法安全解析 exact target。

登录和验证码使用 `console-handoff.md`。用户完成后，新的只读 Worker 必须核验 App key/version 和保存配置；仅凭“已填写”或截图不能通过 S8。

S5 创建 Node 时只选当前可用的 CPU 规格。创建明确失败立即结束该
attempt 并报告，不自动重试或改选另一 Node；结果不确定时只读查询同一
request/Node。文件通过 `bohr file upload ... share/... --project-id ...`
中转，使用现有 CLI profile，禁止自行创建 SSH identity、临时 key 或
AccessKey。`/share` 中的内容必须校验后安装到普通镜像目录。

## 身份变化与失效传播

| 变化 | 至少重置 |
| --- | --- |
| 源码或 adapter | S4–S12 中依赖它的 gate |
| Schema 或表单 | Preview、S8–S11 |
| wheel/bundle | S5–S10 |
| 镜像 identity | S7–S11 的运行证据 |
| App key/submodel/version | S9–S11 |
| License 或可见范围 | S10、S11 remote |
| SDK/CLI 平台行为 | 对应 runtime、release 或 API gate |

旧证据不能删除；标记为 stale，并记录触发失效的新 identity。

## 完成判定

阶段完成不是 Worker 数量或对话长度，而是 gate 证据：

- `local-ready` 不证明 Node、镜像或 App；
- `node-ready` 只证明 CPU Node 上的候选内容已完成组装，不证明运行时；
- `image-ready` 不证明保存的 App 配置；
- `app-ready` 不证明 License、API、科学或公开发布；
- `api-ready` 不自动等于 `release-ready`；
- `skill-ready` 必须基于稳定 App 契约和真实最小下载。

S12 只在所有适用 gate 有证据、持续计费资源状态明确、rollback 可执行且最终 handoff 完成后通过。
