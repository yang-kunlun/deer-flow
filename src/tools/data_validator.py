# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
数据验证Agent
用于验证搜索结果的准确性、时效性和可信度
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.tools import tool
from src.tools.authority_search import get_authority_manager
from src.llms.llm import get_llm_by_type

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器，负责验证搜索结果的质量和可信度"""
    
    def __init__(self):
        self.authority_manager = get_authority_manager()
        
    def validate_search_result(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证单个搜索结果的质量"""
        url = search_result.get("url", "")
        content = search_result.get("content", "")
        title = search_result.get("title", "")
        
        # 1. 来源可信度检查
        credibility_info = self.authority_manager.get_source_credibility_info(url)
        
        # 2. 内容质量检查
        content_quality = self._analyze_content_quality(content, title)
        
        # 3. 时效性检查
        timeliness = self._check_timeliness(content, url)
        
        # 4. 数据完整性检查
        completeness = self._check_data_completeness(content)
        
        # 5. 计算综合评分
        overall_score = self._calculate_overall_score(
            credibility_info["score"],
            content_quality["score"],
            timeliness["score"],
            completeness["score"]
        )
        
        return {
            "url": url,
            "title": title,
            "validation_result": {
                "credibility": credibility_info,
                "content_quality": content_quality,
                "timeliness": timeliness,
                "completeness": completeness,
                "overall_score": overall_score,
                "quality_level": self._get_quality_level(overall_score),
                "recommendations": self._get_validation_recommendations(overall_score)
            }
        }
    
    def _analyze_content_quality(self, content: str, title: str) -> Dict[str, Any]:
        """分析内容质量"""
        if not content:
            return {
                "score": 0,
                "issues": ["内容为空"],
                "quality_indicators": []
            }
        
        quality_indicators = []
        issues = []
        score = 5  # 基础分
        
        # 检查内容长度
        content_length = len(content)
        if content_length < 100:
            issues.append("内容过短，信息量不足")
            score -= 2
        elif content_length > 200:
            quality_indicators.append("内容详细")
            score += 1
        
        # 检查是否有具体数据
        if re.search(r'\d+\.?\d*%|\d+\.?\d*亿|\d+\.?\d*万|\d+\.?\d*千', content):
            quality_indicators.append("包含具体数据")
            score += 1
        
        # 检查是否有时间信息
        if re.search(r'20\d{2}年|\d{4}-\d{2}-\d{2}|近期|最新|今年|去年', content):
            quality_indicators.append("包含时间信息")
            score += 1
        
        # 检查是否有引用来源
        if re.search(r'据.*报道|根据.*统计|.*发布|.*调查|.*研究', content):
            quality_indicators.append("有引用来源")
            score += 1
        
        # 检查是否有垃圾内容
        if re.search(r'Image \d+|乱码|[^\w\s\u4e00-\u9fff]', content):
            issues.append("包含垃圾内容或乱码")
            score -= 1
        
        # 检查标题与内容一致性
        if title and content:
            title_keywords = set(re.findall(r'\w+', title.lower()))
            content_keywords = set(re.findall(r'\w+', content.lower()[:500]))
            if len(title_keywords & content_keywords) > 0:
                quality_indicators.append("标题与内容一致")
                score += 1
        
        return {
            "score": min(10, max(0, score)),
            "issues": issues,
            "quality_indicators": quality_indicators
        }
    
    def _check_timeliness(self, content: str, url: str) -> Dict[str, Any]:
        """检查内容的时效性"""
        timeliness_score = 5  # 默认分数
        time_indicators = []
        
        # 检查内容中的时间信息
        current_year = datetime.now().year
        
        # 查找年份信息
        year_matches = re.findall(r'20(\d{2})', content)
        if year_matches:
            years = [int(y) + 2000 for y in year_matches]
            latest_year = max(years)
            
            if latest_year >= current_year:
                time_indicators.append(f"包含{latest_year}年信息")
                timeliness_score += 2
            elif latest_year >= current_year - 1:
                time_indicators.append(f"包含{latest_year}年信息（较新）")
                timeliness_score += 1
            elif latest_year >= current_year - 3:
                time_indicators.append(f"包含{latest_year}年信息（一般）")
            else:
                time_indicators.append(f"信息较旧（{latest_year}年）")
                timeliness_score -= 2
        
        # 检查相对时间表述
        if re.search(r'最新|最近|今年|本年|近期|刚刚|目前', content):
            time_indicators.append("包含最新时间表述")
            timeliness_score += 1
        
        # 检查URL中的时间信息
        url_year_match = re.search(r'20(\d{2})', url)
        if url_year_match:
            url_year = int(url_year_match.group(0))
            if url_year >= current_year - 1:
                time_indicators.append("URL显示为近期内容")
                timeliness_score += 1
        
        return {
            "score": min(10, max(0, timeliness_score)),
            "time_indicators": time_indicators,
            "estimated_age": self._estimate_content_age(content)
        }
    
    def _check_data_completeness(self, content: str) -> Dict[str, Any]:
        """检查数据完整性"""
        completeness_score = 5
        completeness_indicators = []
        
        # 检查是否有数据支撑
        if re.search(r'\d+\.?\d*%', content):
            completeness_indicators.append("包含百分比数据")
            completeness_score += 1
        
        if re.search(r'\d+\.?\d*亿|\d+\.?\d*万|\d+\.?\d*千', content):
            completeness_indicators.append("包含数量数据")
            completeness_score += 1
        
        # 检查是否有对比数据
        if re.search(r'同比|环比|相比|增长|下降|提高|降低', content):
            completeness_indicators.append("包含对比数据")
            completeness_score += 1
        
        # 检查是否有背景信息
        if re.search(r'背景|原因|影响|意义|作用', content):
            completeness_indicators.append("包含背景信息")
            completeness_score += 1
        
        # 检查内容结构
        if len(content) > 500 and '。' in content:
            completeness_indicators.append("内容结构完整")
            completeness_score += 1
        
        return {
            "score": min(10, max(0, completeness_score)),
            "completeness_indicators": completeness_indicators
        }
    
    def _calculate_overall_score(self, credibility: int, content_quality: int, 
                               timeliness: int, completeness: int) -> float:
        """计算综合评分"""
        # 权重分配：可信度40%，内容质量30%，时效性20%，完整性10%
        weights = {
            "credibility": 0.4,
            "content_quality": 0.3,
            "timeliness": 0.2,
            "completeness": 0.1
        }
        
        overall_score = (
            credibility * weights["credibility"] +
            content_quality * weights["content_quality"] +
            timeliness * weights["timeliness"] +
            completeness * weights["completeness"]
        )
        
        return round(overall_score, 2)
    
    def _get_quality_level(self, score: float) -> str:
        """根据评分获取质量等级"""
        if score >= 8.0:
            return "优秀"
        elif score >= 6.0:
            return "良好"
        elif score >= 4.0:
            return "一般"
        elif score >= 2.0:
            return "较差"
        else:
            return "很差"
    
    def _get_validation_recommendations(self, score: float) -> List[str]:
        """根据评分获取验证建议"""
        if score >= 8.0:
            return [
                "数据质量优秀，可直接使用",
                "适合作为主要数据源",
                "可用于重要报告和决策"
            ]
        elif score >= 6.0:
            return [
                "数据质量良好，建议核实关键信息",
                "可作为主要数据源，但需要补充验证",
                "适合大部分研究场景"
            ]
        elif score >= 4.0:
            return [
                "数据质量一般，建议多重验证",
                "可作为参考信息，但需要寻找更权威来源",
                "适合作为辅助数据源"
            ]
        else:
            return [
                "数据质量较差，不建议直接使用",
                "需要寻找更权威的数据源",
                "如果必须使用，需要充分验证"
            ]
    
    def _estimate_content_age(self, content: str) -> str:
        """估算内容的时效性"""
        current_year = datetime.now().year
        
        # 查找年份信息
        year_matches = re.findall(r'20(\d{2})', content)
        if year_matches:
            years = [int(y) + 2000 for y in year_matches]
            latest_year = max(years)
            
            if latest_year >= current_year:
                return "最新"
            elif latest_year >= current_year - 1:
                return "较新"
            elif latest_year >= current_year - 3:
                return "一般"
            else:
                return "较旧"
        
        # 检查相对时间表述
        if re.search(r'最新|最近|今年|本年|近期|刚刚|目前', content):
            return "最新"
        
        return "未知"


