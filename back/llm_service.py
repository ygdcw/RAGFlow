from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import config


class LLMService:
    """
    LLM对话服务类
    负责管理deepseek-chat大模型的初始化和调用
    
    【人A负责】：LLM模型集成与服务封装
    【协作需求】：
    - 【人D】检索模块需将检索结果传入此类生成回答
    - 【人C】对话历史管理模块需与此类交互以保持上下文连贯
    """

    def __init__(self):
        """
        初始化LLM对话服务
        使用配置文件中的deepseek-chat模型参数
        """
        config.validate_config()
        
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL_NAME,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_API_BASE,
            temperature=config.LLM_TEMPERATURE,
        )

    def generate_response(self, query, context=None, chat_history=None):
        """
        生成基于上下文的回答
        
        参数：
            query (str): 用户查询问题
            context (str, optional): 检索到的相关知识上下文
            chat_history (list, optional): 对话历史记录，格式为[(user_msg, ai_msg), ...]
        
        返回：
            str: 生成的回答文本
        
        【人D协作接口】：检索模块调用此方法生成最终回答
        数据格式：
            - context: 拼接后的知识文本字符串
            - chat_history: 元组列表，每个元组包含(user_msg, ai_msg)
        """
        messages = []

        if chat_history:
            for user_msg, ai_msg in chat_history:
                messages.append(HumanMessage(content=user_msg))
                messages.append(SystemMessage(content=ai_msg))

        if context:
            system_prompt = f"""你是一个基于RAG的智能问答助手。
请根据以下提供的知识上下文回答用户问题：

知识上下文：
{context}

回答要求：
1. 必须基于提供的知识上下文进行回答
2. 如果上下文没有相关信息，请明确说明"没有找到相关信息"
3. 回答要准确、简洁、自然
4. 保持与之前对话的连贯性
"""
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=query))

        try:
            response = self.llm(messages)
            return response.content
        except Exception as e:
            raise RuntimeError(f"LLM调用失败: {str(e)}") from e

    def generate_answer_with_sources(self, query, source_documents, chat_history=None):
        """
        根据检索到的源文档生成回答，并保留来源信息
        
        参数：
            query (str): 用户查询问题
            source_documents (list): 检索到的源文档列表，每个文档包含page_content和metadata
            chat_history (list, optional): 对话历史记录
        
        返回：
            dict: 包含回答和来源信息的字典
                {
                    "answer": str,
                    "sources": list[dict]  # 每个元素包含content和metadata
                }
        
        【人D协作接口】：检索模块调用此方法生成带来源的回答
        数据格式：
            - source_documents: Document对象列表
            - 返回值：包含answer和sources的字典
        """
        context = "\n\n".join([doc.page_content for doc in source_documents])
        
        answer = self.generate_response(query, context, chat_history)
        
        sources = []
        for doc in source_documents:
            sources.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata if hasattr(doc, "metadata") else {}
            })

        return {
            "answer": answer,
            "sources": sources
        }


llm_service = LLMService()
