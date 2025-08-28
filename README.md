# 🎥 Kick Proxyless Viewer Simulator

A **Docker-based GUI application** for viewing [Kick.com](https://kick.com) streams with **built-in Tor proxy support**.  
This tool enables multiple containerized Streamlink sessions with automatic Tor routing for **enhanced privacy** and **connection management**.

**SUPPORTED EDITION ALLOWS UNLIMITED SESIONS**
https://ko-fi.com/s/a61547e0b9

**ACTIVELY DEVELOPED AND UPDATED**

---

## ✨ Features

- 🖥 **Multiple Container Management** – Run multiple simultaneous stream sessions  
- 🕵️ **Built-in Tor Proxy** – Each container routes traffic through Tor  
- 🐳 **Docker Integration** – Fully containerized with automatic setup  
- 🎛 **GUI Interface** – User-friendly with tabs for different functions  
- 📺 **Quality Selection** – Supports 1080p, 720p, 480p, and more  
- 📡 **Output Options** – Stream to stdout or save to file  
- 🔎 **Real-time Monitoring** – View logs and container status live  
- ⚙️ **Configuration Management** – Save & load settings with ease  

---

## 📌 What It Does

Each container created by the app:  

1. Starts a **Tor daemon** with SOCKS5 proxy  
2. Runs **Streamlink** with the Kick.com plugin through Tor  
3. Streams to **stdout** or saves to a **file**  
4. Operates **independently** from other containers  

The **GUI** lets you:  
- Start/stop sessions  
- View logs  
- Configure and save settings  

---

## 🖥 System Requirements

| Requirement | Minimum | Recommended |
|-------------|----------|-------------|
| **OS** | Windows 10/11 (64-bit) | – |
| **Docker** | Docker Desktop | Latest stable |
| **RAM** | 4GB | 8GB+ for multi-container |
| **Network** | Stable internet connection | – |

---

## ⚡ Installation

### 1. Prerequisites
- [Download Docker Desktop](https://www.docker.com/products/docker-desktop/) and install  
- Verify Docker is working:  

```bash
docker --version
docker info
## 2. Quick Start

1. **Download** `kick-proxyless-viewer-simulator.exe` from the Releases page  
2. **Place** it in a folder with write permissions  
3. **Run** the `.exe`  

---

## 🚀 Usage

### First Run Setup
1. Open the app → **Docker tab**  
2. Click **Create Docker Files**  
3. Click **Build Image** (`streamlink-tor`) → wait 5–10 minutes  

### Basic Operation
```bash
kick-proxyless-viewer-simulator.exe
## 🚀 Usage

### Basic Operation

1. Enter a **Kick.com URL** (e.g., `https://kick.com/username`)  
2. Select **stream quality** (480p / 720p / 1080p)  
3. Choose **output mode** (stdout / file)  
4. Set **number of containers**  
5. Click **Start Containers** → monitor progress in the **Logs tab**  

---

## ⚙️ Configuration Options

### Container Settings
- **Name Prefix** – Customize container naming  
- **Default Quality** – Set preferred resolution  
- **Auto-remove** – Clean up stopped containers  

### Output Options
- **stdout** – Print stream to console (default)  
- **file** – Save streams (auto-named, configurable directory)  

---

## 🐳 Managing Containers

- **Right-click** a container for options: Stop, Logs, Remove  
- **Bulk Actions**: Stop All / Refresh Status  
- **Image Management**: Build, Pull, List images  

### Build Directory (default: `./docker_build`)
docker_build/
├── Dockerfile # Docker image config
├── kick.py # Streamlink Kick.com plugin
├── torrc # Tor configuration
└── start_with_tor.py # Container startup script

---

## 🛠 Troubleshooting

### Common Issues
- **Docker Not Available** → Ensure Docker Desktop is running  
- **Build Fails** → Check internet, clear cache:
```bash
docker system prune
Containers Fail to Start → Verify image exists

Stream Connection Problems → Check Kick URL, try different quality, wait 30–60s for Tor

Performance Tips
RAM: Each container uses ~200–500MB

CPU: More containers = higher CPU load

Network: Tor routing may reduce speed (lower quality helps)

🔍 Log Analysis
Check the Logs tab for:

Container startup progress

Tor connection status

Streamlink connection details

Error/debug messages

🧩 Technical Details
Base Image: python:3.11-slim

Proxy: Tor SOCKS5 (localhost:9050)

Streamlink Version: 7.5.0

Plugin: Custom Kick.com plugin with cloudscraper support

Security Features
Isolated container environments

Tor anonymized connections

No persistent storage

Automatic container cleanup

📂 Configuration File
Settings are saved in streamlink_docker_config.json:

json
Copy code
{
  "docker_image": "streamlink-tor",
  "default_quality": "480p",
  "output_directory": "",
  "auto_remove_containers": true,
  "container_prefix": "streamlink-session"
}
⚠️ Known Limitations
Requires active internet + Docker Desktop running

Some networks may block Tor

Stream quality depends on source availability

📜 Version Info
Python: 3.11

GUI: Tkinter

Docker SDK: Python

Streamlink: 7.5.0

Tor: Integrated

🛡 Disclaimer
⚠️ This tool is for educational and legitimate streaming purposes only.
Ensure compliance with Kick.com’s Terms of Service and local laws regarding proxy usage.

