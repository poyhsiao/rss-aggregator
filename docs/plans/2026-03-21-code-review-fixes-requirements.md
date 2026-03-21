# Code Review Fixes Requirements

**Date**: 2026-03-21
**Author**: Code Review Agent
**Status**: Approved

## Background

代码审查发现 14 个问题，需要按优先级分批修复。

## Goals

1. 消除安全隐患（CORS、XSS）
2. 改善代码质量（异常处理、类型安全）
3. 提升代码可维护性（组件拆分、配置优化）

## Non-Goals

- 不重构整体架构
- 不添加新功能
- 不修改现有 API 接口

## Requirements

### Batch 1: Security (High Priority)

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| S1 | CORS 配置支持环境变量控制允许来源 | High | 防止任意网站跨域请求 |
| S2 | 前端 HTML 渲染必须经过净化 | High | 防止 XSS 攻击 |

### Batch 2: Medium Priority

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| M1 | API Key 使用 sessionStorage 存储 | Medium | 缩短会话生命周期 |
| M2 | Debug 模式默认关闭 | Medium | 避免生产环境泄露信息 |
| M3 | Docker 容器使用非 root 用户运行 | Medium | 容器安全最佳实践 |
| M4 | 异常处理使用具体类型 | Medium | 便于调试和错误追踪 |
| M5 | feedparser 返回值添加类型守卫 | Medium | 防止类型错误 |

### Batch 3: Low Priority

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| L1 | 移除生产代码中的 console 语句 | Low | 避免信息泄露 |
| L2 | TypeScript 使用具体类型替代 any | Low | 类型安全 |
| L3 | RssPreviewDialog.vue 拆分为多个组件 | Low | 可维护性 |
| L4 | 404 处理器返回 JSON 响应 | Low | API 一致性 |
| L5 | 修复 source_id 参数不匹配问题 | Low | 类型正确性 |
| L6 | 添加 future annotations 解决循环导入 | Low | 类型检查通过 |
| L7 | 配置 Tailwind CSS LSP（可选） | Low | 开发体验 |

## Acceptance Criteria

### Batch 1

- [ ] `ALLOWED_ORIGINS` 环境变量生效
- [ ] DOMPurify 正确净化 HTML 内容
- [ ] 所有测试通过
- [ ] 无新增 LSP 错误

### Batch 2

- [ ] sessionStorage 正常工作
- [ ] Docker 容器以 appuser 运行
- [ ] 异常处理覆盖具体错误类型
- [ ] feedparser 类型守卫通过 LSP 检查

### Batch 3

- [ ] 组件拆分后功能正常
- [ ] 404 返回 JSON 格式
- [ ] 所有 LSP 错误消除（除 Tailwind 配置）

## Constraints

- 不破坏现有功能
- 每批独立可合并/回滚
- 遵循现有代码风格

## Dependencies

### Batch 1
- 无新增后端依赖
- 前端新增：`dompurify`, `@types/dompurify`

### Batch 2
- 无新增依赖

### Batch 3
- 无新增依赖

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| 组件拆分引入回归 bug | Medium | High | 充分测试，保持原有测试覆盖 |
| CORS 配置变更影响现有用户 | Low | Medium | 文档说明，默认保持 "*" 兼容 |
| sessionStorage 影响用户体验 | Low | Low | 会话结束后需重新登录是合理行为 |

## Timeline

| Batch | Estimated Time | Dependencies |
|-------|---------------|--------------|
| Batch 1 | 2-3 hours | None |
| Batch 2 | 3-4 hours | Batch 1 |
| Batch 3 | 4-5 hours | Batch 2 |