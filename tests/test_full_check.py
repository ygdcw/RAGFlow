import os
import sys
import requests

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
BACK_DIR = os.path.join(os.path.dirname(TEST_DIR), "back")
sys.path.insert(0, BACK_DIR)

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("          前后端连接状态全面检查")
print("=" * 80)

results = []

def add_result(category, item, status, details=""):
    results.append({
        "category": category,
        "item": item,
        "status": status,
        "details": details
    })

# ========== 1. 网络连接状态验证 ==========
print("\n【1】网络连接状态验证")
print("-" * 60)

try:
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    if r.status_code == 200:
        add_result("网络连接", "后端服务可达性", "✓ 通过", f"状态码: {r.status_code}, 响应时间: {r.elapsed.total_seconds():.2f}s")
        print(f"✓ 后端服务可达 (http://localhost:8000)")
    else:
        add_result("网络连接", "后端服务可达性", "✗ 失败", f"状态码: {r.status_code}")
        print(f"✗ 后端服务响应异常: {r.status_code}")
except requests.ConnectionError:
    add_result("网络连接", "后端服务可达性", "✗ 失败", "连接拒绝，后端服务未启动")
    print(f"✗ 连接失败：后端服务未启动")
except Exception as e:
    add_result("网络连接", "后端服务可达性", "✗ 失败", str(e))
    print(f"✗ 网络错误: {e}")

# ========== 2. API接口调用测试 ==========
print("\n【2】API接口调用测试")
print("-" * 60)

endpoints = [
    ("GET", "/health", "健康检查接口", {}),
    ("POST", "/api/v1/auth/login", "登录接口", {"username": "admin", "password": "admin123"}),
]

for method, endpoint, description, data in endpoints:
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            r = requests.get(url, timeout=10)
        else:
            r = requests.post(url, json=data, timeout=10)
        
        if r.status_code in [200, 201]:
            add_result("API接口", description, "✓ 通过", f"状态码: {r.status_code}")
            print(f"✓ {description} ({method} {endpoint}) - 状态码: {r.status_code}")
        else:
            add_result("API接口", description, "✗ 失败", f"状态码: {r.status_code}, 响应: {r.text[:100]}")
            print(f"✗ {description} ({method} {endpoint}) - 状态码: {r.status_code}")
    except Exception as e:
        add_result("API接口", description, "✗ 失败", str(e))
        print(f"✗ {description} ({method} {endpoint}) - 错误: {e}")

# 获取管理员token用于后续测试
admin_token = None
try:
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    if r.status_code == 200:
        data = r.json()
        admin_token = data.get("data", {}).get("user", {}).get("token")
        add_result("API接口", "获取管理员Token", "✓ 通过", "Token获取成功")
        print(f"✓ 管理员Token获取成功")
    else:
        add_result("API接口", "获取管理员Token", "✗ 失败", f"状态码: {r.status_code}")
except Exception as e:
    add_result("API接口", "获取管理员Token", "✗ 失败", str(e))

# 获取普通用户token
user_token = None
try:
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": "user", "password": "user123"}, timeout=10)
    if r.status_code == 200:
        data = r.json()
        user_token = data.get("data", {}).get("user", {}).get("token")
        add_result("API接口", "获取普通用户Token", "✓ 通过", "Token获取成功")
        print(f"✓ 普通用户Token获取成功")
    else:
        add_result("API接口", "获取普通用户Token", "✗ 失败", f"状态码: {r.status_code}")
except Exception as e:
    add_result("API接口", "获取普通用户Token", "✗ 失败", str(e))

# 测试需要认证的接口
auth_endpoints = [
    ("GET", "/api/v1/auth/me", "获取当前用户信息", "admin"),
    ("GET", "/api/v1/conversations", "获取对话列表", "admin"),
    ("GET", "/api/v1/knowledge-bases", "获取知识库列表", "admin"),
    ("GET", "/api/v1/admin/users", "获取用户列表(管理员)", "admin"),
    ("GET", "/api/v1/admin/users", "获取用户列表(普通用户)", "user"),
]

