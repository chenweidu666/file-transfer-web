# File Transfer Web

<p align="center">
  <strong>Simple Web-Based File Transfer Between Devices on Local Network</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue" alt="Language">
  <img src="https://img.shields.io/badge/Framework-http.server-green" alt="Framework">
  <img src="https://img.shields.io/badge/Platform-Cross--Platform-brightgreen" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

<p align="center">
  <a href="./README_zh.md">中文文档</a> | <a href="./README.md">English Document</a>
</p>

---

## 🚀 Features

- **Web-based Transfer**: Transfer files between devices using any web browser
- **Real-time Progress**: Visual upload progress bars with percentage
- **Upload History**: Track all uploaded files with timestamps and sizes
- **Multi-file Support**: Upload multiple files at once
- **Drag & Drop**: Intuitive drag-and-drop interface
- **Auto IP Detection**: Automatically detects local network IP address
- **File Management**: Download, delete individual files, or clear all records
- **Zero Dependencies**: Pure Python standard library implementation

## 📋 Requirements

- Python 3.6+
- Any modern web browser (Chrome, Firefox, Safari, Edge)

## 🛠️ Usage

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

## 📱 How to Use

1. Run the server on the target device
2. Access the displayed URL from any device on the same network
3. Select or drag files to upload
4. Monitor upload progress in real-time
5. Manage uploaded files through the history panel

## 🗂️ Directory Structure

```
file-transfer-web/
├── upload_server.py         # Main server application
├── server.sh                # Server management script
├── data/                    # Auto-generated data directory
│   ├── uploads/             # Storage for uploaded files
│   └── upload.db            # Upload records database
├── LICENSE                  # MIT License
└── README.md                # English documentation
└── README_zh.md             # Chinese documentation
```

## 🔧 Technical Implementation

- **Backend**: Python HTTP server using standard library
- **Frontend**: Pure HTML/CSS/JavaScript, no external dependencies
- **Progress Tracking**: XMLHttpRequest upload events with real-time updates
- **Data Storage**: SQLite database for upload history
- **File Handling**: Safe file operations with duplicate prevention
- **Path Management**: Dynamic path resolution relative to script location

## 📊 Performance

- Successfully tested with files up to 10GB
- Upload speeds up to 1.4GB/s on local networks
- Handles multiple simultaneous uploads
- Efficient memory usage with streaming transfers

## 🛡️ Security

- Local network only access (no external connections)
- No authentication required (intended for trusted networks)
- Files stored locally on the server machine
- No cloud storage or external services

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.