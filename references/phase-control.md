# 运行模式控制

## `baseline`

`baseline` 是 Meta-model-agent 的默认模式，用于建立可重复、可追踪的研究基准链。

基准模式务必满足：

- 阶段次序保持固定；
- 核验点类别保持稳定；
- 交付物及伴随文件严禁缩减；
- 文件规模与质量门槛严禁降低；
- 阶段协议中的硬性约束严禁省略。

## `enhancement`

只有七个基准阶段全部形成有效完成证据后，才可转入 `enhancement`。

增强模式可用于强化角色调度、门禁强度、证据审计、异常恢复和自动化校验，并通过 `rework -> begin -> validate -> gate_check` 对指定阶段实施受控返工。

增强模式严禁改变研究职责、移除既定交付物、绕过基准证据，或另建一条缺少上游依据的替代链路。

## 模式转换

```bash
python scripts/pipeline_manager.py set-phase enhancement --workspace .
```

若基准尚未闭合，命令会拒绝转换；`--force` 仅用于清晰标明授权的诊断场景。转换后先运行：

```bash
python scripts/enhancement_audit.py --workspace .
```

