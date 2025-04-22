

# Client README
管理员-服务器-客户端（从机 Windows系统）的指令和管理系统。用处在一个公网服务器创建一个管理器。客户端上线后会主动与服务器建立websocket连接，等待指令。管理员可以发送指令到指定客户端id，到服务器，服务器收到管理员发送的指令后通过websocket转发到从机，从机执行指令，通过专用的http的api返回执行结果到服务器，服务器再回传到管理员。
本文档中涉及的三方如下：

1. **管理员**：（内网）通过浏览器访问服务器管理页面，向从机下发指令。
2. **服务器**：（公网）负责提供管理页面（前后端分离），并通过 RESTful API 和 WebSocket 与客户端通讯。
3. **客户端**：（内网）Windows从机，与服务器建立 WebSocket 及 HTTP 连接，执行（管理员）服务器下发的命令，并通过 HTTP 接口返回执行结果。


## 1. 通讯架构

- **WebSocket 通讯**  
  客户端与服务器建立 WebSocket 连接（仅用于服务器向客户端下发命令）。服务器将命令（例如：`cmd`、`screenshot`、`restart_cmd` 等）推送到客户端。

- **HTTP API 通讯**  
  客户端将命令执行结果或其他上报数据通过 HTTP POST 请求发送到服务器。例如：
  - 上报当前 CMD 窗口内容（通过 `/api/client/cmd_page_update`）
  - 上传截屏数据（通过 `/api/client/screenshot`）
  - 文件操作结果（通过 `/api/client/file_result`）

---

## 2. 客户端注册

- **注册 API**  
  **URL**: `GET /api/client/reg`  
  **描述**: 客户端初次启动时调用此接口注册自己。  
  **返回数据格式**:
  ```json
  {
      "status": "success",
      "client_id": "<generated_client_id>",
      "hash": "<generated_hash>",
      "ip": "<client_ip>"
  }
  ```
  客户端注册后，保存返回的 `client_id` 和 `hash` 以便后续通讯使用。

---

## 3. WebSocket 连接

- **WebSocket URL**  
  **URL 格式**: `ws://<SERVER_ADDR>/api/client/ws?client_id=<client_id>&hash=<hash>`  
  **说明**:  
  - 客户端建立 WebSocket 连接时需要在 URL 查询参数中传入 `client_id` 和 `hash`。
  - 服务器对这些参数进行验证，验证成功后，WebSocket 连接仅用于下发命令。

- **服务器下发的命令格式**  
  服务器通过 WebSocket 向客户端下发的命令数据格式为 JSON，例如：
  ```json
  {
      "commands": [
          {"name": "cmd", "value": "dir C:\\"},
          {"name": "screenshot", "value": ""},
          {"name": "restart_cmd", "value": ""},
          {"name": "refresh_cmd", "value": ""}
      ]
  }
  ```
  **命令说明**:
  - `cmd`：执行命令行指令。客户端收到后需要在本地 CMD 环境中执行该命令。
  - `screenshot`：指示客户端进行截屏操作。客户端应捕获屏幕并通过 HTTP 接口上报截屏图片。
  - `restart_cmd`：要求客户端重启其 CMD 进程。
  - `refresh_cmd`：要求客户端主动上报最新的 CMD 输出。客户端收到该命令后，需要调用 HTTP API（例如 `/api/client/cmd_page_update`）上传最新的 CMD 内容。

---

## 4. 客户端上报 API

客户端上报数据使用标准 HTTP POST 请求，数据格式均为 JSON。

### 4.1 上报 CMD 页面

- **URL**: `POST /api/client/cmd_page_update`  
- **请求数据格式**:
  ```json
  {
      "client_id": "<client_id>",
      "cmd_page": "<完整的CMD窗口文本>"
  }
  ```
- **返回**:  
  如果成功，则返回类似：
  ```json
  {
      "status": "success",
      "message": "cmd_page updated successfully"
  }
  ```

### 4.2 上传截屏

- **URL**: `POST /api/client/screenshot`  
- **请求数据格式**:
  ```json
  {
      "client_id": "<client_id>",
      "screenshot": "<截屏图片的Base64编码字符串>"
  }
  ```
- **返回**:  
  成功时返回：
  ```json
  {
      "status": "success",
      "filename": ""
  }
  ```

## 5. 客户端通讯摘要

- **注册**  
  客户端启动后调用 `/api/client/reg` 注册，并保存返回的 `client_id` 与 `hash`。

- **WebSocket 连接**  
  客户端通过 WebSocket 建立连接：  
  `ws://<SERVER_ADDR>/api/client/ws?client_id=<client_id>&hash=<hash>`  
  *注意：该连接仅用于服务器向客户端下发命令（例如 `cmd`、`screenshot`、`restart_cmd`、`refresh_cmd` 等）。*

- **上报数据**  
  客户端通过 HTTP POST 接口上报数据：  
  - **CMD 输出**：调用 `/api/client/cmd_page_update` 提交最新的 CMD 窗口内容。  
  - **截屏**：调用 `/api/client/screenshot` 上传截屏（Base64 编码）。  
  - **文件操作结果**：调用 `/api/client/file_result` 上传文件相关操作结果。

- **命令格式**  
  服务器下发的命令格式统一为 JSON：
  ```json
  {
      "commands": [
          {"name": "cmd", "value": "<命令文本>"},
          {"name": "restart_cmd", "value": ""},
          {"name": "screenshot", "value": ""},
          {"name": "refresh_cmd", "value": ""}
      ]
  }
  ```
  客户端收到命令后，应根据命令名称执行相应操作，并在完成后通过相应 HTTP API 上报结果。

---
