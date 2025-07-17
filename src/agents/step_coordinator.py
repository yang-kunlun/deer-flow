# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
步骤协调Agent
负责管理各个研究步骤的执行顺序和依赖关系
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from langchain_core.tools import tool
from src.prompts.planner_model import Step
from src.tools.context_manager import get_context_manager

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"           # 待执行
    READY = "ready"               # 准备就绪
    IN_PROGRESS = "in_progress"   # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 执行失败
    SKIPPED = "skipped"           # 已跳过


@dataclass
class StepDependency:
    """步骤依赖关系"""
    step_id: str                  # 步骤ID
    dependency_id: str            # 依赖步骤ID
    dependency_type: str          # 依赖类型: "prerequisite", "parallel", "optional"
    description: str              # 依赖描述


@dataclass
class StepExecution:
    """步骤执行信息"""
    step_id: str                  # 步骤ID
    status: StepStatus            # 执行状态
    start_time: Optional[float] = None     # 开始时间
    end_time: Optional[float] = None       # 结束时间
    execution_result: Optional[str] = None # 执行结果
    error_message: Optional[str] = None    # 错误信息
    retry_count: int = 0                   # 重试次数
    context_summary: Optional[str] = None  # 上下文摘要


class StepCoordinator:
    """步骤协调器"""
    
    def __init__(self):
        self.context_manager = get_context_manager()
        self.step_executions: Dict[str, StepExecution] = {}
        self.dependencies: List[StepDependency] = []
        self.execution_order: List[str] = []
        self.max_retries = 3
        self.parallel_execution_limit = 2
    
    def initialize_plan(self, steps: List[Step]) -> Dict[str, Any]:
        """初始化研究计划"""
        logger.info(f"初始化研究计划，共 {len(steps)} 个步骤")
        
        # 清空之前的状态
        self.step_executions.clear()
        self.dependencies.clear()
        self.execution_order.clear()
        
        # 为每个步骤创建执行记录
        for step in steps:
            step_id = step.title  # 使用步骤标题作为ID
            self.step_executions[step_id] = StepExecution(
                step_id=step_id,
                status=StepStatus.PENDING
            )
        
        # 分析步骤依赖关系
        self._analyze_dependencies(steps)
        
        # 生成执行顺序
        self._generate_execution_order()
        
        return {
            "total_steps": len(steps),
            "execution_order": self.execution_order,
            "dependencies": [
                {
                    "step": dep.step_id,
                    "depends_on": dep.dependency_id,
                    "type": dep.dependency_type,
                    "description": dep.description
                }
                for dep in self.dependencies
            ]
        }
    
    def _analyze_dependencies(self, steps: List[Step]):
        """分析步骤依赖关系"""
        
        # 基于步骤内容和类型分析依赖关系
        for i, step in enumerate(steps):
            step_id = step.title
            
            # 检查是否需要依赖前面的步骤
            for j in range(i):
                prev_step = steps[j]
                prev_step_id = prev_step.title
                
                # 检查内容相关性
                if self._has_content_dependency(step, prev_step):
                    self.dependencies.append(StepDependency(
                        step_id=step_id,
                        dependency_id=prev_step_id,
                        dependency_type="prerequisite",
                        description=f"{step_id} 需要 {prev_step_id} 的结果作为基础"
                    ))
                
                # 检查数据依赖
                if self._has_data_dependency(step, prev_step):
                    self.dependencies.append(StepDependency(
                        step_id=step_id,
                        dependency_id=prev_step_id,
                        dependency_type="prerequisite",
                        description=f"{step_id} 需要 {prev_step_id} 提供的数据"
                    ))
            
            # 检查是否可以并行执行
            for j in range(i + 1, len(steps)):
                next_step = steps[j]
                next_step_id = next_step.title
                
                if self._can_parallel_execution(step, next_step):
                    self.dependencies.append(StepDependency(
                        step_id=step_id,
                        dependency_id=next_step_id,
                        dependency_type="parallel",
                        description=f"{step_id} 和 {next_step_id} 可以并行执行"
                    ))
    
    def _has_content_dependency(self, step: Step, prev_step: Step) -> bool:
        """检查内容依赖关系"""
        
        # 检查步骤描述中是否包含相关关键词
        step_desc = step.description.lower()
        prev_desc = prev_step.description.lower()
        
        # 基于关键词的依赖分析
        dependency_keywords = [
            "基于", "根据", "结合", "综合", "分析", "总结",
            "依据", "参考", "利用", "使用", "采用"
        ]
        
        for keyword in dependency_keywords:
            if keyword in step_desc:
                # 检查是否引用了前面步骤的内容
                if any(word in prev_desc for word in ["数据", "信息", "研究", "调查", "分析"]):
                    return True
        
        return False
    
    def _has_data_dependency(self, step: Step, prev_step: Step) -> bool:
        """检查数据依赖关系"""
        
        # 检查步骤类型和内容
        step_desc = step.description.lower()
        prev_desc = prev_step.description.lower()
        
        # 数据依赖模式
        data_patterns = [
            ("统计", "数据"),
            ("分析", "收集"),
            ("对比", "统计"),
            ("趋势", "历史"),
            ("预测", "分析"),
            ("评估", "调查")
        ]
        
        for current_pattern, prev_pattern in data_patterns:
            if current_pattern in step_desc and prev_pattern in prev_desc:
                return True
        
        return False
    
    def _can_parallel_execution(self, step1: Step, step2: Step) -> bool:
        """检查是否可以并行执行"""
        
        # 检查步骤内容是否独立
        desc1 = step1.description.lower()
        desc2 = step2.description.lower()
        
        # 独立研究的关键词
        independent_keywords = [
            "独立", "单独", "分别", "各自", "同时", "并行"
        ]
        
        # 如果两个步骤都包含独立性关键词，可以并行
        if any(keyword in desc1 for keyword in independent_keywords) and \
           any(keyword in desc2 for keyword in independent_keywords):
            return True
        
        # 检查研究领域是否不同
        if not self._has_overlapping_domain(step1, step2):
            return True
        
        return False
    
    def _has_overlapping_domain(self, step1: Step, step2: Step) -> bool:
        """检查步骤是否有重叠的研究领域"""
        
        # 提取关键词
        keywords1 = set(step1.description.lower().split())
        keywords2 = set(step2.description.lower().split())
        
        # 计算重叠度
        overlap = keywords1 & keywords2
        overlap_ratio = len(overlap) / min(len(keywords1), len(keywords2))
        
        # 如果重叠度超过30%，认为有重叠
        return overlap_ratio > 0.3
    
    def _generate_execution_order(self):
        """生成执行顺序"""
        
        # 使用拓扑排序生成执行顺序
        in_degree = {}
        graph = {}
        
        # 初始化
        for step_id in self.step_executions.keys():
            in_degree[step_id] = 0
            graph[step_id] = []
        
        # 构建图
        for dep in self.dependencies:
            if dep.dependency_type == "prerequisite":
                graph[dep.dependency_id].append(dep.step_id)
                in_degree[dep.step_id] += 1
        
        # 拓扑排序
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        
        while queue:
            current = queue.pop(0)
            self.execution_order.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
    
    def get_next_ready_steps(self) -> List[str]:
        """获取下一个准备就绪的步骤"""
        ready_steps = []
        
        for step_id in self.execution_order:
            execution = self.step_executions[step_id]
            
            if execution.status == StepStatus.PENDING:
                # 检查依赖是否满足
                if self._are_dependencies_satisfied(step_id):
                    execution.status = StepStatus.READY
                    ready_steps.append(step_id)
                    
                    # 限制并行执行数量
                    if len(ready_steps) >= self.parallel_execution_limit:
                        break
        
        return ready_steps
    
    def _are_dependencies_satisfied(self, step_id: str) -> bool:
        """检查步骤依赖是否满足"""
        
        for dep in self.dependencies:
            if dep.step_id == step_id and dep.dependency_type == "prerequisite":
                dependency_execution = self.step_executions.get(dep.dependency_id)
                if not dependency_execution or dependency_execution.status != StepStatus.COMPLETED:
                    return False
        
        return True
    
    def start_step_execution(self, step_id: str) -> bool:
        """开始步骤执行"""
        
        execution = self.step_executions.get(step_id)
        if not execution:
            logger.error(f"步骤 {step_id} 不存在")
            return False
        
        if execution.status != StepStatus.READY:
            logger.error(f"步骤 {step_id} 状态不是准备就绪: {execution.status}")
            return False
        
        import time
        execution.status = StepStatus.IN_PROGRESS
        execution.start_time = time.time()
        
        logger.info(f"开始执行步骤: {step_id}")
        return True
    
    def complete_step_execution(self, step_id: str, result: str) -> bool:
        """完成步骤执行"""
        
        execution = self.step_executions.get(step_id)
        if not execution:
            logger.error(f"步骤 {step_id} 不存在")
            return False
        
        if execution.status != StepStatus.IN_PROGRESS:
            logger.error(f"步骤 {step_id} 状态不是执行中: {execution.status}")
            return False
        
        import time
        execution.status = StepStatus.COMPLETED
        execution.end_time = time.time()
        execution.execution_result = result
        
        # 生成上下文摘要
        execution.context_summary = self.context_manager.create_step_summary(
            step_id, result
        )
        
        logger.info(f"完成执行步骤: {step_id}")
        return True
    
    def fail_step_execution(self, step_id: str, error: str) -> bool:
        """步骤执行失败"""
        
        execution = self.step_executions.get(step_id)
        if not execution:
            logger.error(f"步骤 {step_id} 不存在")
            return False
        
        execution.retry_count += 1
        execution.error_message = error
        
        if execution.retry_count < self.max_retries:
            execution.status = StepStatus.READY
            logger.warning(f"步骤 {step_id} 执行失败，准备重试 ({execution.retry_count}/{self.max_retries})")
            return True
        else:
            execution.status = StepStatus.FAILED
            logger.error(f"步骤 {step_id} 执行失败，已达到最大重试次数")
            return False
    
    def get_execution_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        
        status_counts = {}
        for execution in self.step_executions.values():
            status = execution.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_steps = len(self.step_executions)
        completed_steps = status_counts.get("completed", 0)
        failed_steps = status_counts.get("failed", 0)
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "status_distribution": status_counts,
            "current_step": self._get_current_step(),
            "next_steps": self.get_next_ready_steps()
        }
    
    def _get_current_step(self) -> Optional[str]:
        """获取当前正在执行的步骤"""
        
        for execution in self.step_executions.values():
            if execution.status == StepStatus.IN_PROGRESS:
                return execution.step_id
        
        return None
    
    def get_step_summary(self, step_id: str) -> Optional[str]:
        """获取步骤摘要"""
        
        execution = self.step_executions.get(step_id)
        if execution and execution.context_summary:
            return execution.context_summary
        
        return None
    
    def is_plan_completed(self) -> bool:
        """检查计划是否完成"""
        
        for execution in self.step_executions.values():
            if execution.status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
                return False
        
        return True
    
    def get_execution_report(self) -> Dict[str, Any]:
        """生成执行报告"""
        
        report = {
            "execution_summary": self.get_execution_progress(),
            "step_details": [],
            "dependencies": [
                {
                    "step": dep.step_id,
                    "depends_on": dep.dependency_id,
                    "type": dep.dependency_type,
                    "description": dep.description
                }
                for dep in self.dependencies
            ],
            "execution_order": self.execution_order,
            "performance_metrics": self._calculate_performance_metrics()
        }
        
        # 添加步骤详情
        for step_id, execution in self.step_executions.items():
            step_detail = {
                "step_id": step_id,
                "status": execution.status.value,
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "execution_time": (execution.end_time - execution.start_time) if execution.start_time and execution.end_time else None,
                "retry_count": execution.retry_count,
                "error_message": execution.error_message,
                "has_summary": execution.context_summary is not None
            }
            report["step_details"].append(step_detail)
        
        return report
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """计算性能指标"""
        
        total_time = 0
        successful_steps = 0
        failed_steps = 0
        
        for execution in self.step_executions.values():
            if execution.start_time and execution.end_time:
                total_time += (execution.end_time - execution.start_time)
            
            if execution.status == StepStatus.COMPLETED:
                successful_steps += 1
            elif execution.status == StepStatus.FAILED:
                failed_steps += 1
        
        total_steps = len(self.step_executions)
        
        return {
            "total_execution_time": total_time,
            "average_step_time": total_time / total_steps if total_steps > 0 else 0,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0,
            "failure_rate": failed_steps / total_steps if total_steps > 0 else 0,
            "total_retries": sum(execution.retry_count for execution in self.step_executions.values())
        }


