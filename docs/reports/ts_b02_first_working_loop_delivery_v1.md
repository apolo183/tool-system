# TS-B02：首个真实开发闭环交付安排

本次调整的是交付组织：以 DGX ARM64 上一个真实、隔离、可验证的开发闭环为终点，把必要的直接依赖读取、实现、普通修复和验证放进获批的功能批次。停止把每一次补证、接口文字修订或 helper 定位默认拆成新的交付任务。

本文件是规划记录，authority_effect: none。当前三文件任务只交付这份安排及显式 manifest/change-plan；它不批准源码实现、宿主操作、发行版组件安装、真实 Worker 或最终验收。合并这份规划也不激活这些权限。

## 1. 事实、历史和本次决定

- 本轮读取 canonical main 得到 75d005cee55a0e33bea17808faaba3085f740d8c，占用树 3f3263c305b1a5d50cb7760d9bb26d37c65d095e。当前状态文件仍将公开入口列为未接受、真实仓库执行阻断；它也保留一次真实 Worker 超时的历史记录，并非从未尝试真实执行。[R1]
- PR #234 已交付四 Gate 合同、Schema、test-only 判定器和 synthetic fixtures。本次不重开其审计、不重跑历史验收、不把合同交付写成后端通过。[R2]
- 用户提供的最新 CLI 回执为 STOPPED_TIME_BUDGET_EXPIRED：20分钟任务留下17组接口草稿，综合提案和D4未完成。封存文档的已核对摘要见第7节；它不是当前运行状态。[E1]
- 现有机制裁定建议 PID1 内部组件、原 cgroup/task 效果检查、MAC 约束和外部 owner 分担责任；这是建议，不是已实现能力，也不证明不存在等价方案。[E2]
- 用户在本对话明确同意纠正交付安排。本次据此准备三个规划文件和一个 Draft PR；未将该同意扩展为 PID1、内核、部署或真实执行授权。

不派发上一轮建议的45分钟纯文档任务。该草案和两次原 STOPPED 终态保留为历史；不续跑、不修补耗时、不返还旧预算。已完成的源码恢复、store 修复、四 Gate 和独立评审均保留，不因本次安排变化返工。SCOPE-01误读区段不成为源码事实依据；以后确需阅读须由新的明确读取范围覆盖，不能追认旧越界。

## 2. 交付终点和阶段结果

固定父交付身份建议为 TS-B02-FIRST-WORKING-LOOP-v1。它是规划身份，不是新运行生命周期枚举。下面各行是同一交付目标的责任和权限边界，不要求每行再发一次纯文档任务。

| 必须交付的结果 | 验收证据 | 不足以替代它的材料 |
| --- | --- | --- |
| 所选 ARM64 后端落实原隔离合同 | 绑定实际组件、宿主/客体、配置与原对象的行为证据；若使用 CubeSandbox，消费已完成四 Gate 合同 | 新报告、接口类型、synthetic PASS |
| 实际排他生命周期与硬期限 | 首次创建/控制FD前生效；原对象效果点拒绝；owner死亡/撤销/正常PID1行为及在途收尾证据 | token、typed guard、本地锁、先查InvocationID再按名操作 |
| 后端经公开入口被调用 | 实际传入与独立读回的请求/执行/候选身份一致，未知和拒绝保持阻断 | 单独 backend 示例或包装层调用 |
| 真实 Codex 完成一个最小开发任务 | 在单独批准的隔离工作副本中生成实际 diff；实际验证命令、输出和独立验收逐项绑定候选 | 伪 Codex、拷贝 acceptance 列表、自报 PASS |
| 失败与退出可靠 | 原绝对期限内终止及全部 reap/namespace/reference/helper/core 清理；实际验证次数、任务和运行终态一致 | 两份 populated=0、ACK、inactive/absent、计划中的验证次数 |

原六阶段、supervisor→controller、原绝对期限和共享最多5秒清理上限保持。CubeSandbox四 Gate 的专属场景期限与 no-core 期限分别继承，不合并或互相替换。PID1 delete-first 使原观测无法取得时，按原合同有界 BLOCKED，不延期、不按名重开、不增设哨兵。

首次真实闭环通过，只能接受其明确覆盖的范围；不自动关闭整个 P16、其他风险或生产部署。TS-B01 的相关重验，以及 TS-H01 对本闭环造成的真实计数/终态缺陷，纳入对应消费者批次；不将未相关的所有 OPEN 拉入关键路径。

## 3. 一次功能授权内怎样推进

后续实现开始前，以实际父源码清单和已有归档绑定工作副本，冻结组件边界、接口、验收集合和预算。不能用当前 main 覆盖仓库外 no-core candidate，也不能把旧 main 基线直接写入新仓库。源码父身份未知时先在同一任务中核对；不能自填摘要。

