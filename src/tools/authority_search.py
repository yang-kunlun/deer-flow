# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
权威源检索工具
优先搜索政府官网、权威媒体等可靠数据源
"""

import logging
import re
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from src.tools.search import get_web_search_tool
from src.config.configuration import Configuration

logger = logging.getLogger(__name__)


class AuthoritySourceManager:
    """权威数据源管理器"""
    
    def __init__(self):
        # 权威域名列表（按优先级排序）
        self.authority_domains = {
            # 政府官网
            "government": [
                ".gov.cn", ".gov", ".gov.uk", ".gov.au", ".gov.ca",
                "stats.gov.cn", "mofcom.gov.cn", "ndrc.gov.cn", 
                "pboc.gov.cn", "mof.gov.cn", "miit.gov.cn",
                "nhc.gov.cn", "mee.gov.cn", "mem.gov.cn"
            ],
            # 国际组织
            "international": [
                "who.int", "un.org", "worldbank.org", "imf.org",
                "oecd.org", "wto.org", "unesco.org", "unicef.org",
                "fao.org", "iea.org", "itu.int"
            ],
            # 权威媒体
            "media": [
                "xinhua.net", "xinhuanet.com", "people.com.cn",
                "cctv.com", "chinadaily.com.cn", "cgtn.com",
                "reuters.com", "bbc.com", "cnn.com", "npr.org",
                "wsj.com", "ft.com", "economist.com"
            ],
            # 学术机构
            "academic": [
                "tsinghua.edu.cn", "pku.edu.cn", "fudan.edu.cn",
                "mit.edu", "harvard.edu", "stanford.edu", "ox.ac.uk",
                "cambridge.org", "nature.com", "science.org", "cell.com"
            ],
            # 金融机构
            "financial": [
                "imf.org", "bis.org", "worldbank.org", "adb.org",
                "federalreserve.gov", "ecb.europa.eu", "boj.or.jp",
                "boe.co.uk", "rbi.org.in", "pboc.gov.cn"
            ],
            # 统计机构
            "statistics": [
                "stats.gov.cn", "census.gov", "ons.gov.uk",
                "abs.gov.au", "statcan.gc.ca", "destatis.de",
                "insee.fr", "stat.go.jp", "kostat.go.kr"
            ]
        }
        
        # 为每个域名类型设置权重
        self.domain_weights = {
            "government": 10,
            "international": 9,
            "statistics": 8,
            "academic": 7,
            "financial": 6,
            "media": 5
        }
    
    def get_domain_authority_score(self, url: str) -> int:
        """获取域名权威性评分"""
        url_lower = url.lower()
        
        for domain_type, domains in self.authority_domains.items():
            for domain in domains:
                if domain in url_lower:
                    return self.domain_weights[domain_type]
        
        return 0  # 未知域名
    
    def is_authority_source(self, url: str) -> bool:
        """判断是否为权威数据源"""
        return self.get_domain_authority_score(url) > 0
    
    def filter_authority_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤出权威数据源的搜索结果"""
        authority_results = []
        
        for result in search_results:
            url = result.get("url", "")
            score = self.get_domain_authority_score(url)
            
            if score > 0:
                result["authority_score"] = score
                authority_results.append(result)
        
        # 按权威性评分排序
        authority_results.sort(key=lambda x: x.get("authority_score", 0), reverse=True)
        
        return authority_results
    
    def enhance_search_query(self, query: str, domain_type: Optional[str] = None) -> str:
        """增强搜索查询，添加权威源限制"""
        enhanced_query = query
        
        if domain_type and domain_type in self.authority_domains:
            # 添加特定域名限制
            domains = self.authority_domains[domain_type][:3]  # 取前3个最权威的域名
            domain_filters = " OR ".join([f"site:{domain}" for domain in domains])
            enhanced_query = f"({query}) AND ({domain_filters})"
        else:
            # 添加常见权威域名限制
            common_domains = [
                ".gov.cn", ".gov", "stats.gov.cn", "xinhua.net",
                "people.com.cn", "who.int", "worldbank.org"
            ]
            domain_filters = " OR ".join([f"site:{domain}" for domain in common_domains])
            enhanced_query = f"({query}) AND ({domain_filters})"
        
        return enhanced_query
    
    def get_source_credibility_info(self, url: str) -> Dict[str, Any]:
        """获取数据源可信度信息"""
        score = self.get_domain_authority_score(url)
        
        if score >= 8:
            credibility = "极高"
            description = "政府官网、国际组织或权威统计机构"
        elif score >= 6:
            credibility = "高"
            description = "知名学术机构或权威金融机构"
        elif score >= 4:
            credibility = "中等"
            description = "权威媒体或行业机构"
        else:
            credibility = "待验证"
            description = "普通网站，需要交叉验证"
        
        return {
            "score": score,
            "credibility": credibility,
            "description": description,
            "is_authority": score > 0
        }