# 创建全局验证器实例
data_validator = DataValidator()


@tool
def validate_search_results(search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    验证搜索结果的质量和可信度
    
    Args:
        search_results: 搜索结果列表
    
    Returns:
        验证后的结果列表，包含质量评估信息
    """
    logger.info(f"开始验证 {len(search_results)} 个搜索结果")
    
    validated_results = []
    
    for result in search_results:
        validated_result = data_validator.validate_search_result(result)
        validated_results.append(validated_result)
        
        # 记录验证结果
        score = validated_result["validation_result"]["overall_score"]
        quality = validated_result["validation_result"]["quality_level"]
        logger.info(f"验证完成: {result.get('url', 'N/A')} - 评分: {score} - 质量: {quality}")
    
    return validated_results


@tool
def filter_high_quality_results(search_results: List[Dict[str, Any]], 
                               min_score: float = 6.0) -> List[Dict[str, Any]]:
    """
    过滤出高质量的搜索结果
    
    Args:
        search_results: 搜索结果列表
        min_score: 最低质量评分
    
    Returns:
        过滤后的高质量结果列表
    """
    logger.info(f"开始过滤搜索结果，最低评分要求: {min_score}")
    
    validated_results = validate_search_results(search_results)
    
    high_quality_results = []
    for result in validated_results:
        overall_score = result["validation_result"]["overall_score"]
        if overall_score >= min_score:
            high_quality_results.append(result)
    
    logger.info(f"过滤完成: {len(high_quality_results)}/{len(search_results)} 个结果符合质量要求")
    
    return high_quality_results


@tool
def get_data_validation_report(search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    生成数据验证报告
    
    Args:
        search_results: 搜索结果列表
    
    Returns:
        数据验证报告
    """
    logger.info("生成数据验证报告")
    
    validated_results = validate_search_results(search_results)
    
    # 统计信息
    total_results = len(validated_results)
    if total_results == 0:
        return {"error": "没有搜索结果可供验证"}
    
    scores = [r["validation_result"]["overall_score"] for r in validated_results]
    quality_levels = [r["validation_result"]["quality_level"] for r in validated_results]
    
    # 计算统计数据
    avg_score = sum(scores) / len(scores)
    high_quality_count = sum(1 for s in scores if s >= 6.0)
    authority_sources = sum(1 for r in validated_results 
                          if r["validation_result"]["credibility"]["is_authority"])
    
    # 质量等级分布
    quality_distribution = {}
    for level in quality_levels:
        quality_distribution[level] = quality_distribution.get(level, 0) + 1
    
    return {
        "total_results": total_results,
        "average_score": round(avg_score, 2),
        "high_quality_results": high_quality_count,
        "high_quality_percentage": round(high_quality_count / total_results * 100, 1),
        "authority_sources": authority_sources,
        "authority_percentage": round(authority_sources / total_results * 100, 1),
        "quality_distribution": quality_distribution,
        "recommendations": [
            f"总共验证了 {total_results} 个搜索结果",
            f"平均质量评分: {avg_score:.2f}/10",
            f"高质量结果占比: {high_quality_count}/{total_results} ({high_quality_count/total_results*100:.1f}%)",
            f"权威来源占比: {authority_sources}/{total_results} ({authority_sources/total_results*100:.1f}%)",
            "建议优先使用质量评分6.0以上的结果"
        ]
    } 