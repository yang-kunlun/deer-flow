# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
数据质量评分机制
为搜索结果提供综合的质量评分和排序
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from langchain_core.tools import tool
from src.config.authority_database import get_authority_database
from src.tools.data_validator import data_validator

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """质量评分结果"""
    overall_score: float                # 总体评分 (0-10)
    credibility_score: float           # 可信度评分 (0-10)
    content_quality_score: float       # 内容质量评分 (0-10)
    timeliness_score: float           # 时效性评分 (0-10)
    completeness_score: float         # 完整性评分 (0-10)
    authority_bonus: float             # 权威性加分 (0-2)
    quality_level: str                 # 质量等级
    confidence_level: str              # 置信度等级
    recommendations: List[str]         # 使用建议
    detailed_analysis: Dict[str, Any]  # 详细分析


class QualityScorer:
    """数据质量评分器"""
    
    def __init__(self):
        self.authority_db = get_authority_database()
        self.data_validator = data_validator
        
        # 评分权重配置
        self.scoring_weights = {
            "credibility": 0.35,        # 可信度权重
            "content_quality": 0.25,    # 内容质量权重
            "timeliness": 0.20,         # 时效性权重
            "completeness": 0.15,       # 完整性权重
            "authority_bonus": 0.05     # 权威性加分权重
        }
    
    def score_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为搜索结果列表评分"""
        scored_results = []
        
        for result in search_results:
            quality_score = self._calculate_quality_score(result)
            
            # 添加评分信息到结果中
            scored_result = {
                **result,
                "quality_score": quality_score
            }
            scored_results.append(scored_result)
        
        # 按评分排序
        scored_results.sort(key=lambda x: x["quality_score"].overall_score, reverse=True)
        
        return scored_results
    
    def _calculate_quality_score(self, search_result: Dict[str, Any]) -> QualityScore:
        """计算单个搜索结果的质量评分"""
        
        # 1. 使用数据验证器获取基础评分
        validation_result = self.data_validator.validate_search_result(search_result)
        validation_data = validation_result["validation_result"]
        
        # 2. 获取权威性信息
        url = search_result.get("url", "")
        authority_source = self.authority_db.get_source_by_url(url)
        
        # 3. 计算各项评分
        credibility_score = validation_data["credibility"]["score"]
        content_quality_score = validation_data["content_quality"]["score"]
        timeliness_score = validation_data["timeliness"]["score"]
        completeness_score = validation_data["completeness"]["score"]
        
        # 4. 计算权威性加分
        authority_bonus = self._calculate_authority_bonus(authority_source)
        
        # 5. 计算总体评分
        overall_score = (
            credibility_score * self.scoring_weights["credibility"] +
            content_quality_score * self.scoring_weights["content_quality"] +
            timeliness_score * self.scoring_weights["timeliness"] +
            completeness_score * self.scoring_weights["completeness"] +
            authority_bonus * self.scoring_weights["authority_bonus"]
        )
        
        # 6. 确保评分在合理范围内
        overall_score = min(10.0, max(0.0, overall_score))
        
        # 7. 确定质量等级和置信度
        quality_level = self._get_quality_level(overall_score)
        confidence_level = self._get_confidence_level(overall_score, authority_source)
        
        # 8. 生成使用建议
        recommendations = self._generate_recommendations(
            overall_score, authority_source, validation_data
        )
        
        # 9. 生成详细分析
        detailed_analysis = self._generate_detailed_analysis(
            validation_data, authority_source, overall_score
        )
        
        return QualityScore(
            overall_score=round(overall_score, 2),
            credibility_score=credibility_score,
            content_quality_score=content_quality_score,
            timeliness_score=timeliness_score,
            completeness_score=completeness_score,
            authority_bonus=authority_bonus,
            quality_level=quality_level,
            confidence_level=confidence_level,
            recommendations=recommendations,
            detailed_analysis=detailed_analysis
        )
    
    def _calculate_authority_bonus(self, authority_source) -> float:
        """计算权威性加分"""
        if not authority_source:
            return 0.0
        
        # 根据权威源类别给予不同的加分
        category_bonus = {
            "government": 2.0,      # 政府机构最高加分
            "international": 1.8,   # 国际组织
            "statistics": 1.6,      # 统计机构
            "academic": 1.4,        # 学术机构
            "financial": 1.2,       # 金融机构
            "technology": 1.0,      # 科技机构
            "health": 1.0,          # 医疗机构
            "media": 0.8            # 媒体机构
        }
        
        base_bonus = category_bonus.get(authority_source.category, 0.0)
        
        # 根据可信度评分调整加分
        credibility_factor = authority_source.credibility_score / 10.0
        
        return base_bonus * credibility_factor
    
    def _get_quality_level(self, score: float) -> str:
        """根据评分确定质量等级"""
        if score >= 9.0:
            return "卓越"
        elif score >= 8.0:
            return "优秀"
        elif score >= 7.0:
            return "良好"
        elif score >= 6.0:
            return "一般"
        elif score >= 4.0:
            return "较差"
        else:
            return "很差"
    
    def _get_confidence_level(self, score: float, authority_source) -> str:
        """根据评分和权威性确定置信度等级"""
        if authority_source and authority_source.category in ["government", "international"]:
            if score >= 8.0:
                return "极高"
            elif score >= 6.0:
                return "高"
            else:
                return "中等"
        elif authority_source and authority_source.category in ["statistics", "academic"]:
            if score >= 8.0:
                return "高"
            elif score >= 6.0:
                return "中高"
            else:
                return "中等"
        else:
            if score >= 8.0:
                return "中高"
            elif score >= 6.0:
                return "中等"
            else:
                return "低"
    
    def _generate_recommendations(self, score: float, authority_source, validation_data) -> List[str]:
        """生成使用建议"""
        recommendations = []
        
        # 基于总体评分的建议
        if score >= 8.0:
            recommendations.append("数据质量优秀，可直接使用")
            recommendations.append("适合作为主要数据源")
        elif score >= 6.0:
            recommendations.append("数据质量良好，建议进行基本验证")
            recommendations.append("适合作为重要参考")
        elif score >= 4.0:
            recommendations.append("数据质量一般，需要多重验证")
            recommendations.append("建议与其他来源交叉验证")
        else:
            recommendations.append("数据质量较差，谨慎使用")
            recommendations.append("建议寻找更权威的数据源")
        
        # 基于权威性的建议
        if authority_source:
            if authority_source.category in ["government", "international"]:
                recommendations.append(f"来自权威机构{authority_source.name}，可信度高")
            elif authority_source.category in ["academic", "statistics"]:
                recommendations.append(f"来自专业机构{authority_source.name}，专业性强")
        else:
            recommendations.append("来源不在权威数据库中，建议验证发布方身份")
        
        # 基于内容质量的建议
        content_score = validation_data["content_quality"]["score"]
        if content_score < 5:
            recommendations.append("内容质量需要改进，建议寻找更详细的资料")
        
        # 基于时效性的建议
        timeliness_score = validation_data["timeliness"]["score"]
        if timeliness_score < 5:
            recommendations.append("信息可能过时，建议查找最新数据")
        
        return recommendations
    
    def _generate_detailed_analysis(self, validation_data, authority_source, overall_score) -> Dict[str, Any]:
        """生成详细分析报告"""
        analysis = {
            "authority_analysis": {},
            "content_analysis": validation_data["content_quality"],
            "timeliness_analysis": validation_data["timeliness"],
            "completeness_analysis": validation_data["completeness"],
            "credibility_analysis": validation_data["credibility"],
            "scoring_breakdown": {
                "credibility_contribution": validation_data["credibility"]["score"] * self.scoring_weights["credibility"],
                "content_quality_contribution": validation_data["content_quality"]["score"] * self.scoring_weights["content_quality"],
                "timeliness_contribution": validation_data["timeliness"]["score"] * self.scoring_weights["timeliness"],
                "completeness_contribution": validation_data["completeness"]["score"] * self.scoring_weights["completeness"],
                "authority_bonus_contribution": self._calculate_authority_bonus(authority_source) * self.scoring_weights["authority_bonus"]
            }
        }
        
        # 权威性分析
        if authority_source:
            analysis["authority_analysis"] = {
                "name": authority_source.name,
                "category": authority_source.category,
                "credibility_score": authority_source.credibility_score,
                "specialties": authority_source.specialties,
                "country": authority_source.country,
                "description": authority_source.description
            }
        else:
            analysis["authority_analysis"] = {
                "status": "非权威数据源",
                "warning": "未在权威数据库中找到该来源"
            }
        
        return analysis
    
    def get_quality_report(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成质量评估报告"""
        scored_results = self.score_search_results(search_results)
        
        if not scored_results:
            return {"error": "没有搜索结果可供评分"}
        
        scores = [result["quality_score"].overall_score for result in scored_results]
        quality_levels = [result["quality_score"].quality_level for result in scored_results]
        
        # 统计权威来源
        authority_sources = 0
        for result in scored_results:
            if result["quality_score"].authority_bonus > 0:
                authority_sources += 1
        
        # 质量等级分布
        level_distribution = {}
        for level in quality_levels:
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        # 评分分布
        score_distribution = {
            "优秀(8-10)": sum(1 for s in scores if s >= 8.0),
            "良好(6-8)": sum(1 for s in scores if 6.0 <= s < 8.0),
            "一般(4-6)": sum(1 for s in scores if 4.0 <= s < 6.0),
            "较差(0-4)": sum(1 for s in scores if s < 4.0)
        }
        
        return {
            "total_results": len(scored_results),
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "authority_sources": authority_sources,
            "authority_percentage": round(authority_sources / len(scored_results) * 100, 1),
            "quality_level_distribution": level_distribution,
            "score_distribution": score_distribution,
            "top_results": [
                {
                    "url": result["url"],
                    "title": result.get("title", ""),
                    "score": result["quality_score"].overall_score,
                    "quality_level": result["quality_score"].quality_level,
                    "authority_source": result["quality_score"].detailed_analysis["authority_analysis"].get("name", "非权威源")
                }
                for result in scored_results[:5]
            ],
            "recommendations": self._generate_overall_recommendations(scored_results)
        }
    
    def _generate_overall_recommendations(self, scored_results: List[Dict[str, Any]]) -> List[str]:
        """生成整体建议"""
        if not scored_results:
            return []
        
        recommendations = []
        
        # 计算统计信息
        scores = [result["quality_score"].overall_score for result in scored_results]
        avg_score = sum(scores) / len(scores)
        high_quality_count = sum(1 for s in scores if s >= 6.0)
        authority_count = sum(1 for result in scored_results if result["quality_score"].authority_bonus > 0)
        
        # 生成建议
        recommendations.append(f"总体质量评分: {avg_score:.1f}/10")
        recommendations.append(f"高质量结果占比: {high_quality_count}/{len(scored_results)} ({high_quality_count/len(scored_results)*100:.1f}%)")
        recommendations.append(f"权威来源占比: {authority_count}/{len(scored_results)} ({authority_count/len(scored_results)*100:.1f}%)")
        
        if avg_score >= 7.0:
            recommendations.append("整体数据质量良好，可放心使用")
        elif avg_score >= 5.0:
            recommendations.append("整体数据质量一般，建议重点关注高分结果")
        else:
            recommendations.append("整体数据质量较差，建议寻找更权威的数据源")
        
        if authority_count / len(scored_results) < 0.3:
            recommendations.append("权威来源较少，建议增加政府机构或国际组织的数据")
        
        return recommendations


