# 上下文长度优化方案

## 问题背景

DeerFlow项目在使用Claude API进行深度研究时，频繁遇到上下文长度超出限制的问题：

### 具体错误情况
- **主要错误**: `prompt is too long: 213317 tokens > 200000 maximum`
- **次要错误**: `input length and max_tokens exceed context limit: 156550 + 64000 > 200000`
- **表现**: 研究工作流程在researcher节点卡住，前端显示"TypeError: network error"和JSON解析错误

### 上下文内容爆炸原因分析

通过详细分析发现，上下文长度超限的主要原因是 **Tavily搜索返回的内容过于庞大且未经过滤**：

#### 1. Tavily搜索内容分析
- **单个搜索结果**: 平均约600-2000 tokens
- **默认返回数量**: 3个结果
- **单次搜索总计**: 约1800-6000 tokens
- **多次搜索累积**: 在一个研究任务中可能进行5-10次搜索

#### 2. 内容组成分析
基于对实际日志的分析，发现以下内容占比：

| 内容类型 | 占比 | 问题描述 |
|---------|------|---------|
| 图片相关内容 | 31.8% | 包含"Image 8"等图片标签、图片描述文本 |
| 普通文本内容 | 66.2% | 搜索结果的主要文本内容 |
| Raw内容 | 可变 | 原始HTML内容，未经清理 |
| 图片URL和描述 | 额外 | 图片链接和自动生成的描述 |

#### 3. 问题根源
- **配置问题**: 在`src/tools/search.py`中设置了：
  ```python
  include_raw_content=True,
  include_images=True,
  include_image_descriptions=True,
  ```
- **无长度限制**: 与`crawl_tool`的1000字符限制不同，tavily搜索结果没有内容长度限制
- **无内容过滤**: 包含大量无关内容如图片标签、乱码、重复文本
- **累积效应**: 多次搜索结果在上下文中累积，快速消耗token额度

#### 4. 具体示例
从日志中观察到的单个搜索结果：
```json
{
  "content": "作为全球性能最强的AI，ChatGPT已遇到算力等方面的瓶颈...(大量文本)...Image 8\n\n全模拟光电智能计算芯片效果图。经长期联合攻关，清华大学研究团队突破传统芯片的物理瓶颈...(继续大量文本)"
}
```

可以看到：
- 单个`content`字段包含数千字符
- 包含图片相关的无用标签如"Image 8"
- 文本内容没有经过清理和过滤
- 存在大量与搜索主题无关的内容

## 主要修改方案

### 1. **禁用图片搜索功能** (已完成)
**目标**: 消除图片内容对上下文长度的影响

```python
# src/tools/search.py - 已修改
return LoggedTavilySearch(
    name="web_search",
    max_results=max_search_results,
    include_raw_content=False,    # 禁用原始内容
    include_images=False,         # 禁用图片
    include_image_descriptions=False,  # 禁用图片描述
)
```

**效果**:
- ✅ 减少单次搜索的token消耗约30-50%
- ✅ 移除无关的图片和乱码内容
- ✅ 保持搜索结果的核心信息
- ✅ 已实施并验证有效

### 2. **分步研究机制** (已完成)
**目标**: 将研究计划分步执行，避免上下文累积

```python
# src/tools/context_manager.py - 新增
class ContextManager:
    def create_step_summary(self, step, execution_result):
        """为单个步骤创建摘要"""
        # 使用LLM生成摘要，控制在500字以内
        
    def create_step_context(self, current_step, state):
        """为当前步骤创建独立的上下文"""
        # 基于前期步骤摘要构建上下文
```

**效果**:
- ✅ 每个步骤独立处理，避免上下文累积
- ✅ 通过摘要机制保持研究连贯性
- ✅ 大幅减少上下文长度
- ✅ 已实施并集成到工作流中

### 3. **权威数据源优先机制** (已完成)
**目标**: 优先使用政府、权威媒体等可靠数据源

```python
# src/tools/authority_search.py - 新增
class AuthoritySourceManager:
    def __init__(self):
        self.authority_domains = {
            "government": [".gov.cn", ".gov", "stats.gov.cn", ...],
            "international": ["who.int", "un.org", "worldbank.org", ...],
            "media": ["xinhua.net", "people.com.cn", "reuters.com", ...],
            ...
        }
```

**效果**:
- ✅ 提高数据源的权威性和可信度
- ✅ 减少需要验证的信息量
- ✅ 优化搜索结果质量
- ✅ 已集成到researcher agent中

### 4. **上下文管理优化** (已完成)
**目标**: 智能管理上下文长度，防止溢出