在批准的组件边界内，执行者自主完成以下工作，无需每个函数、文件片段或普通修复再请求批准：

1. 阅读直接调用者、声明、释放路径和必要测试，补齐影响当前实现的证据；同步把实际文件加入事先获准的组件清单。已确认的函数可以完整阅读，不再采用容易截错调用边界的机械行数片段。
2. 落实尚缺接口责任和失败语义，并直接实现；17组草稿只作起点，不作为外部真实权力的证明。K3须选定引用转移或增持并对应释放；J6须明确效果发生前后的返回和收尾。
3. 在同一候选上运行必要行为测试、诊断和有限修复；只检查真实改动及其影响边界，不重跑已封存材料恢复和无关验收。
4. 保存候选、已满足验收项、阻断和下一动作；最后交付代码差异、验证证据和运行限制。过程记录与必要报告随工程产出保存，不以增加报告数量算进度。

这些权限必须出现在下一份明确获批的组件范围和实际 manifest/change-plan 中。本规划不以通配目录自动扩大旧授权。发现范围外组件、公共契约矛盾、需改变宿主或新权限时，给出具体差异和一个需要用户决定的问题。普通实现错误留在原任务修复；原验收外的优化作为非阻断后续项。[R3][R4]

任务恢复沿用同一身份、起点、候选、分支、修复次数和周期记录。已封存终态不得自动恢复；确需新授权时保留旧账，不通过v2/v3或新包名重置预算。每轮须减少阻断、增加通过项，或产生改变当前决定的实质证据；重复状态或连续两轮无进展按现有规则停止。

## 4. 当前真正需要的授权决定

| 项目 | 本次状态 | 下一批准必须覆盖的内容 |
| --- | --- | --- |
| 三文件交付安排与Draft PR | 本次范围 | 仅规划记录；CI通过后仍不自动合并或执行 |
| tool-system/no-core 实现与接入 | 待源码实施授权 | 精确父身份、原对象所有权、直接调用者/测试、候选输出范围 |
| PID1与内核组件源码工程 | 待明确接受工程责任 | 仅隔离源码副本的编写、构建和测试；新增接口/声明/注册/释放/build/reexec责任必须显式进入范围 |
| MAC及宿主部署 | 未授权 | 有效策略、其他正常管理路径、实际namespace、旧FD、安装/加载/重启/回滚及资源范围 |
| ARM64后端行为验收 | 未授权 | 当前可用组件及摘要、观察者、精确命令/故障注入、原期限、资源清理和副作用预算 |
| 真实Codex最小任务 | 未授权 | 前项通过；隔离工作副本及改动范围、订阅传输和数据边界、独立验证及调用预算 |

不能在 deny_all 场景中为真实 Codex 偷开网络。所需 subscription_transport_only 边界必须按既有父合同单独明确授权；不改用 API key、抓取会话材料或暴露宿主凭据。真实下游仓库写入、PR生命周期和生产部署仍按原权限边界处理。

若接受现有机制建议，第一批应包含 PID1 pair 强制组件、内核原对象保护接口，以及实现它们不可缺的 owner/MAC 接线责任；不能先写一个没有实际强制提供端的 provider，再称后端已交付。报告已经点名的路径和职责如下，均是建议，实际父字节、声明和构建接线还必须在实施前核对。[E2]

| 组件 | 已知拟改路径/根域 | 实现责任 |
| --- | --- | --- |
| systemd | src/core/protected-pair.c/.h（拟新增）；dbus-manager.c、dbus-unit.c、manager.c、transaction.c、job.c、unit.c、service.c | 创建前真实准入；永久名字消费；作业/直接效果检查；真实原对象登记、失败、销毁和恢复 |
| Linux | kernel/cgroup/cgroup.c；具体声明、登记/UAPI及释放所有者待定位 | source/target/task效果检查；在途引用和锁序；撤销与正常清理不误绑 |
| no-core owner | nocore/exclusive_systemd.py（拟新增）；接管与原句柄直接责任以已核对父源码为准 | 实际效果FD持有、移交及旧引用失效；原六阶段和失败收尾 |
| MAC/部署 | 精确有效域及安装路径尚未冻结 | 实际约束管理主体和继承/传递/取回FD；保留Docker/GPU/snap/登录/电源/维护正常功能 |

这里没有证明上述方案是唯一可行方案，也没有批准修改 upstream。若选择另一实现方案或改变原合同，必须明确变更决定；不能在任务内部悄然换路线。工程可行性不足时，交付一个具体的架构/权限决定供用户裁定，不再自动生成下一轮纯补证任务。

