# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

"""
权威数据源数据库
包含各个领域的权威机构和数据源信息
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AuthoritySource:
    """权威数据源信息"""
    name: str                    # 机构名称
    domain: str                  # 主域名
    domains: List[str]           # 所有相关域名
    category: str                # 类别
    credibility_score: int       # 可信度评分 (1-10)
    description: str             # 描述
    language: str                # 主要语言
    country: str                 # 国家
    specialties: List[str]       # 专业领域
    data_types: List[str]        # 数据类型
    last_updated: datetime = field(default_factory=datetime.now)


class AuthorityDatabase:
    """权威数据源数据库"""
    
    def __init__(self):
        self.sources: Dict[str, AuthoritySource] = {}
        self._initialize_database()
    
    def _initialize_database(self):
        """初始化权威数据源数据库"""
        
        # 中国政府机构
        self._add_government_sources_china()
        
        # 国际政府机构
        self._add_government_sources_international()
        
        # 国际组织
        self._add_international_organizations()
        
        # 统计机构
        self._add_statistics_organizations()
        
        # 学术机构
        self._add_academic_institutions()
        
        # 权威媒体
        self._add_media_organizations()
        
        # 金融机构
        self._add_financial_institutions()
        
        # 科技机构
        self._add_technology_organizations()
        
        # 医疗卫生机构
        self._add_health_organizations()
        
        logger.info(f"权威数据源数据库初始化完成，共加载 {len(self.sources)} 个权威源")
    
    def _add_government_sources_china(self):
        """添加中国政府机构数据源"""
        
        # 国家统计局
        self._add_source(AuthoritySource(
            name="国家统计局",
            domain="stats.gov.cn",
            domains=["stats.gov.cn", "data.stats.gov.cn"],
            category="government",
            credibility_score=10,
            description="中华人民共和国国家统计局，负责国家统计工作",
            language="zh-CN",
            country="China",
            specialties=["统计数据", "经济数据", "人口数据", "社会发展"],
            data_types=["统计报告", "数据公报", "统计年鉴", "经济指标"]
        ))
        
        # 商务部
        self._add_source(AuthoritySource(
            name="商务部",
            domain="mofcom.gov.cn",
            domains=["mofcom.gov.cn", "english.mofcom.gov.cn"],
            category="government",
            credibility_score=10,
            description="中华人民共和国商务部",
            language="zh-CN",
            country="China",
            specialties=["对外贸易", "对外投资", "国内贸易", "国际经济合作"],
            data_types=["贸易数据", "投资数据", "政策文件", "统计公报"]
        ))
        
        # 发改委
        self._add_source(AuthoritySource(
            name="国家发展改革委",
            domain="ndrc.gov.cn",
            domains=["ndrc.gov.cn", "en.ndrc.gov.cn"],
            category="government",
            credibility_score=10,
            description="国家发展和改革委员会",
            language="zh-CN",
            country="China",
            specialties=["宏观经济", "产业政策", "投资管理", "价格监管"],
            data_types=["政策文件", "经济数据", "投资数据", "价格信息"]
        ))
        
        # 人民银行
        self._add_source(AuthoritySource(
            name="中国人民银行",
            domain="pboc.gov.cn",
            domains=["pboc.gov.cn", "pbc.gov.cn"],
            category="government",
            credibility_score=10,
            description="中华人民共和国中央银行",
            language="zh-CN",
            country="China",
            specialties=["货币政策", "金融监管", "外汇管理", "支付系统"],
            data_types=["货币政策", "金融数据", "汇率信息", "统计报告"]
        ))
        
        # 卫健委
        self._add_source(AuthoritySource(
            name="国家卫生健康委员会",
            domain="nhc.gov.cn",
            domains=["nhc.gov.cn", "en.nhc.gov.cn"],
            category="government",
            credibility_score=10,
            description="国家卫生健康委员会",
            language="zh-CN",
            country="China",
            specialties=["公共卫生", "医疗服务", "健康政策", "疾病预防"],
            data_types=["健康数据", "医疗统计", "政策文件", "疫情信息"]
        ))
    
    def _add_government_sources_international(self):
        """添加国际政府机构数据源"""
        
        # 美国政府
        self._add_source(AuthoritySource(
            name="美国政府",
            domain="gov",
            domains=[".gov"],
            category="government",
            credibility_score=9,
            description="美国联邦政府官方网站",
            language="en",
            country="United States",
            specialties=["政府信息", "法律法规", "统计数据", "公共服务"],
            data_types=["政策文件", "统计报告", "法律文档", "官方声明"]
        ))
        
        # 英国政府
        self._add_source(AuthoritySource(
            name="英国政府",
            domain="gov.uk",
            domains=[".gov.uk"],
            category="government",
            credibility_score=9,
            description="英国政府官方网站",
            language="en",
            country="United Kingdom",
            specialties=["政府信息", "法律法规", "统计数据", "公共服务"],
            data_types=["政策文件", "统计报告", "法律文档", "官方声明"]
        ))
    
    def _add_international_organizations(self):
        """添加国际组织数据源"""
        
        # 世界卫生组织
        self._add_source(AuthoritySource(
            name="世界卫生组织",
            domain="who.int",
            domains=["who.int", "www.who.int"],
            category="international",
            credibility_score=9,
            description="世界卫生组织（WHO）",
            language="en",
            country="International",
            specialties=["全球健康", "疾病预防", "医疗标准", "健康政策"],
            data_types=["健康报告", "疾病数据", "医疗指南", "全球统计"]
        ))
        
        # 联合国
        self._add_source(AuthoritySource(
            name="联合国",
            domain="un.org",
            domains=["un.org", "www.un.org"],
            category="international",
            credibility_score=9,
            description="联合国（United Nations）",
            language="en",
            country="International",
            specialties=["国际关系", "全球发展", "和平安全", "人权"],
            data_types=["研究报告", "统计数据", "政策文件", "全球指标"]
        ))
        
        # 世界银行
        self._add_source(AuthoritySource(
            name="世界银行",
            domain="worldbank.org",
            domains=["worldbank.org", "www.worldbank.org", "data.worldbank.org"],
            category="international",
            credibility_score=9,
            description="世界银行（World Bank）",
            language="en",
            country="International",
            specialties=["经济发展", "减贫", "金融服务", "发展援助"],
            data_types=["经济数据", "发展报告", "统计指标", "研究分析"]
        ))
        
        # 国际货币基金组织
        self._add_source(AuthoritySource(
            name="国际货币基金组织",
            domain="imf.org",
            domains=["imf.org", "www.imf.org"],
            category="international",
            credibility_score=9,
            description="国际货币基金组织（IMF）",
            language="en",
            country="International",
            specialties=["货币政策", "金融稳定", "经济监管", "国际合作"],
            data_types=["经济数据", "金融报告", "政策建议", "全球展望"]
        ))
    
    def _add_statistics_organizations(self):
        """添加统计机构数据源"""
        
        # 经济合作与发展组织
        self._add_source(AuthoritySource(
            name="经济合作与发展组织",
            domain="oecd.org",
            domains=["oecd.org", "www.oecd.org", "data.oecd.org"],
            category="statistics",
            credibility_score=8,
            description="经济合作与发展组织（OECD）",
            language="en",
            country="International",
            specialties=["经济统计", "社会指标", "教育数据", "环境数据"],
            data_types=["统计数据", "经济报告", "政策分析", "国际比较"]
        ))
        
        # 美国统计局
        self._add_source(AuthoritySource(
            name="美国人口普查局",
            domain="census.gov",
            domains=["census.gov", "www.census.gov"],
            category="statistics",
            credibility_score=8,
            description="美国人口普查局",
            language="en",
            country="United States",
            specialties=["人口统计", "经济数据", "住房数据", "社会统计"],
            data_types=["人口数据", "经济统计", "社会指标", "地理信息"]
        ))
    
    def _add_academic_institutions(self):
        """添加学术机构数据源"""
        
        # 清华大学
        self._add_source(AuthoritySource(
            name="清华大学",
            domain="tsinghua.edu.cn",
            domains=["tsinghua.edu.cn", "www.tsinghua.edu.cn"],
            category="academic",
            credibility_score=8,
            description="清华大学",
            language="zh-CN",
            country="China",
            specialties=["工程技术", "自然科学", "管理科学", "人文社科"],
            data_types=["学术论文", "研究报告", "技术文档", "教育资源"]
        ))
        
        # 北京大学
        self._add_source(AuthoritySource(
            name="北京大学",
            domain="pku.edu.cn",
            domains=["pku.edu.cn", "www.pku.edu.cn"],
            category="academic",
            credibility_score=8,
            description="北京大学",
            language="zh-CN",
            country="China",
            specialties=["基础科学", "人文社科", "医学", "法学"],
            data_types=["学术论文", "研究报告", "政策建议", "教育资源"]
        ))
        
        # 麻省理工学院
        self._add_source(AuthoritySource(
            name="麻省理工学院",
            domain="mit.edu",
            domains=["mit.edu", "www.mit.edu"],
            category="academic",
            credibility_score=8,
            description="麻省理工学院（MIT）",
            language="en",
            country="United States",
            specialties=["工程技术", "计算机科学", "自然科学", "管理"],
            data_types=["学术论文", "研究报告", "技术文档", "创新成果"]
        ))
        
        # 自然杂志
        self._add_source(AuthoritySource(
            name="自然杂志",
            domain="nature.com",
            domains=["nature.com", "www.nature.com"],
            category="academic",
            credibility_score=9,
            description="《自然》杂志",
            language="en",
            country="International",
            specialties=["自然科学", "基础研究", "科学发现", "技术创新"],
            data_types=["学术论文", "研究文章", "科学新闻", "评论文章"]
        ))
    
    def _add_media_organizations(self):
        """添加权威媒体数据源"""
        
        # 新华社
        self._add_source(AuthoritySource(
            name="新华社",
            domain="xinhuanet.com",
            domains=["xinhuanet.com", "xinhua.net", "news.cn"],
            category="media",
            credibility_score=8,
            description="新华通讯社",
            language="zh-CN",
            country="China",
            specialties=["时政新闻", "经济新闻", "国际新闻", "社会新闻"],
            data_types=["新闻报道", "时政分析", "经济数据", "国际动态"]
        ))
        
        # 人民日报
        self._add_source(AuthoritySource(
            name="人民日报",
            domain="people.com.cn",
            domains=["people.com.cn", "www.people.com.cn"],
            category="media",
            credibility_score=8,
            description="人民日报",
            language="zh-CN",
            country="China",
            specialties=["时政新闻", "评论文章", "社会新闻", "文化新闻"],
            data_types=["新闻报道", "评论文章", "政策解读", "社会动态"]
        ))
        
        # 路透社
        self._add_source(AuthoritySource(
            name="路透社",
            domain="reuters.com",
            domains=["reuters.com", "www.reuters.com"],
            category="media",
            credibility_score=7,
            description="路透社（Reuters）",
            language="en",
            country="International",
            specialties=["国际新闻", "财经新闻", "科技新闻", "政治新闻"],
            data_types=["新闻报道", "市场分析", "经济数据", "国际动态"]
        ))
        
        # BBC
        self._add_source(AuthoritySource(
            name="英国广播公司",
            domain="bbc.com",
            domains=["bbc.com", "www.bbc.com", "bbc.co.uk"],
            category="media",
            credibility_score=7,
            description="英国广播公司（BBC）",
            language="en",
            country="United Kingdom",
            specialties=["国际新闻", "科技新闻", "文化新闻", "体育新闻"],
            data_types=["新闻报道", "深度分析", "纪录片", "教育内容"]
        ))
    
    def _add_financial_institutions(self):
        """添加金融机构数据源"""
        
        # 中国证券监督管理委员会
        self._add_source(AuthoritySource(
            name="中国证监会",
            domain="csrc.gov.cn",
            domains=["csrc.gov.cn", "www.csrc.gov.cn"],
            category="financial",
            credibility_score=9,
            description="中国证券监督管理委员会",
            language="zh-CN",
            country="China",
            specialties=["证券监管", "资本市场", "投资管理", "金融政策"],
            data_types=["监管政策", "市场数据", "公司信息", "投资指南"]
        ))
        
        # 上海证券交易所
        self._add_source(AuthoritySource(
            name="上海证券交易所",
            domain="sse.com.cn",
            domains=["sse.com.cn", "www.sse.com.cn"],
            category="financial",
            credibility_score=9,
            description="上海证券交易所",
            language="zh-CN",
            country="China",
            specialties=["股票交易", "债券市场", "公司上市", "市场数据"],
            data_types=["市场数据", "公司公告", "交易信息", "投资者教育"]
        ))
        
        # 美国证券交易委员会
        self._add_source(AuthoritySource(
            name="美国证券交易委员会",
            domain="sec.gov",
            domains=["sec.gov", "www.sec.gov"],
            category="financial",
            credibility_score=9,
            description="美国证券交易委员会（SEC）",
            language="en",
            country="United States",
            specialties=["证券监管", "投资者保护", "市场监管", "公司监管"],
            data_types=["监管文件", "公司报告", "投资指南", "市场数据"]
        ))
    
    def _add_technology_organizations(self):
        """添加科技机构数据源"""
        
        # 中国科技部
        self._add_source(AuthoritySource(
            name="科学技术部",
            domain="most.gov.cn",
            domains=["most.gov.cn", "www.most.gov.cn"],
            category="technology",
            credibility_score=9,
            description="中华人民共和国科学技术部",
            language="zh-CN",
            country="China",
            specialties=["科技政策", "科技发展", "创新创业", "科技合作"],
            data_types=["科技政策", "发展规划", "科技统计", "创新报告"]
        ))
        
        # 中国科学院
        self._add_source(AuthoritySource(
            name="中国科学院",
            domain="cas.cn",
            domains=["cas.cn", "www.cas.cn"],
            category="technology",
            credibility_score=8,
            description="中国科学院",
            language="zh-CN",
            country="China",
            specialties=["基础研究", "应用研究", "技术创新", "人才培养"],
            data_types=["研究报告", "科技成果", "学术论文", "技术文档"]
        ))
    
    def _add_health_organizations(self):
        """添加医疗卫生机构数据源"""
        
        # 中国疾病预防控制中心
        self._add_source(AuthoritySource(
            name="中国疾病预防控制中心",
            domain="chinacdc.cn",
            domains=["chinacdc.cn", "www.chinacdc.cn"],
            category="health",
            credibility_score=9,
            description="中国疾病预防控制中心",
            language="zh-CN",
            country="China",
            specialties=["疾病预防", "健康监测", "流行病学", "公共卫生"],
            data_types=["疾病数据", "健康报告", "防控指南", "监测信息"]
        ))
        
        # 美国疾病控制与预防中心
        self._add_source(AuthoritySource(
            name="美国疾病控制与预防中心",
            domain="cdc.gov",
            domains=["cdc.gov", "www.cdc.gov"],
            category="health",
            credibility_score=9,
            description="美国疾病控制与预防中心（CDC）",
            language="en",
            country="United States",
            specialties=["疾病预防", "健康促进", "应急准备", "职业健康"],
            data_types=["健康数据", "疾病监测", "预防指南", "研究报告"]
        ))
    
    def _add_source(self, source: AuthoritySource):
        """添加数据源"""
        self.sources[source.domain] = source
        logger.debug(f"添加权威数据源: {source.name} ({source.domain})")
    
    def get_source_by_domain(self, domain: str) -> Optional[AuthoritySource]:
        """根据域名获取数据源信息"""
        return self.sources.get(domain)
    
    def get_source_by_url(self, url: str) -> Optional[AuthoritySource]:
        """根据URL获取数据源信息"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 直接匹配
            if domain in self.sources:
                return self.sources[domain]
            
            # 模糊匹配
            for source_domain, source in self.sources.items():
                if domain.endswith(source_domain) or source_domain in domain:
                    return source
                
                # 检查别名域名
                for alias_domain in source.domains:
                    if domain.endswith(alias_domain) or alias_domain in domain:
                        return source
            
            return None
        except Exception as e:
            logger.warning(f"解析URL时出错: {url}, 错误: {e}")
            return None
    
    def search_sources(self, **kwargs) -> List[AuthoritySource]:
        """搜索数据源"""
        results = []
        
        for source in self.sources.values():
            match = True
            
            # 按类别筛选
            if 'category' in kwargs and source.category != kwargs['category']:
                match = False
            
            # 按国家筛选
            if 'country' in kwargs and source.country != kwargs['country']:
                match = False
            
            # 按语言筛选
            if 'language' in kwargs and source.language != kwargs['language']:
                match = False
            
            # 按可信度筛选
            if 'min_credibility' in kwargs and source.credibility_score < kwargs['min_credibility']:
                match = False
            
            # 按专业领域筛选
            if 'specialty' in kwargs:
                specialty = kwargs['specialty'].lower()
                if not any(specialty in s.lower() for s in source.specialties):
                    match = False
            
            if match:
                results.append(source)
        
        # 按可信度排序
        results.sort(key=lambda x: x.credibility_score, reverse=True)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        
        # 按类别统计
        category_counts = {}
        for source in self.sources.values():
            category_counts[source.category] = category_counts.get(source.category, 0) + 1
        
        # 按国家统计
        country_counts = {}
        for source in self.sources.values():
            country_counts[source.country] = country_counts.get(source.country, 0) + 1
        
        # 按语言统计
        language_counts = {}
        for source in self.sources.values():
            language_counts[source.language] = language_counts.get(source.language, 0) + 1
        
        # 可信度分布
        credibility_distribution = {}
        for source in self.sources.values():
            score = source.credibility_score
            credibility_distribution[score] = credibility_distribution.get(score, 0) + 1
        
        return {
            "total_sources": len(self.sources),
            "category_distribution": category_counts,
            "country_distribution": country_counts,
            "language_distribution": language_counts,
            "credibility_distribution": credibility_distribution,
            "average_credibility": sum(s.credibility_score for s in self.sources.values()) / len(self.sources)
        }


# 创建全局数据库实例
authority_database = AuthorityDatabase()


def get_authority_database() -> AuthorityDatabase:
    """获取权威数据源数据库实例"""
    return authority_database 