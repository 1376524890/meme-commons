"""
meme-commons 梗文化总结工具 - 调用Dashscope LLM生成结构化知识卡
"""
import requests
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from database.models import MemeCard, RawPost, TrendData, get_db_session
from config import settings
from vector_store import vector_store

logger = logging.getLogger(__name__)

class DashscopeLLMClient:
    """Dashscope LLM API客户端"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model = settings.DASHSCOPE_LLM_MODEL
        self.max_tokens = 2000
        self.temperature = 0.7
    
    def generate_text(self, prompt: str, system_prompt: str = None, max_tokens: int = None) -> Optional[str]:
        """生成文本"""
        if not self.api_key:
            logger.error("Dashscope API key not configured")
            return None
        
        try:
            payload = {
                "model": self.model,
                "input": {
                    "messages": []
                },
                "parameters": {
                    "max_tokens": max_tokens or self.max_tokens,
                    "temperature": self.temperature,
                    "result_format": "message"
                }
            }
            
            # 添加系统提示词
            if system_prompt:
                payload["input"]["messages"].append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加用户提示词
            payload["input"]["messages"].append({
                "role": "user",
                "content": prompt
            })
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == "200":
                return result["output"]["text"]
            else:
                logger.error(f"Dashscope LLM API error: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            return None

class MemeSummarizer:
    """梗文化总结工具"""
    
    def __init__(self):
        self.llm_client = DashscopeLLMClient()
        
        # 系统提示词模板
        self.system_prompt = """
你是一个专业的梗文化研究专家和网络文化分析师。你的任务是分析和总结网络梗文化现象。

请根据提供的内容，提取并总结梗文化的核心信息，生成结构化的知识卡。

输出格式必须为JSON，包含以下字段：
{
  "title": "梗的名称",
  "origin": "梗的起源和背景",
  "meaning": "梗的具体含义和用途",
  "examples": ["具体使用例子1", "具体使用例子2"],
  "category": "梗的类别",
  "sentiment": "正面/负面/中性",
  "popularity": "热度等级(1-10)"
}

