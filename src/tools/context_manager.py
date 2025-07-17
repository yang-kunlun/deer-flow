# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
上下文管理工具
用于在分步研究过程中管理上下文长度和生成摘要
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from src.llms.llm import get_llm_by_type
from src.prompts.planner_model import Step

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器，用于控制研究过程中的上下文长度"""
    
    def __init__(self, max_context_length: int = 30000):
        self.max_context_length = max_context_length
        self.step_summaries: List[Dict[str, Any]] = []
    
    def estimate_token_count(self, text: str) -> int:
        """估算文本的token数量（粗略估算：1 token ≈ 4 characters）"""
        return len(text) // 4
    
    def create_step_summary(self, step: Step, execution_result: str) -> Dict[str, Any]:
        """为单个步骤创建摘要"""
        # 使用LLM生成摘要
        summary_prompt = f"""
请为以下研究步骤生成一个简洁的摘要，保留关键发现和数据，控制在500字以内：

## 研究步骤
标题：{step.title}
描述：{step.description}

## 执行结果
{execution_result}

请生成摘要，格式如下：
- 关键发现：[列出3-5个最重要的发现]
- 核心数据：[列出重要的数据和数字]
- 结论：[简要结论]
- 数据来源：[主要数据来源]
"""
        
        try:
            llm = get_llm_by_type("basic")
            response = llm.invoke([HumanMessage(content=summary_prompt)])
            summary = response.content
            
            # 确保摘要长度不超过限制
            if len(summary) > 2000:
                summary = summary[:2000] + "...[摘要截断]"
            
            return {
                "step_title": step.title,
                "step_description": step.description[:200] + "..." if len(step.description) > 200 else step.description,
                "summary": summary,
                "execution_result": execution_result,
                "token_count": self.estimate_token_count(summary)
            }
        except Exception as e:
            logger.error(f"生成步骤摘要失败: {e}")
            # 如果AI总结失败，使用简单的截断
            truncated_result = execution_result[:1000] + "...[截断]" if len(execution_result) > 1000 else execution_result
            return {
                "step_title": step.title,
                "step_description": step.description[:200] + "..." if len(step.description) > 200 else step.description,
                "summary": f"关键发现：{truncated_result}",
                "execution_result": execution_result,
                "token_count": self.estimate_token_count(truncated_result)
            }
    
    def add_step_summary(self, step: Step, execution_result: str) -> Dict[str, Any]:
        """添加步骤摘要到管理器"""
        summary = self.create_step_summary(step, execution_result)
        self.step_summaries.append(summary)
        
        # 如果摘要太多，只保留最近的几个
        if len(self.step_summaries) > 5:
            self.step_summaries = self.step_summaries[-5:]
            logger.info(f"步骤摘要数量过多，只保留最近的5个")
        
        return summary
    
    def get_consolidated_context(self) -> str:
        """获取整合后的上下文信息"""
        if not self.step_summaries:
            return ""
        
        consolidated = "# 前期研究发现\n\n"
        total_tokens = 0
        
        for i, summary in enumerate(self.step_summaries, 1):
            # 检查是否会超出长度限制
            summary_text = f"## 步骤 {i}：{summary['step_title']}\n{summary['summary']}\n\n"
            
            if total_tokens + summary['token_count'] > self.max_context_length:
                consolidated += "... [更多研究发现因上下文长度限制而省略]\n\n"
                break
            
            consolidated += summary_text
            total_tokens += summary['token_count']
        
        return consolidated
    
    def create_step_context(self, current_step: Step, state: Dict[str, Any]) -> Dict[str, Any]:
        """为当前步骤创建独立的上下文"""
        # 获取整合后的前期研究发现
        previous_findings = self.get_consolidated_context()
        
        # 构建当前步骤的上下文
        current_context = f"""
{previous_findings}

# 当前研究任务

## 任务标题
{current_step.title}

## 任务描述
{current_step.description}

## 语言设置
{state.get('locale', 'zh-CN')}

## 研究要求
请基于以上前期研究发现，针对当前任务进行深入研究。注意：
1. 优先使用权威数据源（政府官网、官方统计、权威媒体）
2. 保持客观和准确，避免主观判断
3. 如果与前期发现有冲突，请注明并分析原因
4. 提供具体的数据和引用来源
"""
        
        # 检查上下文长度
        context_length = self.estimate_token_count(current_context)
        if context_length > self.max_context_length:
            logger.warning(f"步骤上下文长度 ({context_length} tokens) 超过限制，进行截断")
            # 如果太长，减少前期发现的内容
            if previous_findings:
                truncated_findings = previous_findings[:self.max_context_length//2] + "...[前期发现截断]"
                current_context = f"""
{truncated_findings}

# 当前研究任务

## 任务标题
{current_step.title}

## 任务描述
{current_step.description}

## 语言设置
{state.get('locale', 'zh-CN')}
"""
        
        return {
            "messages": [HumanMessage(content=current_context)],
            "context_length": self.estimate_token_count(current_context)
        }
    
    def should_create_summary(self, execution_result: str) -> bool:
        """判断是否需要为执行结果创建摘要"""
        return self.estimate_token_count(execution_result) > 5000
    
    def get_research_progress(self, current_plan) -> Dict[str, Any]:
        """获取研究进度信息"""
        if not current_plan or not current_plan.steps:
            return {"completed": 0, "total": 0, "percentage": 0}
        
        completed = sum(1 for step in current_plan.steps if step.execution_res)
        total = len(current_plan.steps)
        percentage = (completed / total) * 100 if total > 0 else 0
        
        return {
            "completed": completed,
            "total": total,
            "percentage": round(percentage, 1)
        }
    
    def clear_summaries(self):
        """清空所有摘要（用于新的研究任务）"""
        self.step_summaries = []
        logger.info("清空所有步骤摘要")


# 全局上下文管理器实例
context_manager = ContextManager()


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器实例"""
    return context_manager


def reset_context_manager():
    """重置上下文管理器（用于新的研究任务）"""
    global context_manager
    context_manager = ContextManager()
    logger.info("重置上下文管理器") 