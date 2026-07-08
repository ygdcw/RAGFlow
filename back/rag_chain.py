from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain
from config import config
from llm_service import llm_service
from vector_db import vector_db_service
from chat_history_manager import chat_history_manager


class RAGChain:
    """
    RAG链构建类
    负责构建和管理基于RAG的问答链，整合检索和生成能力
    
    【人A负责】：RAG链构建与管理
    【人C扩展】：通过chat_history_manager实现对话历史持久化和管理
    【协作需求】：
    - 【人C】向量数据库模块提供检索能力
    - 【人A】LLM服务模块提供生成能力
    - 【人D】检索策略优化需要与此类集成
    - 【人C】对话历史管理模块提供会话管理和消息持久化
    """

    def __init__(self):
        """
        初始化RAG链
        创建对话记忆和检索问答链
        """
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )
        
        self.retriever = vector_db_service.get_retriever()
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm_service.llm,
            memory=self.memory,
            retriever=self.retriever,
            return_source_documents=True,
            verbose=True,
        )

    def query(self, question):
        """
        执行RAG查询
        
        参数：
            question (str): 用户问题
        
        返回：
            dict: 查询结果，包含answer和source_documents
        
        【人D协作接口】：检索模块调用此方法执行完整的RAG查询
        数据格式：输入为问题字符串，输出为包含answer和source_documents的字典
        """
        if not question:
            return {
                "answer": "请输入有效的问题",
                "source_documents": []
            }
        
        try:
            result = self.qa_chain.invoke({"question": question})
            return result
        except Exception as e:
            raise RuntimeError(f"RAG查询失败: {str(e)}") from e

    def query_with_sources(self, question):
        """
        执行RAG查询并返回来源信息
        
        参数：
            question (str): 用户问题
        
        返回：
            dict: 查询结果，包含answer、source_documents和formatted_sources
        
        【人D协作接口】：检索模块调用此方法执行查询并获取格式化的来源信息
        数据格式：输出为包含answer和formatted_sources的字典
        """
        result = self.query(question)
        
        formatted_sources = []
        if "source_documents" in result and result["source_documents"]:
            for doc in result["source_documents"]:
                formatted_sources.append({
                    "content": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, "metadata") else {}
                })
        
        return {
            "answer": result.get("answer", ""),
            "source_documents": result.get("source_documents", []),
            "formatted_sources": formatted_sources
        }

    def clear_chat_history(self):
        """
        清除对话历史
        
        【人C协作接口】：对话管理模块调用此方法清除历史记录
        """
        self.memory.clear()

    def get_chat_history(self):
        """
        获取对话历史
        
        返回：
            list: 对话历史记录
        
        【人C协作接口】：对话管理模块调用此方法获取历史记录
        数据格式：消息对象列表
        """
        return self.memory.chat_memory.messages

    def query_with_session(self, question, session_id=None):
        """
        【人C扩展方法】带会话管理的RAG查询
        
        参数：
            question (str): 用户问题
            session_id (str, optional): 会话ID，不提供则创建新会话
            
        返回：
            dict: 查询结果，包含answer、source_documents、session_id和formatted_sources
        
        设计思路：
            - 如果提供session_id，加载对应的对话历史
            - 如果未提供，创建新会话
            - 执行查询并保存对话消息到持久化存储
            - 返回包含会话信息的完整结果
        """
        # 如果提供了session_id，确保会话存在
        if session_id:
            if session_id not in chat_history_manager.session_index:
                chat_history_manager.create_session(session_id)
        else:
            # 创建新会话
            session_id = chat_history_manager.create_session()
        
        # 执行查询
        result = self.query_with_sources(question)
        
        # 保存用户消息和AI响应到对话历史
        chat_history_manager.add_message(
            session_id=session_id,
            role="user",
            content=question,
        )
        
        chat_history_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            source_documents=result["formatted_sources"],
        )
        
        # 返回包含会话信息的结果
        return {
            "session_id": session_id,
            "answer": result["answer"],
            "source_documents": result["source_documents"],
            "formatted_sources": result["formatted_sources"],
        }

    def load_session_history(self, session_id):
        """
        【人C扩展方法】加载会话历史到内存
        
        参数：
            session_id (str): 会话ID
            
        返回：
            bool: 是否加载成功
        
        设计思路：
            - 从chat_history_manager获取会话消息
            - 将消息加载到ConversationBufferMemory中
            - 恢复之前的对话上下文
        """
        if session_id not in chat_history_manager.session_index:
            return False
        
        # 获取会话消息
        messages = chat_history_manager.get_messages(session_id)
        
        if not messages:
            return False
        
        # 清空当前内存
        self.memory.clear()
        
        # 加载消息到内存
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "user":
                self.memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                self.memory.chat_memory.add_ai_message(content)
            elif role == "system":
                self.memory.chat_memory.add_system_message(content)
        
        return True

    def get_session_info(self, session_id):
        """
        【人C扩展方法】获取会话信息
        
        参数：
            session_id (str): 会话ID
            
        返回：
            dict or None: 会话信息字典，如果会话不存在返回None
        """
        return chat_history_manager.get_session_info(session_id)


rag_chain = RAGChain()
