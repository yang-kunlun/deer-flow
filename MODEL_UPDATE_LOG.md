# 模型更新日志 - Claude Sonnet 4

## 更新概述
将DeerFlow项目的默认模型从Claude 3.5 Sonnet更新为最新的Claude Sonnet 4模型。

## 更新时间
2025年1月15日

## 修改内容

### 1. 后端配置 (conf.yaml)
- **文件**: `conf.yaml`
- **修改**: 将 `BASIC_MODEL.model` 从 `"anthropic/claude-3.5-sonnet:beta"` 更新为 `"anthropic/claude-sonnet-4"`

### 2. 前端默认设置 (settings-store.ts)
- **文件**: `web/src/core/store/settings-store.ts`
- **修改**: 将 `DEFAULT_SETTINGS.general.selectedModel` 从 `"claude-3.5-sonnet"` 更新为 `"claude-sonnet-4"`

### 3. 模型选择器组件 (model-selector.tsx)
- **文件**: `web/src/components/deer-flow/model-selector.tsx`
- **修改内容**:
  - 将 `DEFAULT_MODELS` 中的第一个模型更新：
    - `id`: `"claude-3.5-sonnet"` → `"claude-sonnet-4"`
    - `name`: `"Claude 3.5 Sonnet"` → `"Claude Sonnet 4"`
    - `description`: `"Advanced reasoning and analysis"` → `"Latest Claude model with enhanced reasoning"`
  - 将组件默认props中的 `selectedModel` 从 `"claude-3.5-sonnet"` 更新为 `"claude-sonnet-4"`

## Claude Sonnet 4 特性
根据OpenRouter官方信息，Claude Sonnet 4具有以下增强功能：
- 在SWE-bench测试中达到72.7%的成绩
- 在编程和推理任务中显著提升性能
- 更好的代码库导航能力
- 降低了代理驱动工作流程中的错误率
- 提高了遵循复杂指令的可靠性
- 优化了日常使用的实用性，保持高效和响应性

## 技术细节
- **模型提供商**: OpenRouter
- **模型ID**: `anthropic/claude-sonnet-4`
- **上下文长度**: 200,000 tokens
- **定价**: $3/M input tokens, $15/M output tokens
- **多模态支持**: 支持图像处理

## 验证步骤
1. 更新后端配置文件
2. 更新前端默认设置
3. 更新模型选择器界面
4. 验证前端应用正常启动
5. 确认模型选择器显示正确的模型选项

## 注意事项
- 需要重启后端服务器以使配置生效
- 前端会自动热重载更新
- 现有用户的本地存储设置可能仍会保留旧模型选择，但新用户会默认使用Claude Sonnet 4
- 所有API调用将使用新的Claude Sonnet 4模型 