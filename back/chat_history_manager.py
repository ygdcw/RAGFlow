import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from config import config


class ChatHistoryManager:
    """
    对话历史管理类
    【人C负责】：对话历史持久化、查询、统计和管理
    
    功能特性：
    1. 会话管理：创建、查询、删除会话
    2. 消息持久化：将对话消息保存到文件系统
    3. 历史查询：支持按会话ID、时间范围查询对话历史
    4. 统计分析：提供对话数量、消息数量等统计信息
    5. 消息清理：支持清理过期或超出限制的对话
    
    协作需求：
    - 【人A】RAG链模块调用此类保存和加载对话历史
    - 【人D】前端模块调用此类查询对话历史
    - 【人C】需确保与向量数据库模块的数据一致性
    """

    def __init__(self):
        """
        初始化对话历史管理器
        """
        self.persist_directory = config.CHAT_HISTORY_PERSIST_DIR
        self.max_messages = config.CHAT_HISTORY_MAX_MESSAGES
        self.max_sessions = config.CHAT_HISTORY_MAX_SESSIONS
        
        # 确保持久化目录存在
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # 会话索引（内存缓存，加速查询）
        self.session_index: Dict[str, dict] = {}
        self._load_session_index()

    def _load_session_index(self):
        """
        加载会话索引
        
        从persist_directory读取所有会话目录，构建索引
        索引格式：{session_id: {"created_at": datetime, "message_count": int}}
        """
        try:
            index_file = os.path.join(self.persist_directory, "index.json")
            if os.path.exists(index_file):
                with open(index_file, "r", encoding="utf-8") as f:
                    self.session_index = json.load(f)
        except Exception as e:
            print(f"加载会话索引失败: {str(e)}")
            self.session_index = {}

    def _save_session_index(self):
        """
        保存会话索引到文件
        
        将内存中的会话索引序列化并保存到index.json文件
        """
        try:
            index_file = os.path.join(self.persist_directory, "index.json")
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(self.session_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存会话索引失败: {str(e)}")

    def create_session(self, session_id: str = None, user_id: str = None) -> str:
        """
        创建新会话
        
        参数：
            session_id (str, optional): 会话ID，不提供则自动生成
            user_id (str, optional): 用户ID，用于会话隔离
            
        返回：
            str: 会话ID
        
        【人A协作接口】：RAG链模块调用此方法创建新会话
        数据格式：字符串会话ID
        
        设计思路：
            - 如果提供session_id，检查是否已存在
            - 如果未提供，生成UUID作为会话ID
            - 创建会话目录用于存储消息文件
            - 记录用户ID用于会话隔离
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id in self.session_index:
            raise ValueError(f"会话 {session_id} 已存在")
        
        session_dir = os.path.join(self.persist_directory, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        now = datetime.now().isoformat()
        self.session_index[session_id] = {
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "user_id": user_id,
        }
        
        self._save_session_index()
        return session_id

    def add_message(self, session_id: str, role: str, content: str, source_documents: list = None):
        """
        向会话添加消息
        
        参数：
            session_id (str): 会话ID
            role (str): 消息角色，支持"user"、"assistant"、"system"
            content (str): 消息内容
            source_documents (list, optional): 来源文档信息
            
        【人A协作接口】：RAG链模块调用此方法保存对话消息
        数据格式：
            - role: "user" | "assistant" | "system"
            - content: 消息文本
            - source_documents: 包含content和metadata的字典列表
        
        设计思路：
            - 检查会话是否存在，不存在则创建
            - 构建消息对象，包含时间戳和来源信息
            - 将消息追加到会话的消息文件中
            - 更新会话索引中的消息计数
        """
        # 如果会话不存在，创建新会话
        if session_id not in self.session_index:
            self.create_session(session_id)
        
        # 构建消息对象
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "source_documents": source_documents or [],
        }
        
        # 保存消息到文件
        session_dir = os.path.join(self.persist_directory, session_id)
        messages_file = os.path.join(session_dir, "messages.json")
        
        try:
            if os.path.exists(messages_file):
                with open(messages_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            else:
                messages = []
            
            # 检查消息数量限制
            if len(messages) >= self.max_messages:
                messages = messages[-self.max_messages + 1:]
            
            messages.append(message)
            
            with open(messages_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self.session_index[session_id]["message_count"] = len(messages)
            self.session_index[session_id]["updated_at"] = datetime.now().isoformat()
            self._save_session_index()
            
        except Exception as e:
            raise RuntimeError(f"保存消息失败: {str(e)}") from e

    def get_messages(self, session_id: str, limit: int = None) -> List[dict]:
        """
        获取会话的消息列表
        
        参数：
            session_id (str): 会话ID
            limit (int, optional): 返回消息数量限制
            
        返回：
            List[dict]: 消息列表
        
        【人A协作接口】：RAG链模块调用此方法加载对话历史
        【人D协作接口】：前端模块调用此方法显示对话历史
        数据格式：消息字典列表，包含id、role、content、timestamp、source_documents
        """
        if session_id not in self.session_index:
            return []
        
        session_dir = os.path.join(self.persist_directory, session_id)
        messages_file = os.path.join(session_dir, "messages.json")
        
        try:
            if not os.path.exists(messages_file):
                return []
            
            with open(messages_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            
            if limit is not None:
                messages = messages[-limit:]
            
            return messages
        except Exception as e:
            raise RuntimeError(f"获取消息失败: {str(e)}") from e

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        获取会话信息
        
        参数：
            session_id (str): 会话ID
            
        返回：
            Optional[dict]: 会话信息字典，如果会话不存在返回None
        
        【人D协作接口】：前端模块调用此方法获取会话详情
        数据格式：包含session_id、created_at、updated_at、message_count
        """
        if session_id not in self.session_index:
            return None
        
        return {
            "session_id": session_id,
            **self.session_index[session_id],
        }

    def list_sessions(self, limit: int = None, order_by: str = "updated_at", user_id: str = None) -> List[dict]:
        """
        获取会话列表
        
        参数：
            limit (int, optional): 返回会话数量限制
            order_by (str): 排序字段，支持"created_at"、"updated_at"、"message_count"
            user_id (str, optional): 用户ID，用于过滤用户专属会话
            
        返回：
            List[dict]: 会话信息列表
        
        【人D协作接口】：前端模块调用此方法获取会话列表
        数据格式：会话信息字典列表，按指定字段排序
        
        设计思路：
            - 根据user_id参数过滤用户专属会话
            - 根据order_by参数选择排序字段
            - 按降序排列（最新的在前面）
            - 应用limit限制返回数量
        """
        sessions = []
        for session_id, info in self.session_index.items():
            if user_id is not None and info.get("user_id") != user_id:
                continue
            sessions.append({
                "session_id": session_id,
                **info,
            })
        
        if order_by in ["created_at", "updated_at", "message_count"]:
            sessions.sort(key=lambda x: x.get(order_by, ""), reverse=True)
        
        if limit is not None:
            sessions = sessions[:limit]
        
        return sessions

    def get_session_user_id(self, session_id: str) -> str:
        """
        获取会话所属用户ID
        
        参数：
            session_id (str): 会话ID
            
        返回：
            str: 用户ID，如果会话不存在或未设置用户ID返回None
        """
        if session_id not in self.session_index:
            return None
        return self.session_index[session_id].get("user_id")

    def delete_session(self, session_id: str):
        """
        删除会话
        
        参数：
            session_id (str): 会话ID
            
        【人D协作接口】：前端模块调用此方法删除会话
        数据格式：字符串会话ID
        
        设计思路：
            - 从索引中删除会话信息
            - 删除会话目录及其所有文件
        """
        if session_id not in self.session_index:
            raise ValueError(f"会话 {session_id} 不存在")
        
        # 从索引中删除
        del self.session_index[session_id]
        self._save_session_index()
        
        # 删除会话目录
        session_dir = os.path.join(self.persist_directory, session_id)
        if os.path.exists(session_dir):
            import shutil
            shutil.rmtree(session_dir)

    def clear_all_sessions(self):
        """
        清空所有会话
        
        警告：此操作不可逆，请谨慎使用
        """
        # 清空索引
        self.session_index = {}
        self._save_session_index()
        
        # 删除所有会话目录
        for item in os.listdir(self.persist_directory):
            item_path = os.path.join(self.persist_directory, item)
            if os.path.isdir(item_path) and item != "__pycache__":
                import shutil
                shutil.rmtree(item_path)

    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        返回：
            dict: 统计信息字典
        
        【人D协作接口】：前端模块调用此方法获取系统统计
        数据格式：包含session_count、total_message_count、storage_usage等
        
        设计思路：
            - 计算会话总数
            - 计算消息总数
            - 计算存储使用量
            - 计算平均每会话消息数
        """
        session_count = len(self.session_index)
        total_message_count = sum(info.get("message_count", 0) for info in self.session_index.values())
        
        # 计算存储使用量
        storage_usage = 0
        for session_id in self.session_index:
            session_dir = os.path.join(self.persist_directory, session_id)
            if os.path.exists(session_dir):
                for file in os.listdir(session_dir):
                    file_path = os.path.join(session_dir, file)
                    if os.path.isfile(file_path):
                        storage_usage += os.path.getsize(file_path)
        
        # 转换为更易读的单位
        if storage_usage < 1024:
            storage_str = f"{storage_usage} B"
        elif storage_usage < 1024 * 1024:
            storage_str = f"{storage_usage / 1024:.2f} KB"
        else:
            storage_str = f"{storage_usage / (1024 * 1024):.2f} MB"
        
        avg_messages_per_session = total_message_count / session_count if session_count > 0 else 0
        
        return {
            "session_count": session_count,
            "total_message_count": total_message_count,
            "avg_messages_per_session": round(avg_messages_per_session, 2),
            "storage_usage": storage_str,
            "max_sessions_limit": self.max_sessions,
            "max_messages_limit": self.max_messages,
        }

    def cleanup_old_sessions(self, days_to_keep: int = 30):
        """
        清理过期会话
        
        参数：
            days_to_keep (int): 保留天数，超过此天数的会话将被清理
            
        【人C维护接口】：定期任务调用此方法清理过期会话
        数据格式：整数天数
        
        设计思路：
            - 遍历所有会话，检查更新时间
            - 删除超过保留天数的会话
            - 返回被清理的会话数量
        """
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        sessions_to_delete = []
        for session_id, info in self.session_index.items():
            updated_at = info.get("updated_at", "")
            try:
                updated_timestamp = datetime.fromisoformat(updated_at).timestamp()
                if updated_timestamp < cutoff_date:
                    sessions_to_delete.append(session_id)
            except ValueError:
                continue
        
        for session_id in sessions_to_delete:
            self.delete_session(session_id)
            deleted_count += 1
        
        return deleted_count

    def export_session(self, session_id: str, export_path: str = None) -> str:
        """
        导出会话数据
        
        参数：
            session_id (str): 会话ID
            export_path (str, optional): 导出路径，不提供则使用默认路径
            
        返回：
            str: 导出文件路径
        
        【人D协作接口】：前端模块调用此方法导出会话数据
        数据格式：JSON文件路径
        
        设计思路：
            - 获取会话的所有消息
            - 将消息和会话信息导出为JSON文件
            - 支持自定义导出路径
        """
        if session_id not in self.session_index:
            raise ValueError(f"会话 {session_id} 不存在")
        
        if export_path is None:
            export_path = os.path.join(
                self.persist_directory,
                f"export_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
        
        session_info = self.get_session_info(session_id)
        messages = self.get_messages(session_id)
        
        export_data = {
            "session_info": session_info,
            "messages": messages,
            "export_time": datetime.now().isoformat(),
        }
        
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return export_path


chat_history_manager = ChatHistoryManager()
