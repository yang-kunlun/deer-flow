# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
Agent协作管理器
优化agent间的协作机制，包括智能任务分配、信息共享和协作策略
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from src.prompts.planner_model import Step, StepType
from src.agents.step_coordinator import get_step_coordinator
from src.tools.context_manager import get_context_manager

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent角色枚举"""
    COORDINATOR = "coordinator"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CODER = "coder"
    REPORTER = "reporter"
    AUTHORITY_SEARCHER = "authority_searcher"
    DATA_VALIDATOR = "data_validator"
    CONTEXT_MANAGER = "context_manager"


class CollaborationPattern(Enum):
    """协作模式枚举"""
    SEQUENTIAL = "sequential"     # 顺序协作
    PARALLEL = "parallel"         # 并行协作
    HIERARCHICAL = "hierarchical" # 层级协作
    PEER_TO_PEER = "peer_to_peer" # 点对点协作


@dataclass
class AgentCapability:
    """Agent能力描述"""
    agent_role: AgentRole
    specialties: List[str]        # 专业领域
    tools: List[str]             # 可用工具
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    load_factor: float = 0.0     # 负载因子
    availability: bool = True    # 可用性


@dataclass
class CollaborationRequest:
    """协作请求"""
    request_id: str
    requesting_agent: AgentRole
    target_agent: AgentRole
    task_description: str
    required_capabilities: List[str]
    priority: int = 1            # 优先级 (1-10)
    deadline: Optional[datetime] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    collaboration_pattern: CollaborationPattern = CollaborationPattern.SEQUENTIAL


@dataclass
class CollaborationResponse:
    """协作响应"""
    response_id: str
    request_id: str
    responding_agent: AgentRole
    result: Any
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCommunication:
    """Agent通信消息"""
    message_id: str
    sender: AgentRole
    receiver: AgentRole
    message_type: str           # "request", "response", "notification", "data_share"
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1


class CollaborationManager:
    """协作管理器"""
    
    def __init__(self):
        self.agents: Dict[AgentRole, AgentCapability] = {}
        self.active_requests: Dict[str, CollaborationRequest] = {}
        self.communication_history: List[AgentCommunication] = []
        self.shared_knowledge_base: Dict[str, Any] = {}
        self.collaboration_patterns: Dict[str, CollaborationPattern] = {}
        self.step_coordinator = get_step_coordinator()
        self.context_manager = get_context_manager()
        
        # 初始化Agent能力
        self._initialize_agent_capabilities()
        
        # 初始化协作模式
        self._initialize_collaboration_patterns()
    
    def _initialize_agent_capabilities(self):
        """初始化Agent能力"""
        
        # 协调器
        self.agents[AgentRole.COORDINATOR] = AgentCapability(
            agent_role=AgentRole.COORDINATOR,
            specialties=["任务分配", "流程管理", "整体协调"],
            tools=["handoff_to_planner"]
        )
        
        # 规划器
        self.agents[AgentRole.PLANNER] = AgentCapability(
            agent_role=AgentRole.PLANNER,
            specialties=["任务规划", "策略制定", "计划优化"],
            tools=["planning_tools"]
        )
        
        # 研究员
        self.agents[AgentRole.RESEARCHER] = AgentCapability(
            agent_role=AgentRole.RESEARCHER,
            specialties=["信息搜索", "数据收集", "文献调研"],
            tools=["web_search", "crawl_tool", "authority_search", "credibility_checker"]
        )
        
        # 编程员
        self.agents[AgentRole.CODER] = AgentCapability(
            agent_role=AgentRole.CODER,
            specialties=["代码分析", "数据处理", "算法实现"],
            tools=["python_repl_tool", "code_analysis_tools"]
        )
        
        # 报告员
        self.agents[AgentRole.REPORTER] = AgentCapability(
            agent_role=AgentRole.REPORTER,
            specialties=["内容生成", "报告撰写", "信息整合"],
            tools=["report_generation_tools"]
        )
        
        # 权威搜索员
        self.agents[AgentRole.AUTHORITY_SEARCHER] = AgentCapability(
            agent_role=AgentRole.AUTHORITY_SEARCHER,
            specialties=["权威数据源", "政府官网", "学术资源"],
            tools=["authority_search_tool", "credibility_checker_tool"]
        )
        
        # 数据验证员
        self.agents[AgentRole.DATA_VALIDATOR] = AgentCapability(
            agent_role=AgentRole.DATA_VALIDATOR,
            specialties=["数据验证", "质量评估", "可信度分析"],
            tools=["validate_search_results", "filter_high_quality_results"]
        )
        
        # 上下文管理员
        self.agents[AgentRole.CONTEXT_MANAGER] = AgentCapability(
            agent_role=AgentRole.CONTEXT_MANAGER,
            specialties=["上下文管理", "信息摘要", "长度控制"],
            tools=["context_management_tools"]
        )
    
    def _initialize_collaboration_patterns(self):
        """初始化协作模式"""
        
        # 研究任务的协作模式
        self.collaboration_patterns = {
            "research_task": CollaborationPattern.SEQUENTIAL,
            "data_collection": CollaborationPattern.PARALLEL,
            "quality_validation": CollaborationPattern.HIERARCHICAL,
            "context_management": CollaborationPattern.PEER_TO_PEER
        }
    
    def register_agent(self, agent_capability: AgentCapability):
        """注册Agent"""
        self.agents[agent_capability.agent_role] = agent_capability
        logger.info(f"Agent {agent_capability.agent_role.value} registered")
    
    def find_suitable_agent(self, required_capabilities: List[str], 
                           exclude_agents: Set[AgentRole] = None) -> Optional[AgentRole]:
        """寻找合适的Agent"""
        
        if exclude_agents is None:
            exclude_agents = set()
        
        best_agent = None
        best_score = 0
        
        for agent_role, capability in self.agents.items():
            if agent_role in exclude_agents or not capability.availability:
                continue
            
            # 计算匹配度
            score = self._calculate_capability_match(capability, required_capabilities)
            
            # 考虑负载因子
            score *= (1 - capability.load_factor)
            
            if score > best_score:
                best_score = score
                best_agent = agent_role
        
        return best_agent
    
    def _calculate_capability_match(self, capability: AgentCapability, 
                                  required_capabilities: List[str]) -> float:
        """计算能力匹配度"""
        
        if not required_capabilities:
            return 0.0
        
        matches = 0
        for req_cap in required_capabilities:
            req_cap_lower = req_cap.lower()
            
            # 检查专业领域匹配
            for specialty in capability.specialties:
                if req_cap_lower in specialty.lower():
                    matches += 1
                    break
            
            # 检查工具匹配
            for tool in capability.tools:
                if req_cap_lower in tool.lower():
                    matches += 0.5
                    break
        
        return matches / len(required_capabilities)
    
    def create_collaboration_request(self, requesting_agent: AgentRole,
                                   task_description: str,
                                   required_capabilities: List[str],
                                   priority: int = 1,
                                   collaboration_pattern: CollaborationPattern = None) -> str:
        """创建协作请求"""
        
        import uuid
        request_id = str(uuid.uuid4())
        
        # 寻找合适的目标Agent
        target_agent = self.find_suitable_agent(required_capabilities, {requesting_agent})
        
        if not target_agent:
            logger.warning(f"No suitable agent found for capabilities: {required_capabilities}")
            return None
        
        # 确定协作模式
        if collaboration_pattern is None:
            collaboration_pattern = self._determine_collaboration_pattern(
                task_description, required_capabilities
            )
        
        request = CollaborationRequest(
            request_id=request_id,
            requesting_agent=requesting_agent,
            target_agent=target_agent,
            task_description=task_description,
            required_capabilities=required_capabilities,
            priority=priority,
            collaboration_pattern=collaboration_pattern
        )
        
        self.active_requests[request_id] = request
        
        # 记录通信
        self._record_communication(
            requesting_agent, target_agent, "request",
            {
                "request_id": request_id,
                "task_description": task_description,
                "required_capabilities": required_capabilities
            },
            priority
        )
        
        logger.info(f"Collaboration request created: {request_id}")
        return request_id
    
    def _determine_collaboration_pattern(self, task_description: str,
                                       required_capabilities: List[str]) -> CollaborationPattern:
        """确定协作模式"""
        
        task_lower = task_description.lower()
        
        # 基于任务类型确定协作模式
        if any(keyword in task_lower for keyword in ["验证", "检查", "评估"]):
            return CollaborationPattern.HIERARCHICAL
        elif any(keyword in task_lower for keyword in ["并行", "同时", "分别"]):
            return CollaborationPattern.PARALLEL
        elif any(keyword in task_lower for keyword in ["共享", "交换", "协商"]):
            return CollaborationPattern.PEER_TO_PEER
        else:
            return CollaborationPattern.SEQUENTIAL
    
    def process_collaboration_request(self, request_id: str, 
                                    execution_result: Any) -> CollaborationResponse:
        """处理协作请求"""
        
        request = self.active_requests.get(request_id)
        if not request:
            logger.error(f"Request {request_id} not found")
            return None
        
        # 根据协作模式处理请求
        if request.collaboration_pattern == CollaborationPattern.SEQUENTIAL:
            response = self._process_sequential_collaboration(request, execution_result)
        elif request.collaboration_pattern == CollaborationPattern.PARALLEL:
            response = self._process_parallel_collaboration(request, execution_result)
        elif request.collaboration_pattern == CollaborationPattern.HIERARCHICAL:
            response = self._process_hierarchical_collaboration(request, execution_result)
        else:  # PEER_TO_PEER
            response = self._process_peer_to_peer_collaboration(request, execution_result)
        
        # 更新Agent负载
        self._update_agent_load(request.target_agent, -0.1)
        
        # 移除已完成的请求
        if request_id in self.active_requests:
            del self.active_requests[request_id]
        
        return response
    
    def _process_sequential_collaboration(self, request: CollaborationRequest, 
                                        execution_result: Any) -> CollaborationResponse:
        """处理顺序协作"""
        
        import uuid
        response_id = str(uuid.uuid4())
        
        # 顺序协作：直接返回结果
        response = CollaborationResponse(
            response_id=response_id,
            request_id=request.request_id,
            responding_agent=request.target_agent,
            result=execution_result,
            success=True,
            metadata={"collaboration_pattern": "sequential"}
        )
        
        # 记录通信
        self._record_communication(
            request.target_agent, request.requesting_agent, "response",
            {
                "response_id": response_id,
                "request_id": request.request_id,
                "result_summary": str(execution_result)[:200] + "..." if len(str(execution_result)) > 200 else str(execution_result)
            }
        )
        
        return response
    
    def _process_parallel_collaboration(self, request: CollaborationRequest, 
                                      execution_result: Any) -> CollaborationResponse:
        """处理并行协作"""
        
        import uuid
        response_id = str(uuid.uuid4())
        
        # 并行协作：可能需要等待其他并行任务完成
        response = CollaborationResponse(
            response_id=response_id,
            request_id=request.request_id,
            responding_agent=request.target_agent,
            result=execution_result,
            success=True,
            metadata={"collaboration_pattern": "parallel", "parallel_task_id": uuid.uuid4().hex}
        )
        
        return response
    
    def _process_hierarchical_collaboration(self, request: CollaborationRequest, 
                                          execution_result: Any) -> CollaborationResponse:
        """处理层级协作"""
        
        import uuid
        response_id = str(uuid.uuid4())
        
        # 层级协作：可能需要上级验证
        response = CollaborationResponse(
            response_id=response_id,
            request_id=request.request_id,
            responding_agent=request.target_agent,
            result=execution_result,
            success=True,
            metadata={"collaboration_pattern": "hierarchical", "requires_approval": True}
        )
        
        return response
    
    def _process_peer_to_peer_collaboration(self, request: CollaborationRequest, 
                                          execution_result: Any) -> CollaborationResponse:
        """处理点对点协作"""
        
        import uuid
        response_id = str(uuid.uuid4())
        
        # 点对点协作：直接交换信息
        response = CollaborationResponse(
            response_id=response_id,
            request_id=request.request_id,
            responding_agent=request.target_agent,
            result=execution_result,
            success=True,
            metadata={"collaboration_pattern": "peer_to_peer"}
        )
        
        # 在共享知识库中记录信息
        self._update_shared_knowledge(request.task_description, execution_result)
        
        return response
    
    def _record_communication(self, sender: AgentRole, receiver: AgentRole,
                            message_type: str, content: Dict[str, Any],
                            priority: int = 1):
        """记录通信"""
        
        import uuid
        communication = AgentCommunication(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        self.communication_history.append(communication)
        
        # 保持通信历史在合理范围内
        if len(self.communication_history) > 1000:
            self.communication_history = self.communication_history[-500:]
    
    def _update_agent_load(self, agent_role: AgentRole, load_change: float):
        """更新Agent负载"""
        
        if agent_role in self.agents:
            self.agents[agent_role].load_factor = max(0.0, min(1.0, 
                self.agents[agent_role].load_factor + load_change))
    
    def _update_shared_knowledge(self, topic: str, knowledge: Any):
        """更新共享知识库"""
        
        timestamp = datetime.now().isoformat()
        
        if topic not in self.shared_knowledge_base:
            self.shared_knowledge_base[topic] = []
        
        self.shared_knowledge_base[topic].append({
            "knowledge": knowledge,
            "timestamp": timestamp
        })
        
        # 保持知识库在合理范围内
        if len(self.shared_knowledge_base[topic]) > 10:
            self.shared_knowledge_base[topic] = self.shared_knowledge_base[topic][-5:]
    
    def get_shared_knowledge(self, topic: str) -> List[Dict[str, Any]]:
        """获取共享知识"""
        return self.shared_knowledge_base.get(topic, [])
    
    def optimize_agent_allocation(self, current_plan: Any) -> Dict[str, Any]:
        """优化Agent分配"""
        
        optimization_result = {
            "original_allocation": {},
            "optimized_allocation": {},
            "performance_improvement": 0.0,
            "recommendations": []
        }
        
        if not current_plan or not hasattr(current_plan, 'steps'):
            return optimization_result
        
        # 分析当前步骤需求
        step_requirements = []
        for step in current_plan.steps:
            requirements = self._analyze_step_requirements(step)
            step_requirements.append(requirements)
        
        # 为每个步骤分配最优Agent
        for i, (step, requirements) in enumerate(zip(current_plan.steps, step_requirements)):
            # 原始分配
            original_agent = self._get_default_agent_for_step(step)
            optimization_result["original_allocation"][f"step_{i}"] = original_agent.value
            
            # 优化分配
            optimized_agent = self.find_suitable_agent(requirements["capabilities"])
            if optimized_agent:
                optimization_result["optimized_allocation"][f"step_{i}"] = optimized_agent.value
                
                # 如果分配发生变化，给出建议
                if optimized_agent != original_agent:
                    optimization_result["recommendations"].append(
                        f"步骤 '{step.title}' 建议使用 {optimized_agent.value} 而不是 {original_agent.value}"
                    )
        
        return optimization_result
    
    def _analyze_step_requirements(self, step: Step) -> Dict[str, Any]:
        """分析步骤需求"""
        
        requirements = {
            "capabilities": [],
            "complexity": 1,
            "priority": 1
        }
        
        description = step.description.lower()
        
        # 基于步骤类型分析
        if step.step_type == StepType.RESEARCH:
            requirements["capabilities"].extend(["信息搜索", "数据收集", "文献调研"])
        elif step.step_type == StepType.PROCESSING:
            requirements["capabilities"].extend(["代码分析", "数据处理", "算法实现"])
        
        # 基于描述关键词分析
        if any(keyword in description for keyword in ["政府", "官方", "权威"]):
            requirements["capabilities"].append("权威数据源")
        
        if any(keyword in description for keyword in ["验证", "检查", "评估"]):
            requirements["capabilities"].append("数据验证")
        
        if any(keyword in description for keyword in ["分析", "统计", "计算"]):
            requirements["capabilities"].append("数据分析")
            requirements["complexity"] = 2
        
        return requirements
    
    def _get_default_agent_for_step(self, step: Step) -> AgentRole:
        """获取步骤的默认Agent"""
        
        if step.step_type == StepType.RESEARCH:
            return AgentRole.RESEARCHER
        elif step.step_type == StepType.PROCESSING:
            return AgentRole.CODER
        else:
            return AgentRole.RESEARCHER
    
    def get_collaboration_metrics(self) -> Dict[str, Any]:
        """获取协作指标"""
        
        metrics = {
            "active_requests": len(self.active_requests),
            "communication_count": len(self.communication_history),
            "agent_load_status": {},
            "collaboration_patterns": {},
            "performance_metrics": {}
        }
        
        # Agent负载状态
        for agent_role, capability in self.agents.items():
            metrics["agent_load_status"][agent_role.value] = {
                "load_factor": capability.load_factor,
                "availability": capability.availability
            }
        
        # 协作模式统计
        pattern_counts = {}
        for request in self.active_requests.values():
            pattern = request.collaboration_pattern.value
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        metrics["collaboration_patterns"] = pattern_counts
        
        # 通信统计
        message_type_counts = {}
        for comm in self.communication_history[-100:]:  # 最近100条通信
            msg_type = comm.message_type
            message_type_counts[msg_type] = message_type_counts.get(msg_type, 0) + 1
        metrics["communication_statistics"] = message_type_counts
        
        return metrics
    
    def generate_collaboration_report(self) -> Dict[str, Any]:
        """生成协作报告"""
        
        metrics = self.get_collaboration_metrics()
        
        report = {
            "summary": {
                "total_agents": len(self.agents),
                "active_requests": metrics["active_requests"],
                "communication_volume": metrics["communication_count"]
            },
            "agent_performance": [],
            "collaboration_efficiency": {},
            "recommendations": []
        }
        
        # Agent性能分析
        for agent_role, capability in self.agents.items():
            performance = {
                "agent": agent_role.value,
                "specialties": capability.specialties,
                "load_factor": capability.load_factor,
                "availability": capability.availability,
                "tools_count": len(capability.tools)
            }
            report["agent_performance"].append(performance)
        
        # 协作效率分析
        avg_load = sum(cap.load_factor for cap in self.agents.values()) / len(self.agents)
        report["collaboration_efficiency"] = {
            "average_load": avg_load,
            "load_balance": 1.0 - (max(cap.load_factor for cap in self.agents.values()) - 
                                  min(cap.load_factor for cap in self.agents.values())),
            "active_patterns": len(metrics["collaboration_patterns"])
        }
        
        # 生成建议
        if avg_load > 0.7:
            report["recommendations"].append("整体Agent负载较高，建议增加Agent数量或优化任务分配")
        
        if report["collaboration_efficiency"]["load_balance"] < 0.5:
            report["recommendations"].append("Agent负载不均衡，建议重新分配任务")
        
        return report


# 创建全局协作管理器实例
collaboration_manager = CollaborationManager()


@tool
def create_collaboration_request(requesting_agent: str, task_description: str,
                               required_capabilities: List[str], priority: int = 1) -> str:
    """
    创建协作请求
    
    Args:
        requesting_agent: 请求Agent
        task_description: 任务描述
        required_capabilities: 需要的能力
        priority: 优先级
    
    Returns:
        请求ID
    """
    agent_role = AgentRole(requesting_agent)
    return collaboration_manager.create_collaboration_request(
        agent_role, task_description, required_capabilities, priority
    )


@tool
def find_suitable_agent(required_capabilities: List[str]) -> Optional[str]:
    """
    寻找合适的Agent
    
    Args:
        required_capabilities: 需要的能力
    
    Returns:
        合适的Agent角色
    """
    agent_role = collaboration_manager.find_suitable_agent(required_capabilities)
    return agent_role.value if agent_role else None


@tool
def get_collaboration_metrics() -> Dict[str, Any]:
    """
    获取协作指标
    
    Returns:
        协作指标
    """
    return collaboration_manager.get_collaboration_metrics()


@tool
def optimize_agent_allocation(current_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    优化Agent分配
    
    Args:
        current_plan: 当前计划
    
    Returns:
        优化结果
    """
    return collaboration_manager.optimize_agent_allocation(current_plan)


@tool
def generate_collaboration_report() -> Dict[str, Any]:
    """
    生成协作报告
    
    Returns:
        协作报告
    """
    return collaboration_manager.generate_collaboration_report()


def get_collaboration_manager() -> CollaborationManager:
    """获取协作管理器实例"""
    return collaboration_manager 