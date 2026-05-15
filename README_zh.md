# TOOL-File-Transfer-Web

<p align="center">
  <strong>局域网站设备间文件传输工具</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue" alt="语言">
  <img src="https://img.shields.io/badge/Framework-http.server-green" alt="框架">
  <img src="https://img.shields.io/badge/Platform-跨平台-brightgreen" alt="平台">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="许可证">
</p>

---

<p align="center">
  <a href="./README_zh.md">中文文档</a> | <a href="./README.md">English Document</a>
</p>

---

## 🚀 功能特性

- **网页传输**：使用任意浏览器在设备间传输文件
- **实时进度**：可视化上传进度条及百分比
- **上传记录**：追踪所有上传文件的时间戳和大小
- **多文件支持**：一次性上传多个文件
- **拖拽上传**：直观的拖放界面
- **自动IP检测**：自动检测局域网IP地址
- **文件管理**：下载、删除单个文件或清除所有记录
- **零依赖**：纯Python标准库实现

## 📋 系统要求

- Python 3.6+
- 任一现代浏览器（Chrome、Firefox、Safari、Edge）

## 🛠️ 使用方法

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

## 📱 使用步骤

1. 在目标设备上运行服务器
2. 在同网段的任一设备上访问显示的网址
3. 选择或拖拽文件上传
4. 实时监控上传进度
5. 通过历史面板管理上传文件

## 🗂️ 目录结构

```
TOOL-File-Transfer-Web/
├── upload_server.py         # 主服务器程序
├── server.sh                # 服务器管理脚本
├── data/                    # 自动生成的数据目录
│   ├── uploads/             # 上传文件存储目录
│   └── upload.db            # 上传记录数据库
├── LICENSE                  # 许可证
└── README.md                # 英文文档
└── README_zh.md             # 中文文档
```

## 🔧 技术实现

- **后端**: Python HTTP 服务器，使用标准库
- **前端**: 纯 HTML/CSS/JavaScript，无外部依赖
- **进度跟踪**: XMLHttpRequest 上传事件，实时更新
- **数据存储**: SQLite 数据库存储上传历史
- **文件处理**: 安全文件操作，防止重复覆盖
- **路径管理**: 动态路径解析，相对脚本位置

## 📊 性能表现

- 成功测试高达 10GB 的文件
- 局域网上传速度最高可达 1.4GB/s
- 支持多并发上传
- 流式传输，高效内存使用

## 🛡️ 安全性

- 仅限局域网访问（无外网连接）
- 无需身份验证（适用于受信任网络）
- 文件存储在服务器本地
- 无云存储或外部服务

## 🤝 贡献

欢迎贡献！请随时提交拉取请求。对于重大更改，请先开 issue 讨论您想要修改的内容。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。