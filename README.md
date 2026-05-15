# File Transfer Web

<p align="center">
  <strong>Simple Web-Based File Transfer Between Devices on Local Network</strong><br>
  通过局域网站在设备间轻松传输文件
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue" alt="Language">
  <img src="https://img.shields.io/badge/Framework-http.server-green" alt="Framework">
  <img src="https://img.shields.io/badge/Platform-Cross--Platform-brightgreen" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## 🚀 Features | 特性

### English
- **Web-based Transfer**: Transfer files between devices using any web browser
- **Real-time Progress**: Visual upload progress bars with percentage
- **Upload History**: Track all uploaded files with timestamps and sizes
- **Multi-file Support**: Upload multiple files at once
- **Drag & Drop**: Intuitive drag-and-drop interface
- **Auto IP Detection**: Automatically detects local network IP address
- **File Management**: Download, delete individual files, or clear all records
- **Zero Dependencies**: Pure Python standard library implementation

### 中文
- **网页传输**：使用任意浏览器在设备间传输文件
- **实时进度**：可视化上传进度条及百分比
- **上传记录**：追踪所有上传文件的时间戳和大小
- **多文件支持**：一次性上传多个文件
- **拖拽上传**：直观的拖放界面
- **自动IP检测**：自动检测局域网IP地址
- **文件管理**：下载、删除单个文件或清除所有记录
- **零依赖**：纯Python标准库实现

---

## 📋 Requirements | 系统要求

### English
- Python 3.6+
- Any modern web browser (Chrome, Firefox, Safari, Edge)

### 中文
- Python 3.6+
- 任一现代浏览器（Chrome、Firefox、Safari、Edge）

---

## 🛠️ Usage | 使用方法

### English
```bash
# Start the server (default port 8000)
./server.sh start

# Custom port
./server.sh start 9000

# Check status
./server.sh status

# Restart
./server.sh restart

# Stop
./server.sh stop
```

### 中文
```bash
# 启动服务（默认端口 8000）
./server.sh start

# 自定义端口
./server.sh start 9000

# 查看状态
./server.sh status

# 重启服务
./server.sh restart

# 停止服务
./server.sh stop
```

---

## 📱 How to Use | 使用方法

### English
1. Run the server on the target device
2. Access the displayed URL from any device on the same network
3. Select or drag files to upload
4. Monitor upload progress in real-time
5. Manage uploaded files through the history panel

### 中文
1. 在目标设备上运行服务器
2. 在同网段的任一设备上访问显示的网址
3. 选择或拖拽文件上传
4. 实时监控上传进度
5. 通过历史面板管理上传文件

---

## 🗂️ Directory Structure | 目录结构

```
file-transfer-web/
├── upload_server.py         # Main server application | 主服务器程序
├── server.sh                # Server management script | 服务器管理脚本
├── data/                    # Auto-generated data directory | 自动生成的数据目录
│   ├── uploads/             # Storage for uploaded files | 上传文件存储目录
│   └── upload.db            # Upload records database | 上传记录数据库
├── LICENSE                  # MIT License | 许可证
└── README.md                # Documentation | 文档
```

---

## 🔧 Technical Implementation | 技术实现

### English
- **Backend**: Python HTTP server using standard library
- **Frontend**: Pure HTML/CSS/JavaScript, no external dependencies
- **Progress Tracking**: XMLHttpRequest upload events with real-time updates
- **Data Storage**: SQLite database for upload history
- **File Handling**: Safe file operations with duplicate prevention
- **Path Management**: Dynamic path resolution relative to script location

### 中文
- **后端**: Python HTTP 服务器，使用标准库
- **前端**: 纯 HTML/CSS/JavaScript，无外部依赖
- **进度跟踪**: XMLHttpRequest 上传事件，实时更新
- **数据存储**: SQLite 数据库存储上传历史
- **文件处理**: 安全文件操作，防止重复覆盖
- **路径管理**: 动态路径解析，相对脚本位置

---

## 📊 Performance | 性能表现

### English
- Successfully tested with files up to 10GB
- Upload speeds up to 1.4GB/s on local networks
- Handles multiple simultaneous uploads
- Efficient memory usage with streaming transfers

### 中文
- 成功测试高达 10GB 的文件
- 局域网上传速度最高可达 1.4GB/s
- 支持多并发上传
- 流式传输，高效内存使用

---

## 🛡️ Security | 安全性

### English
- Local network only access (no external connections)
- No authentication required (intended for trusted networks)
- Files stored locally on the server machine
- No cloud storage or external services

### 中文
- 仅限局域网访问（无外网连接）
- 无需身份验证（适用于受信任网络）
- 文件存储在服务器本地
- 无云存储或外部服务

---

## 🤝 Contributing | 贡献

### English
Contributions are welcome! Please feel free to submit a Pull Request. For major changes, open an issue first to discuss what you would like to change.

### 中文
欢迎贡献！请随时提交拉取请求。对于重大更改，请先开 issue 讨论您想要修改的内容。

---

## 📄 License | 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。