## 5. 预算与交付建议

下一源码工程批次的建议窗口为4小时，Reasoning：Extra high，预留最后15分钟保存状态；最多3轮修复、1轮独立审查、4次完整受影响验收运行。直接依赖阅读、必要设计、实现、测试、构建与修复计入同一个窗口。该预算尚未批准，也不是4小时内完成整个后端的承诺；独立审查若要使用子代理须明确包含在后续批准中。

运行注入与部署另有精确权限和原合同预算；源码工程窗口不能延长运行硬期限。任何阶段都不自动安装缺失工具链、下载未知产物、提升权限或修改宿主；需要时一次列清具体对象、理由、效果和回滚供决定。

先持续保存任务状态，再进行耗时操作。时间、修复或调用预算耗尽就停止，不能在到期后补做功能或把网络断线/上下文压缩当作预算暂停。交接只需要一份TASK记录、候选差异与一份HANDOFF；不再要求用户为每个普通helper故障搬运独立包。

本次三文件任务的有限写入/验证/发布预算、停止条件及配对关系见随附 manifest/change-plan。旧45分钟草案不作为当前执行入口。现阶段不提供一个会误启动运行权限的Codex执行命令；下一份正式指令只在上述源码工程责任被明确接受后派发，并固定Reasoning：Extra high。

## 6. 保留的边界

受信宿主边界、Route B原合同、创建或控制FD取得前约束、双名字永久消费、owner死亡后保护和消费历史、在途效果不能当作取消、原对象不得按名换绑均保持。无义务对抗完全控制宿主的恶意root；也不能忽略正常PID1和已有管理路径。

exclusive_lifecycle_runtime_implemented=false

exclusive_lifecycle_runtime_verified=false

runtime_entry_integrated=false

global_cleanup_complete=false

next_slice_scope_ready_for_approval=false

full_implementation_scope_ready_for_approval=false

real_repository_execution_blocked=true

这些是继承的未完成状态，不是本次运行测量。本次不改项目状态文件、AGENTS、中央治理、公共契约或验收标准；正式准备源码或部署时仍读取当时的当前治理并遵守显式任务对。

## 7. 引用和交付身份

- [R1] docs/tool_system_project_state_v1.yaml，subscription_worker_public_entry_acceptance/current_disposition与subscription_worker_real_isolated_acceptance_v2_descriptive_closeout：未接受、真实仓库阻断和超时历史；本轮main读取。
- [R2] PR #234，已合并commit 75d005cee55a0e33bea17808faaba3085f740d8c；合同和synthetic交付边界，真实后端尚未验收。使用其成果，不重开四Gate审计。
- [R3] AGENTS.md §9及config/process_authority_v1.yaml：授权里程碑内自主工作；显式manifest/change-plan；不隐式取得真实执行权限。
- [R4] docs/tool_system_global_development_principles_v1.md §14，及本轮读取的finance-governance main两固定治理：有限闭环、原集合内修复、无进展停止、无隐式扩权。
- [R5] docs/reports/subscription_worker_ts_b02a_dgx_spark_linux_arm64_primary_target_and_ephemeral_kvm_isolation_path_realignment_specification_v1.md §§5–11：ARM64/KVM、信任边界、完整清理、deny_all与订阅传输分离。其封存权限不作为新的授权。
- [E1] 用户提供并在本对话核对的TERMINAL_RECEIPT.json，11326字节，SHA256 e8d0af734e5c669917370718bdd2492a2c6b646557ec40c0e4e00a9658b9a49a；INTERFACE_CONTRACTS.json，41878字节，SHA256 6de1ba6df22477845c96afe1f94b92f6bd052c2f5240605b43f54292bea217c2。外部封存报告，不是仓库源码或本轮实测。
- [E2] 用户提供并核对的MECHANISM_DECISION.md，22021字节，SHA256 ff7ae20ed0b8ae83c21bffae76942ade799bd975542f7e607ee4835b7e4b9af8：PID1/内核/MAC/owner建议，尚未冻结全部实施范围。没有重新运行源码语义审阅。

本次任务身份：ts-b02-working-loop-delivery-plan-v1。基线：75d005cee55a0e33bea17808faaba3085f740d8c / 3f3263c305b1a5d50cb7760d9bb26d37c65d095e。冻结规划任务摘要：f8619a84d491389eb29ea2f4215760b68bbee5bfd9d17aabdf75a81c575732a5。准确三条写入路径在manifest中；候选tree由本次实际提交产生，不预填。目标是一个Draft PR；不合并、不启用真实Worker、不启动后续任务。