# 全局权威源管理器实例
authority_manager = AuthoritySourceManager()


@tool
def authority_search_tool(query: str, domain_type: str = None, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    权威源搜索工具
    
    Args:
        query: 搜索查询
        domain_type: 域名类型限制 (government, international, media, academic, financial, statistics)
        max_results: 最大结果数量
    
    Returns:
        权威源搜索结果列表
    """
    logger.info(f"Authority search: {query}, domain_type: {domain_type}")
    
    # 增强搜索查询
    enhanced_query = authority_manager.enhance_search_query(query, domain_type)
    logger.info(f"Enhanced query: {enhanced_query}")
    
    # 执行搜索
    try:
        search_tool = get_web_search_tool(max_results * 2)  # 获取更多结果用于过滤
        raw_results = search_tool.invoke(enhanced_query)
        
        # 如果返回的是字符串，尝试解析
        if isinstance(raw_results, str):
            logger.warning(f"Search returned string result: {raw_results}")
            return [{
                "title": "搜索结果",
                "url": "N/A",
                "content": raw_results,
                "authority_score": 0
            }]
        
        # 过滤出权威数据源
        authority_results = authority_manager.filter_authority_results(raw_results)
        
        # 限制结果数量
        authority_results = authority_results[:max_results]
        
        # 添加可信度信息
        for result in authority_results:
            credibility_info = authority_manager.get_source_credibility_info(result.get("url", ""))
            result["credibility_info"] = credibility_info
        
        logger.info(f"Found {len(authority_results)} authority results out of {len(raw_results)} total results")
        
        return authority_results
        
    except Exception as e:
        logger.error(f"Authority search failed: {e}")
        return [{
            "title": "搜索失败",
            "url": "N/A",
            "content": f"权威源搜索失败: {str(e)}",
            "authority_score": 0
        }]


@tool
def credibility_checker_tool(url: str) -> Dict[str, Any]:
    """
    可信度检查工具
    
    Args:
        url: 要检查的URL
    
    Returns:
        可信度评估结果
    """
    logger.info(f"Checking credibility for: {url}")
    
    credibility_info = authority_manager.get_source_credibility_info(url)
    
    return {
        "url": url,
        "credibility_score": credibility_info["score"],
        "credibility_level": credibility_info["credibility"],
        "description": credibility_info["description"],
        "is_authority_source": credibility_info["is_authority"],
        "recommendations": get_usage_recommendations(credibility_info["score"])
    }


def get_usage_recommendations(score: int) -> List[str]:
    """根据可信度评分获取使用建议"""
    if score >= 8:
        return [
            "可直接引用，无需额外验证",
            "适合作为主要数据源",
            "可用于重要决策支持"
        ]
    elif score >= 6:
        return [
            "建议与其他权威源交叉验证",
            "适合作为辅助数据源",
            "可用于学术研究引用"
        ]
    elif score >= 4:
        return [
            "需要多重验证",
            "可作为参考信息",
            "建议查找原始数据源"
        ]
    else:
        return [
            "需要谨慎使用",
            "必须进行多重验证",
            "建议寻找更权威的数据源"
        ]


def get_authority_manager() -> AuthoritySourceManager:
    """获取权威源管理器实例"""
    return authority_manager 