```python
# src/graph/nodes.py - 已修改
async def _execute_agent_step(state, agent, agent_name):
    # 使用上下文管理器创建步骤上下文
    context_manager = get_context_manager()
    step_context = context_manager.create_step_context(current_step, state)
    
    # 为完成的步骤创建摘要
    step_summary = context_manager.add_step_summary(current_step, response_content)
```

**效果**:
- ✅ 防止历史信息过度累积
- ✅ 保持最新的上下文信息
- ✅ 通过摘要保持研究连贯性
- ✅ 已实施并验证有效

### 5. **LangGraph Studio可视化调研** (已完成)
**目标**: 了解LangGraph Studio的可视化和编辑功能

**发现**:
- LangGraph Studio提供实时工作流可视化
- 支持drag-and-drop式的工作流编辑
- 可以实时监控agent执行状态
- 支持断点调试和状态检查
- 通过langgraph.json配置文件定义工作流

**实施建议**:
- 当前已支持LangGraph Studio可视化
- 可通过`langgraph dev`命令启动
- 未来可考虑扩展自定义可视化界面

### 6. **前端JSON解析优化** (已完成)
**目标**: 提高前端对不完整JSON的处理能力

```javascript
// web/src/core/utils/json.ts - 已优化
export function parseJSON(jsonString: string): any {
  try {
    return JSON.parse(jsonString);
  } catch (error) {
    return parsePartialJSON(jsonString);
  }
}
```

**效果**:
- ✅ 提高了前端稳定性
- ✅ 减少了JSON解析错误
- ✅ 提供更好的用户体验

## 性能评估

### 优化效果对比

| 方案 | Token减少量 | 稳定性提升 | 信息损失风险 | 实现复杂度 |
|------|------------|------------|-------------|------------|
| Token配置优化 | 中等 | 高 | 低 | 低 |
| 上下文管理优化 | 中等 | 中等 | 中等 | 中等 |
| **Tavily搜索优化** | **高** | **高** | **低** | **中等** |
| 多级上下文检查 | 高 | 高 | 中等 | 高 |
| 观察结果管理 | 低 | 中等 | 低 | 低 |
| 前端JSON解析 | 无 | 中等 | 无 | 低 |

### 实际性能数据

通过分析脚本(`analyze_context_content.py`)的测试结果：

- **单个搜索结果**: ~600 tokens
- **图片内容占比**: 31.8%
- **有效文本占比**: 66.2%
- **预期优化效果**: 禁用图片内容可减少约30%的token消耗

### 核心建议

**立即实施**:
1. **禁用Tavily搜索的图片相关功能**
2. **添加搜索结果内容长度限制**
3. **实施内容清理和过滤**

**后续优化**:
1. 智能内容截断算法
2. 内容相关性评分
3. 上下文压缩技术

## 未来优化方向

### 短期优化 (1-2周)
1. **智能内容截断**: 基于内容相关性进行智能截断
2. **上下文压缩**: 使用摘要技术压缩历史信息
3. **搜索结果去重**: 移除重复或相似的搜索结果

### 长期优化 (1-3个月)
1. **向量化存储**: 使用向量数据库存储搜索结果
2. **分层处理**: 根据研究深度动态调整上下文长度
3. **模型升级**: 迁移到更大上下文窗口的模型

### 监控策略

#### 关键指标
- **上下文使用率**: 目标 < 80%
- **搜索结果长度**: 目标 < 1000 tokens/结果
- **研究任务成功率**: 目标 > 95%

#### 告警阈值
- **警告**: 上下文使用率 > 70%
- **错误**: 上下文使用率 > 90%
- **紧急**: 出现上下文溢出错误

#### 配置参数
```yaml
# 建议的配置参数
context_management:
  max_search_results: 3
  max_content_length: 1000
  max_historical_steps: 2
  max_observations: 3
  enable_content_filtering: true
  enable_image_content: false
```

## 总结

上下文长度超限的核心问题是 **Tavily搜索返回的内容过于庞大且未经过滤**。通过禁用图片相关功能、添加内容长度限制和实施内容清理，可以显著减少token消耗并提高系统稳定性。

**关键数据**:
- 图片相关内容占搜索结果的31.8%
- 单次搜索可能消耗1800-6000 tokens
- 多次搜索累积是导致上下文爆炸的主要原因

**立即行动**:
1. 修改Tavily搜索配置，禁用图片相关功能
2. 添加搜索结果内容长度限制（建议1000字符）
3. 实施内容清理，移除图片标签和乱码

通过这些优化，预计可以减少50-70%的搜索相关token消耗，从根本上解决上下文长度超限问题。 