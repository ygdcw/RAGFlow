import os
import sys
import json
import asyncio
import jwt
import time
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from config import config
from document_processor import document_processor
from vector_db import vector_db_service
from rag_chain import rag_chain
from chat_history_manager import chat_history_manager

app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)

# JWT配置
SECRET_KEY = "ragflow_secret_key_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# 模拟用户数据库
users_db = {
    "admin": {
        "id": "1",
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "status": "active",
        "created_at": "2026-01-01 00:00:00",
        "last_login": None,
    },
    "user": {
        "id": "2",
        "username": "user",
        "password": "user123",
        "role": "user",
        "status": "active",
        "created_at": "2026-01-01 00:00:00",
        "last_login": None,
    },
}

# 安全认证
security = HTTPBearer()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

from fastapi.responses import JSONResponse

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    return JSONResponse(
        content={"message": "CORS preflight allowed"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


# ========== 认证相关模型 ==========
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user: Dict[str, Any]


class UserInfo(BaseModel):
    id: str
    username: str
    role: str
    token: str


# ========== 认证工具函数 ==========
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前登录用户"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="未授权")
        
        user = users_db.get(username)
        if user is None or user["status"] != "active":
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="令牌无效")


async def get_current_admin_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取当前管理员用户"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ========== 通用响应格式 ==========
def success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    """成功响应"""
    return {"code": 200, "data": data, "message": message}


def error_response(message: str, code: int = 400) -> Dict[str, Any]:
    """错误响应"""
    return {"code": code, "data": None, "message": message}


# ========== 认证API ==========
@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """
    用户登录接口
    
    参数：
        request (LoginRequest): 包含username和password的请求体
    
    返回：
        LoginResponse: 包含用户信息的响应体
    """
    user = users_db.get(request.username)
    
    if user is None or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if user["status"] != "active":
        raise HTTPException(status_code=401, detail="用户已禁用")
    
    # 更新最后登录时间
    user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    
    return success_response({
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "token": access_token,
        }
    })


@app.post("/api/v1/auth/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    """
    用户登出接口
    """
    return success_response(message="登出成功")


@app.get("/api/v1/auth/me")
async def get_current_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取当前用户信息接口
    """
    return success_response({
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    })


# ========== 对话API ==========
@app.get("/api/v1/conversations")
async def get_conversation_list(user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取对话列表接口
    """
    sessions = chat_history_manager.list_sessions(limit=20)
    conversations = []
    for session in sessions:
        messages = chat_history_manager.get_messages(session["session_id"])
        title = ""
        if messages:
            first_user_msg = next((m for m in messages if m["role"] == "user"), None)
            title = first_user_msg["content"][:30] if first_user_msg else "新对话"
        conversations.append({
            "id": session["session_id"],
            "title": title,
            "created_at": session["created_at"],
        })
    return success_response({"items": conversations, "total": len(conversations), "page": 1, "page_size": 20})


@app.post("/api/v1/conversations")
async def create_conversation(user: Dict[str, Any] = Depends(get_current_user)):
    """
    创建新对话接口
    """
    session_id = chat_history_manager.create_session()
    return success_response({
        "id": session_id,
        "title": "新对话",
        "created_at": datetime.now().isoformat(),
    })


@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """
    删除对话接口
    """
    try:
        chat_history_manager.delete_session(conversation_id)
        return success_response(message="对话已删除")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取对话消息接口
    """
    messages = chat_history_manager.get_messages(conversation_id)
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "id": msg["message_id"],
            "conversation_id": conversation_id,
            "role": msg["role"],
            "content": msg["content"],
            "created_at": msg["created_at"],
        })
    return success_response({"items": formatted_messages, "total": len(formatted_messages), "page": 1, "page_size": 100})