headers_admin = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
headers_user = {"Authorization": f"Bearer {user_token}"} if user_token else {}

for method, endpoint, description, role in auth_endpoints:
    try:
        url = f"{BASE_URL}{endpoint}"
        headers = headers_admin if role == "admin" else headers_user
        
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, headers=headers, timeout=10)
        
        expected_status = 200 if (role == "admin" or "admin" not in endpoint) else 403
        if r.status_code == expected_status:
            add_result("API接口", f"{description}({role})", "✓ 通过", f"状态码: {r.status_code}")
            print(f"✓ {description}({role}) - 状态码: {r.status_code}")
        else:
            add_result("API接口", f"{description}({role})", "✗ 失败", f"预期: {expected_status}, 实际: {r.status_code}")
            print(f"✗ {description}({role}) - 预期: {expected_status}, 实际: {r.status_code}")
    except Exception as e:
        add_result("API接口", f"{description}({role})", "✗ 失败", str(e))
        print(f"✗ {description}({role}) - 错误: {e}")

# ========== 3. 数据库连接状态确认 ==========
print("\n【3】数据库连接状态确认")
print("-" * 60)

try:
    from vector_db import vector_db_service
    
    doc_count = vector_db_service.get_document_count()
    collections = vector_db_service.get_collection_info()
    
    add_result("数据库", "向量数据库连接", "✓ 通过", f"文档数量: {doc_count}, 集合数量: {len(collections)}")
    print(f"✓ 向量数据库连接正常")
    print(f"  - 当前文档数量: {doc_count}")
    print(f"  - 集合列表: {list(collections.keys())}")
except Exception as e:
    add_result("数据库", "向量数据库连接", "✗ 失败", str(e))
    print(f"✗ 向量数据库连接失败: {e}")

# ========== 4. 前后端数据传输格式一致性检查 ==========
print("\n【4】前后端数据传输格式一致性检查")
print("-" * 60)

try:
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    response = r.json()
    
    expected_fields = ["code", "data", "message"]
    has_all_fields = all(field in response for field in expected_fields)
    
    if has_all_fields and response["code"] == 200:
        add_result("数据格式", "统一响应格式", "✓ 通过", f"包含字段: {expected_fields}")
        print(f"✓ 统一响应格式正确")
        print(f"  - code: {response['code']}")
        print(f"  - data: {type(response['data']).__name__}")
        print(f"  - message: {response['message']}")
    else:
        add_result("数据格式", "统一响应格式", "✗ 失败", f"缺少字段或code错误")
        print(f"✗ 响应格式不符合预期")
except Exception as e:
    add_result("数据格式", "统一响应格式", "✗ 失败", str(e))
    print(f"✗ 数据格式检查失败: {e}")

# ========== 5. CORS配置验证 ==========
print("\n【5】CORS配置验证")
print("-" * 60)

try:
    # 测试OPTIONS预检请求（携带Origin头）
    r = requests.options(f"{BASE_URL}/api/v1/auth/login", headers={"Origin": "http://localhost:3000"}, timeout=10)
    
    cors_headers = [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers",
    ]
    
    missing_headers = [h for h in cors_headers if h not in r.headers]
    
    if not missing_headers:
        add_result("CORS", "OPTIONS预检响应", "✓ 通过", "所有CORS头齐全")
        print(f"✓ OPTIONS预检响应正常")
        for h in cors_headers:
            print(f"  - {h}: {r.headers.get(h)}")
    else:
        add_result("CORS", "OPTIONS预检响应", "✗ 失败", f"缺少头: {missing_headers}, 状态码: {r.status_code}")
        print(f"✗ 缺少CORS头: {missing_headers}, 状态码: {r.status_code}")
        print(f"  所有响应头: {dict(r.headers)}")
except Exception as e:
    add_result("CORS", "OPTIONS预检响应", "✗ 失败", str(e))
    print(f"✗ CORS检查失败: {e}")