# 创建全局步骤协调器实例
step_coordinator = StepCoordinator()


@tool
def initialize_research_plan(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    初始化研究计划
    
    Args:
        steps: 研究步骤列表
    
    Returns:
        初始化结果
    """
    logger.info("初始化研究计划")
    
    # 转换为Step对象
    step_objects = []
    for step_data in steps:
        step = Step(
            title=step_data["title"],
            description=step_data["description"],
            step_type=step_data.get("step_type", "research"),
            need_search=step_data.get("need_search", True)
        )
        step_objects.append(step)
    
    result = step_coordinator.initialize_plan(step_objects)
    
    return result


@tool
def get_next_ready_steps() -> List[str]:
    """
    获取下一个准备就绪的步骤
    
    Returns:
        准备就绪的步骤列表
    """
    return step_coordinator.get_next_ready_steps()


@tool
def start_step_execution(step_id: str) -> bool:
    """
    开始步骤执行
    
    Args:
        step_id: 步骤ID
    
    Returns:
        是否成功开始执行
    """
    return step_coordinator.start_step_execution(step_id)


@tool
def complete_step_execution(step_id: str, result: str) -> bool:
    """
    完成步骤执行
    
    Args:
        step_id: 步骤ID
        result: 执行结果
    
    Returns:
        是否成功完成
    """
    return step_coordinator.complete_step_execution(step_id, result)


@tool
def get_execution_progress() -> Dict[str, Any]:
    """
    获取执行进度
    
    Returns:
        执行进度信息
    """
    return step_coordinator.get_execution_progress()


@tool
def get_execution_report() -> Dict[str, Any]:
    """
    生成执行报告
    
    Returns:
        执行报告
    """
    return step_coordinator.get_execution_report()


def get_step_coordinator() -> StepCoordinator:
    """获取步骤协调器实例"""
    return step_coordinator 