# ========== 知识库API ==========
@app.get("/api/v1/knowledge-bases")
async def get_knowledge_bases(user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取知识库列表接口
    """
    collections = vector_db_service.get_collection_info()
    kb_list = []
    for name, info in collections.items():
        kb_list.append({
            "id": name,
            "name": info.get("category", name),
            "doc_count": info.get("document_count", 0),
            "created_at": datetime.now().isoformat(),
        })
    return success_response({"items": kb_list, "total": len(kb_list), "page": 1, "page_size": 20})


@app.post("/api/v1/knowledge-bases")
async def create_knowledge_base(name: str, user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    创建知识库接口（管理员权限）
    """
    try:
        vector_db_service.create_new_collection(name, category=name)
        return success_response({
            "id": name,
            "name": name,
            "doc_count": 0,
            "created_at": datetime.now().isoformat(),
        }, message="知识库创建成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str, user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    删除知识库接口（管理员权限）
    """
    try:
        vector_db_service.delete_collection(kb_id)
        return success_response(message="知识库已删除")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge-bases/{kb_id}/documents")
async def get_documents(kb_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """
    获取知识库文档列表接口
    """
    collections = vector_db_service.get_collection_info()
    if kb_id not in collections:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    docs = []
    doc_count = collections[kb_id].get("document_count", 0)
    for i in range(min(doc_count, 50)):
        docs.append({
            "id": f"{kb_id}_doc_{i}",
            "knowledge_base_id": kb_id,
            "filename": f"document_{i}.txt",
            "status": "ready",
            "created_at": datetime.now().isoformat(),
        })
    return success_response({"items": docs, "total": len(docs), "page": 1, "page_size": 50})


@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = "default",
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    上传文档接口
    
    普通用户可以上传文档到自己的知识库
    管理员可以上传到任何知识库
    """
    try:
        # 保存上传的文件
        file_path = os.path.join(os.path.dirname(__file__), "uploads", file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # 处理文档
        documents = document_processor.load_and_split([file_path])
        
        if user["role"] == "admin":
            doc_ids = vector_db_service.add_documents_to_collection(documents, knowledge_base_id)
        else:
            doc_ids = vector_db_service.add_documents(documents)
        
        # 清理临时文件
        os.remove(file_path)
        
        return success_response({
            "id": doc_ids[0] if doc_ids else "",
            "knowledge_base_id": knowledge_base_id,
            "filename": file.filename,
            "status": "ready",
            "created_at": datetime.now().isoformat(),
        }, message="文档上传成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/documents/{doc_id}")
async def delete_document(doc_id: str, user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    删除文档接口（管理员权限）
    """
    try:
        vector_db_service.clear_all_documents()
        return success_response(message="文档已删除")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 管理后台API ==========
@app.get("/api/v1/admin/users")
async def get_user_list(user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    获取用户列表（管理员权限）
    """
    admin_users = []
    for username, info in users_db.items():
        admin_users.append({
            "id": info["id"],
            "username": info["username"],
            "role": info["role"],
            "created_at": info["created_at"],
            "last_login": info["last_login"],
            "status": info["status"],
        })
    return success_response(admin_users)


@app.post("/api/v1/admin/users")
async def add_user(
    username: str,
    password: str,
    role: str = "user",
    user: Dict[str, Any] = Depends(get_current_admin_user),
):
    """
    添加用户（管理员权限）
    """
    if username in users_db:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_id = str(len(users_db) + 1)
    users_db[username] = {
        "id": new_id,
        "username": username,
        "password": password,
        "role": role,
        "status": "active",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": None,
    }
    
    return success_response({
        "id": new_id,
        "username": username,
        "role": role,
    }, message="用户添加成功")


@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: str, user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    删除用户（管理员权限）
    """
    if user_id == "1":
        raise HTTPException(status_code=400, detail="不能删除超级管理员")
    
    for username, info in list(users_db.items()):
        if info["id"] == user_id:
            del users_db[username]
            return success_response(message="用户已删除")
    
    raise HTTPException(status_code=404, detail="用户不存在")


@app.post("/api/v1/admin/users/{user_id}/toggle")
async def toggle_user_status(user_id: str, user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    切换用户状态（管理员权限）
    """
    if user_id == "1":
        raise HTTPException(status_code=400, detail="不能禁用超级管理员")
    
    for info in users_db.values():
        if info["id"] == user_id:
            info["status"] = "disabled" if info["status"] == "active" else "active"
            return success_response(message="状态已更新")
    
    raise HTTPException(status_code=404, detail="用户不存在")


@app.get("/api/v1/admin/knowledge-bases")
async def admin_get_knowledge_bases(user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    获取知识库列表（管理员权限）
    """
    collections = vector_db_service.get_collection_info()
    kb_list = []
    for name, info in collections.items():
        kb_list.append({
            "id": name,
            "name": info.get("category", name),
            "doc_count": info.get("document_count", 0),
            "owner": "admin",
            "created_at": datetime.now().isoformat(),
            "status": "active" if info.get("document_count", 0) > 0 else "empty",
        })
    return success_response(kb_list)


@app.get("/api/v1/admin/documents")
async def get_all_documents(user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    获取所有文档（管理员权限）
    """
    collections = vector_db_service.get_collection_info()
    docs = []
    for kb_name, info in collections.items():
        doc_count = info.get("document_count", 0)
        for i in range(min(doc_count, 20)):
            docs.append({
                "id": f"{kb_name}_doc_{i}",
                "filename": f"document_{i}.txt",
                "knowledge_base": kb_name,
                "size": "10KB",
                "status": "ready",
                "tags": [],
                "created_at": datetime.now().isoformat(),
            })
    return success_response(docs)


@app.post("/api/v1/admin/documents/reparse/{doc_id}")
async def reparse_document(doc_id: str, user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    重新解析文档（管理员权限）
    """
    return success_response(message="重新解析已触发")


@app.post("/api/v1/admin/documents/{doc_id}/tags")
async def update_document_tags(doc_id: str, tags: List[str], user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    更新文档标签（管理员权限）
    """
    return success_response(message="标签已更新")


@app.get("/api/v1/admin/stats")
async def get_system_stats(user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    获取系统统计信息（管理员权限）
    """
    collections = vector_db_service.get_collection_info()
    total_docs = sum(info.get("document_count", 0) for info in collections.values())
    
    return success_response({
        "total_users": len(users_db),
        "total_documents": total_docs,
        "total_questions": 0,
        "avg_response_time": 0.5,
        "cpu_usage": 25,
        "memory_usage": 45,
        "disk_usage": 30,
    })


@app.get("/api/v1/admin/logs")
async def get_operation_logs(user: Dict[str, Any] = Depends(get_current_admin_user)):
    """
    获取操作日志（管理员权限）
    """
    logs = [
        {
            "id": "1",
            "user": "admin",
            "action": "登录",
            "detail": "管理员登录系统",
            "created_at": datetime.now().isoformat(),
        }
    ]
    return success_response(logs)


# ========== 问答API ==========
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]


@app.post("/api/v1/chat")
async def chat(query: QueryRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """
    RAG问答接口（带会话管理）
    """
    if not query.question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    try:
        result = rag_chain.query_with_sources(query.question)
        return success_response({
            "answer": result["answer"],
            "sources": result["formatted_sources"],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SessionQueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


@app.post("/api/v1/chat/session")
async def chat_with_session(request: SessionQueryRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """
    带会话管理的RAG问答接口
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    try:
        result = rag_chain.query_with_session(request.question, request.conversation_id)
        return success_response({
            "conversation_id": result["session_id"],
            "answer": result["answer"],
            "sources": result["formatted_sources"],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi.responses import StreamingResponse

@app.post("/api/v1/chat/send")
async def chat_send(request: SessionQueryRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """
    SSE流式问答接口
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    async def generate():
        try:
            result = rag_chain.query_with_session(request.question, request.conversation_id)
            
            answer = result["answer"]
            sources = result["formatted_sources"]
            
            for i in range(0, len(answer), 20):
                chunk = answer[i:i+20]
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                await asyncio.sleep(0.05)
            
            if sources:
                yield f"data: {json.dumps({'type': 'sources', 'documents': sources})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ========== 健康检查和旧API兼容 ==========
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app_name": config.APP_NAME,
        "version": config.APP_VERSION,
    }


@app.get("/api/chat/sessions")
async def list_sessions_v1(limit: Optional[int] = 10):
    """兼容旧接口"""
    sessions = chat_history_manager.list_sessions(limit=limit)
    return {"sessions": sessions}


@app.get("/api/chat/sessions/{session_id}")
async def get_session_v1(session_id: str):
    """兼容旧接口"""
    session_info = chat_history_manager.get_session_info(session_id)
    if session_info is None:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    messages = chat_history_manager.get_messages(session_id)
    return {"session_info": session_info, "messages": messages}


@app.delete("/api/chat/sessions/{session_id}")
async def delete_session_v1(session_id: str):
    """兼容旧接口"""
    try:
        chat_history_manager.delete_session(session_id)
        return {"message": f"会话 {session_id} 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/chat/statistics")
async def get_chat_statistics_v1():
    """兼容旧接口"""
    stats = chat_history_manager.get_statistics()
    return stats


@app.delete("/api/chat/sessions")
async def clear_all_sessions_v1():
    """兼容旧接口"""
    chat_history_manager.clear_all_sessions()
    return {"message": "已清空所有会话"}


@app.get("/api/collections")
async def get_collections_v1():
    """兼容旧接口"""
    collections = vector_db_service.get_collection_info()
    return {"collections": collections}


@app.post("/api/collections")
async def create_collection_v1(collection_name: str, category: Optional[str] = None, description: str = ""):
    """兼容旧接口"""
    try:
        vector_db_service.create_new_collection(collection_name, category, description)
        return {"message": f"集合 {collection_name} 创建成功", "collection_name": collection_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/collections/{collection_name}")
async def delete_collection_v1(collection_name: str):
    """兼容旧接口"""
    try:
        vector_db_service.delete_collection(collection_name)
        return {"message": f"集合 {collection_name} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/upload_to_collection")
async def upload_documents_to_collection_v1(file_paths: List[str], collection_name: str = "default"):
    """兼容旧接口"""
    if not file_paths:
        raise HTTPException(status_code=400, detail="文件路径列表不能为空")
    
    try:
        documents = document_processor.load_and_split(file_paths)
        doc_ids = vector_db_service.add_documents_to_collection(documents, collection_name)
        return {
            "message": f"成功上传并处理 {len(file_paths)} 个文件到集合 {collection_name}",
            "document_count": len(doc_ids),
            "chunk_count": len(documents),
            "collection_name": collection_name,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/count")
async def get_document_count_v1():
    """兼容旧接口"""
    return {"count": vector_db_service.get_document_count()}


@app.delete("/api/documents/clear")
async def clear_documents_v1():
    """兼容旧接口"""
    vector_db_service.clear_all_documents()
    return {"message": "已清空所有文档"}


@app.post("/api/query")
async def query_v1(request: QueryRequest):
    """兼容旧接口"""
    if not request.question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    try:
        result = rag_chain.query_with_sources(request.question)
        return QueryResponse(
            answer=result["answer"],
            sources=result["formatted_sources"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


def run_cli():
    """命令行交互模式"""
    print(f"\n===== {config.APP_NAME} v{config.APP_VERSION} 命令行模式 =====")
    print("输入 'help' 查看命令列表")
    print("输入 'exit' 或 'quit' 退出")
    
    while True:
        try:
            command = input("\n请输入命令或问题： ").strip()
            
            if not command:
                continue
            
            if command.lower() in ["exit", "quit"]:
                print("退出程序...")
                break
            
            if command.lower() == "help":
                print("\n命令列表：")
                print("  help          - 显示帮助信息")
                print("  exit/quit     - 退出程序")
                print("  upload <文件> - 上传文档到知识库")
                print("  count         - 查看当前文档数量")
                print("  clear         - 清空知识库")
                print("  chat_clear    - 清除对话历史")
                print("  其他文本      - 作为问题进行问答")
                continue
            
            if command.lower().startswith("upload "):
                file_path = command[7:].strip()
                if not file_path:
                    print("请指定要上传的文件路径")
                    continue
                
                try:
                    documents = document_processor.load_and_split([file_path])
                    doc_ids = vector_db_service.add_documents(documents)
                    print(f"成功上传 {len(documents)} 个文档块")
                except FileNotFoundError:
                    print(f"文件不存在: {file_path}")
                except Exception as e:
                    print(f"上传失败: {str(e)}")
                continue
            
            if command.lower() == "count":
                count = vector_db_service.get_document_count()
                print(f"当前知识库文档数量: {count}")
                continue
            
            if command.lower() == "clear":
                confirm = input("确定要清空知识库吗？(y/n): ").strip().lower()
                if confirm == "y":
                    vector_db_service.clear_all_documents()
                    print("知识库已清空")
                else:
                    print("取消操作")
                continue
            
            if command.lower() == "chat_clear":
                rag_chain.clear_chat_history()
                print("对话历史已清除")
                continue
            
            result = rag_chain.query_with_sources(command)
            print(f"\nAI: {result['answer']}")
            
            if result["formatted_sources"]:
                print("\n参考片段:")
                for i, source in enumerate(result["formatted_sources"], 1):
                    print(f"  [{i}] {source['content']}")
        
        except KeyboardInterrupt:
            print("\n退出程序...")
            break
        except Exception as e:
            print(f"错误: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        run_cli()