# 创建全局评分器实例
quality_scorer = QualityScorer()


@tool
def score_search_results(search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    为搜索结果评分并排序
    
    Args:
        search_results: 搜索结果列表
    
    Returns:
        评分后的搜索结果列表，按质量评分排序
    """
    logger.info(f"开始为 {len(search_results)} 个搜索结果评分")
    
    scored_results = quality_scorer.score_search_results(search_results)
    
    logger.info(f"评分完成，平均分: {sum(r['quality_score'].overall_score for r in scored_results) / len(scored_results):.2f}")
    
    return scored_results


@tool
def filter_high_quality_results_by_score(search_results: List[Dict[str, Any]], 
                                        min_score: float = 6.0) -> List[Dict[str, Any]]:
    """
    根据质量评分过滤高质量结果
    
    Args:
        search_results: 搜索结果列表
        min_score: 最低质量评分要求
    
    Returns:
        过滤后的高质量结果列表
    """
    logger.info(f"开始过滤高质量结果，最低评分要求: {min_score}")
    
    scored_results = quality_scorer.score_search_results(search_results)
    
    high_quality_results = [
        result for result in scored_results 
        if result["quality_score"].overall_score >= min_score
    ]
    
    logger.info(f"过滤完成: {len(high_quality_results)}/{len(scored_results)} 个结果符合要求")
    
    return high_quality_results


@tool
def get_quality_assessment_report(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成质量评估报告
    
    Args:
        search_results: 搜索结果列表
    
    Returns:
        质量评估报告
    """
    logger.info("生成质量评估报告")
    
    report = quality_scorer.get_quality_report(search_results)
    
    return report


def get_quality_scorer() -> QualityScorer:
    """获取质量评分器实例"""
    return quality_scorer 