请确保输出是有效的JSON格式，不要包含其他文字说明。
"""
        
        # 类别映射
        self.category_mapping = {
            "游戏": ["minecraft", "游戏", "steam", "任天堂", "ps", "xbox"],
            "动漫": ["动漫", "动画", "二次元", "acg", "anime", "漫画"],
            "网络": ["网络", "社交", "微博", "抖音", "快手"],
            "流行": ["流行", "热点", "热搜", "热门"],
            "科技": ["科技", "数码", "AI", "人工智能", "编程"],
            "生活": ["生活", "日常", "情感", "友情", "恋爱"],
            "幽默": ["幽默", "搞笑", "段子", "有趣"]
        }
    
    def summarize_meme(self, meme_id: str) -> Optional[Dict[str, Any]]:
        """总结指定的梗"""
        try:
            # 从数据库获取梗相关的数据
            session = get_db_session()
            
            # 获取原始帖子数据
            raw_posts = session.query(RawPost).filter(
                RawPost.content.contains(meme_id) if meme_id.isdigit() else True
            ).limit(20).all()
            
            if not raw_posts:
                logger.warning(f"No data found for meme_id: {meme_id}")
                session.close()
                return None
            
            # 准备用于LLM分析的文本
            content_data = self._prepare_content_for_analysis(raw_posts)
            
            session.close()
            
            # 调用LLM进行总结
            summary = self.llm_client.generate_text(
                prompt=self._create_analysis_prompt(content_data),
                system_prompt=self.system_prompt
            )
            
            if not summary:
                logger.error("Failed to generate meme summary")
                return None
            
            # 解析LLM输出
            parsed_summary = self._parse_llm_output(summary)
            if not parsed_summary:
                logger.error("Failed to parse LLM output")
                return None
            
            # 验证和完善总结数据
            validated_summary = self._validate_and_enhance_summary(parsed_summary)
            
            return validated_summary
            
        except Exception as e:
            logger.error(f"Failed to summarize meme {meme_id}: {e}")
            return None
    
    def summarize_posts_batch(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量总结帖子中的梗信息"""
        summaries = []
        
        # 将帖子按内容分组
        grouped_posts = self._group_posts_by_similarity(posts)
        
        for group in grouped_posts:
            try:
                # 准备内容数据
                content_data = self._prepare_content_for_analysis(group)
                
                # 调用LLM总结
                summary_text = self.llm_client.generate_text(
                    prompt=self._create_analysis_prompt(content_data),
                    system_prompt=self.system_prompt
                )
                
                if summary_text:
                    parsed_summary = self._parse_llm_output(summary_text)
                    if parsed_summary:
                        validated_summary = self._validate_and_enhance_summary(parsed_summary)
                        validated_summary["related_posts"] = [post["content"] for post in group]
                        summaries.append(validated_summary)
                
            except Exception as e:
                logger.error(f"Failed to summarize post group: {e}")
                continue
        
        return summaries
    
    def _prepare_content_for_analysis(self, posts: List[RawPost]) -> str:
        """准备用于LLM分析的内容"""
        content_parts = []
        
        for i, post in enumerate(posts[:10]):  # 限制分析前10个帖子
            content_parts.append(f"内容{i+1}: {post.content}")
            if post.author:
                content_parts.append(f"作者: {post.author}")
            content_parts.append(f"点赞: {post.upvotes}, 评论: {post.comment_count}")
            content_parts.append("---")
        
        return "\n".join(content_parts)
    
    def _create_analysis_prompt(self, content: str) -> str:
        """创建分析提示词"""
        return f"""
请分析以下网络梗相关的内容，提取核心信息并生成结构化的知识卡：

{content}

请严格按照JSON格式输出，不要包含其他文字。
"""
    
    def _parse_llm_output(self, output: str) -> Optional[Dict[str, Any]]:
        """解析LLM输出"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if not json_match:
                logger.error("No JSON found in LLM output")
                return None
            
            json_str = json_match.group(0)
            
            # 验证JSON格式
            parsed = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ["title", "origin", "meaning", "examples"]
            for field in required_fields:
                if field not in parsed:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM output: {e}")
            logger.debug(f"LLM output: {output}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse LLM output: {e}")
            return None
    
    def _validate_and_enhance_summary(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """验证和完善总结数据"""
        # 确保所有字段都存在
        validated = {
            "title": summary.get("title", "未知梗"),
            "origin": summary.get("origin", "未知起源"),
            "meaning": summary.get("meaning", "未知含义"),
            "examples": summary.get("examples", []),
            "category": self._map_to_category(summary.get("category", "")),
            "sentiment": summary.get("sentiment", "中性"),
            "popularity": max(1, min(10, int(summary.get("popularity", 5)))),
            "last_updated": datetime.now().isoformat()
        }
        
        # 验证examples格式
        if isinstance(validated["examples"], str):
            validated["examples"] = [validated["examples"]]
        elif not isinstance(validated["examples"], list):
            validated["examples"] = []
        
        return validated
    
    def _map_to_category(self, category: str) -> str:
        """映射类别"""
        category_lower = category.lower()
        
        for mapped_category, keywords in self.category_mapping.items():
            if any(keyword.lower() in category_lower for keyword in keywords):
                return mapped_category
        
        return "其他"
    
    def _group_posts_by_similarity(self, posts: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """按相似性分组帖子（简化实现）"""
        # 这里实现一个简化的分组逻辑
        # 实际中可以使用更复杂的聚类算法
        
        groups = []
        used_indices = set()
        
        for i, post in enumerate(posts):
            if i in used_indices:
                continue
            
            # 简单的相似性检查：查找包含相同关键词的帖子
            current_group = [post]
            used_indices.add(i)
            
            for j, other_post in enumerate(posts[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # 简单的关键词重叠检查
                if self._has_keyword_overlap(post["content"], other_post["content"]):
                    current_group.append(other_post)
                    used_indices.add(j)
            
            groups.append(current_group)
        
        return groups
    
    def _has_keyword_overlap(self, content1: str, content2: str) -> bool:
        """检查两个内容的关键词重叠"""
        # 提取关键词
        keywords1 = self._extract_simple_keywords(content1)
        keywords2 = self._extract_simple_keywords(content2)
        
        # 计算重叠
        overlap = set(keywords1) & set(keywords2)
        
        return len(overlap) > 0
    
    def _extract_simple_keywords(self, text: str) -> List[str]:
        """提取简单关键词"""
        import re
        
        # 移除标点符号
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # 分词并过滤短词
        words = cleaned_text.split()
        keywords = [word for word in words if len(word) > 2]
        
        return keywords[:10]  # 限制关键词数量

    def save_summary_to_db(self, summary: Dict[str, Any]) -> Optional[str]:
        """将总结保存到数据库"""
        try:
            session = get_db_session()
            
            # 检查是否已存在相同的梗
            existing_meme = session.query(MemeCard).filter(
                MemeCard.title == summary["title"]
            ).first()
            
            if existing_meme:
                # 更新现有记录
                existing_meme.origin = summary["origin"]
                existing_meme.meaning = summary["meaning"]
                existing_meme.examples = summary["examples"]
                existing_meme.category = summary["category"]
                existing_meme.last_updated = datetime.now()
                
                # 计算趋势分数（基于流行度和情感）
                trend_score = self._calculate_trend_score(summary)
                existing_meme.trend_score = trend_score
                
                meme_id = str(existing_meme.id)
            else:
                # 创建新记录
                new_meme = MemeCard(
                    title=summary["title"],
                    origin=summary["origin"],
                    meaning=summary["meaning"],
                    examples=summary["examples"],
                    category=summary["category"],
                    trend_score=self._calculate_trend_score(summary),
                    popularity_score=summary.get("popularity", 5)
                )
                session.add(new_meme)
                session.flush()  # 获取ID
                meme_id = str(new_meme.id)
            
            session.commit()
            session.close()
            
            # 缓存到Redis
            vector_store.cache_knowledge_card(summary["title"], summary)
            
            logger.info(f"Successfully saved meme summary: {summary['title']}")
            return meme_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save summary to database: {e}")
            return None
    
    def _calculate_trend_score(self, summary: Dict[str, Any]) -> float:
        """计算趋势分数"""
        base_score = summary.get("popularity", 5) / 10.0
        
        # 根据情感调整
        sentiment = summary.get("sentiment", "中性").lower()
        if sentiment == "正面":
            sentiment_multiplier = 1.2
        elif sentiment == "负面":
            sentiment_multiplier = 0.8
        else:
            sentiment_multiplier = 1.0
        
        return min(1.0, base_score * sentiment_multiplier)

# 全局总结工具实例
meme_summarizer = MemeSummarizer()