# ========== 6. 身份验证与授权机制测试 ==========
print("\n【6】身份验证与授权机制测试")
print("-" * 60)

# 测试无token访问需要认证的接口
try:
    r = requests.get(f"{BASE_URL}/api/v1/auth/me", timeout=10)
    if r.status_code == 401:
        add_result("认证授权", "无token访问受保护接口", "✓ 通过", "正确返回401")
        print(f"✓ 无token访问受保护接口返回401")
    else:
        add_result("认证授权", "无token访问受保护接口", "✗ 失败", f"状态码: {r.status_code}")
        print(f"✗ 无token访问受保护接口状态码异常: {r.status_code}")
except Exception as e:
    add_result("认证授权", "无token访问受保护接口", "✗ 失败", str(e))

# 测试普通用户访问管理员接口
if user_token:
    try:
        r = requests.get(f"{BASE_URL}/api/v1/admin/users", headers={"Authorization": f"Bearer {user_token}"}, timeout=10)
        if r.status_code == 403:
            add_result("认证授权", "普通用户访问管理员接口", "✓ 通过", "正确返回403")
            print(f"✓ 普通用户访问管理员接口返回403")
        else:
            add_result("认证授权", "普通用户访问管理员接口", "✗ 失败", f"状态码: {r.status_code}")
            print(f"✗ 普通用户访问管理员接口状态码异常: {r.status_code}")
    except Exception as e:
        add_result("认证授权", "普通用户访问管理员接口", "✗ 失败", str(e))

# 测试无效token
try:
    r = requests.get(f"{BASE_URL}/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}, timeout=10)
    if r.status_code == 401:
        add_result("认证授权", "无效token访问", "✓ 通过", "正确返回401")
        print(f"✓ 无效token访问返回401")
    else:
        add_result("认证授权", "无效token访问", "✗ 失败", f"状态码: {r.status_code}")
        print(f"✗ 无效token访问状态码异常: {r.status_code}")
except Exception as e:
    add_result("认证授权", "无效token访问", "✗ 失败", str(e))

# ========== 7. 错误处理测试 ==========
print("\n【7】错误处理测试")
print("-" * 60)

# 测试登录失败
try:
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={"username": "admin", "password": "wrong"}, timeout=10)
    if r.status_code == 401:
        add_result("错误处理", "登录失败处理", "✓ 通过", "正确返回401")
        print(f"✓ 登录失败返回401")
    else:
        add_result("错误处理", "登录失败处理", "✗ 失败", f"状态码: {r.status_code}")
        print(f"✗ 登录失败状态码异常: {r.status_code}")
except Exception as e:
    add_result("错误处理", "登录失败处理", "✗ 失败", str(e))

# 测试参数错误
try:
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json={}, timeout=10)
    if r.status_code in [400, 422]:
        add_result("错误处理", "参数缺失处理", "✓ 通过", "正确返回错误状态码")
        print(f"✓ 参数缺失返回错误状态码: {r.status_code}")
    else:
        add_result("错误处理", "参数缺失处理", "✗ 失败", f"状态码: {r.status_code}")
        print(f"✗ 参数缺失状态码异常: {r.status_code}")
except Exception as e:
    add_result("错误处理", "参数缺失处理", "✗ 失败", str(e))

# ========== 总结报告 ==========
print("\n" + "=" * 80)
print("          检查结果总结")
print("=" * 80)

passed = [r for r in results if r["status"] == "✓ 通过"]
failed = [r for r in results if r["status"] == "✗ 失败"]

print(f"\n✓ 通过: {len(passed)} / {len(results)}")
print(f"✗ 失败: {len(failed)} / {len(results)}")

if failed:
    print("\n失败项详情:")
    for item in failed:
        print(f"  • [{item['category']}] {item['item']}: {item['details']}")

if len(passed) == len(results):
    print("\n✓✓✓ 所有检查项通过，系统状态正常！")
else:
    print(f"\n✗✗✗ 有 {len(failed)} 项检查失败，请检查相关配置")

print("\n" + "=" * 80)