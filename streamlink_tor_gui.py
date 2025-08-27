import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import sys
import os
import time
import tempfile
import shutil
import json
from datetime import datetime
import docker
from pathlib import Path
import uuid

class StreamlinkDockerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Streamlink Docker Manager")
        self.root.geometry("1200x800")
        
        # Container management
        self.containers = {}  # Store active containers
        self.container_counter = 0
        
        # Docker client
        try:
            self.docker_client = docker.from_env()
            self.docker_available = True
        except Exception as e:
            self.docker_available = False
            self.docker_error = str(e)
        
        # Configuration
        self.config_file = "streamlink_docker_config.json"
        self.load_config()
        
        # Setup GUI
        self.setup_gui()
        
        # Setup cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Check Docker on startup
        self.root.after(1000, self.check_docker_status)
    
    def load_config(self):
        """Load configuration from file"""
        self.config = {
            "docker_image": "streamlink-tor",
            "default_quality": "480p",
            "output_directory": "",
            "auto_remove_containers": True,
            "container_prefix": "streamlink-session"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config.update(json.load(f))
            except Exception as e:
                self.log_message(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log_message(f"Error saving config: {e}")
    
    def setup_gui(self):
        """Setup the GUI interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Containers tab
        self.containers_frame = ttk.Frame(notebook)
        notebook.add(self.containers_frame, text="Containers")
        self.setup_containers_tab()
        
        # Docker tab
        self.docker_frame = ttk.Frame(notebook)
        notebook.add(self.docker_frame, text="Docker")
        self.setup_docker_tab()
        
        # Configuration tab
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="Configuration")
        self.setup_config_tab()
        
        # Logs tab
        self.logs_frame = ttk.Frame(notebook)
        notebook.add(self.logs_frame, text="Logs")
        self.setup_logs_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready" if self.docker_available else "Docker not available")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_containers_tab(self):
        """Setup the container management tab"""
        # Top frame for controls
        control_frame = ttk.Frame(self.containers_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # URL input
        ttk.Label(control_frame, text="Kick URL:").grid(row=0, column=0, sticky="w", padx=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(control_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.url_entry.insert(0, "https://kick.com/")
        
        # Quality input
        ttk.Label(control_frame, text="Quality:").grid(row=1, column=0, sticky="w", padx=5)
        self.quality_var = tk.StringVar(value=self.config.get("default_quality", "480p"))
        self.quality_combo = ttk.Combobox(control_frame, textvariable=self.quality_var, 
                                        values=["best", "worst", "1080p", "720p", "480p", "360p", "240p"])
        self.quality_combo.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Output mode
        ttk.Label(control_frame, text="Output Mode:").grid(row=2, column=0, sticky="w", padx=5)
        self.output_mode_var = tk.StringVar(value="stdout")
        output_mode_frame = ttk.Frame(control_frame)
        output_mode_frame.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Radiobutton(output_mode_frame, text="stdout", variable=self.output_mode_var, 
                       value="stdout").pack(side="left")
        ttk.Radiobutton(output_mode_frame, text="File", variable=self.output_mode_var, 
                       value="file").pack(side="left", padx=(10,0))
        
        # Output directory (for file mode)
        ttk.Label(control_frame, text="Output Directory:").grid(row=3, column=0, sticky="w", padx=5)
        self.output_dir_var = tk.StringVar(value=self.config.get("output_directory", ""))
        output_dir_frame = ttk.Frame(control_frame)
        output_dir_frame.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
        
        self.output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir_var, width=50)
        self.output_dir_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(output_dir_frame, text="Browse", command=self.browse_output_dir).pack(side="right", padx=(5,0))
        
        # Container count input
        ttk.Label(control_frame, text="Number of Containers:").grid(row=4, column=0, sticky="w", padx=5)
        self.container_count_var = tk.StringVar(value="1")
        self.container_spinbox = ttk.Spinbox(control_frame, from_=1, to=10, textvariable=self.container_count_var, width=10)
        self.container_spinbox.grid(row=4, column=1, padx=5, pady=2, sticky="w")
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="Start Containers", command=self.start_containers)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_all_btn = ttk.Button(button_frame, text="Stop All Containers", command=self.stop_all_containers)
        self.stop_all_btn.pack(side="left", padx=5)
        
        self.refresh_btn = ttk.Button(button_frame, text="Refresh Status", command=self.refresh_container_status)
        self.refresh_btn.pack(side="left", padx=5)
        
        # Configure grid weights
        control_frame.columnconfigure(1, weight=1)
        
        # Containers list
        containers_label_frame = ttk.LabelFrame(self.containers_frame, text="Active Containers")
        containers_label_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview for containers
        columns = ("Container ID", "Name", "URL", "Quality", "Status", "Output", "Created")
        self.containers_tree = ttk.Treeview(containers_label_frame, columns=columns, show="tree headings")
        
        for col in columns:
            self.containers_tree.heading(col, text=col)
            self.containers_tree.column(col, width=120)
        
        # Add scrollbars
        tree_scroll = ttk.Scrollbar(containers_label_frame, orient="vertical", command=self.containers_tree.yview)
        self.containers_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.containers_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        tree_scroll.pack(side="right", fill="y")
        
        # Context menu for containers
        self.container_menu = tk.Menu(self.root, tearoff=0)
        self.container_menu.add_command(label="Stop Container", command=self.stop_selected_container)
        self.container_menu.add_command(label="View Logs", command=self.view_container_logs)
        self.container_menu.add_command(label="Remove Container", command=self.remove_selected_container)
        
        self.containers_tree.bind("<Button-3>", self.show_container_menu)
    
    def setup_docker_tab(self):
        """Setup the Docker management tab"""
        # Docker status frame
        status_frame = ttk.LabelFrame(self.docker_frame, text="Docker Status")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.docker_status_var = tk.StringVar()
        ttk.Label(status_frame, textvariable=self.docker_status_var, font=("TkDefaultFont", 10, "bold")).pack(pady=5)
        
        ttk.Button(status_frame, text="Check Docker Status", command=self.check_docker_status).pack(pady=5)
        
        # Image management frame
        image_frame = ttk.LabelFrame(self.docker_frame, text="Image Management")
        image_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(image_frame, text="Docker Image:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.docker_image_var = tk.StringVar(value=self.config.get("docker_image", "streamlink-tor"))
        ttk.Entry(image_frame, textvariable=self.docker_image_var, width=40).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        button_frame = ttk.Frame(image_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Build Image", command=self.build_docker_image).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Pull Image", command=self.pull_docker_image).pack(side="left", padx=5)
        ttk.Button(button_frame, text="List Images", command=self.list_docker_images).pack(side="left", padx=5)
        
        image_frame.columnconfigure(1, weight=1)
        
        # Dockerfile creation frame
        dockerfile_frame = ttk.LabelFrame(self.docker_frame, text="Create Docker Files")
        dockerfile_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ttk.Button(dockerfile_frame, text="Create Docker Files", command=self.create_docker_files).pack(pady=10)
        ttk.Label(dockerfile_frame, text="This will create Dockerfile, kick.py, torrc, and start_with_tor.py").pack()
        
        # Build directory
        ttk.Label(dockerfile_frame, text="Build Directory:").pack(pady=(10,0))
        build_dir_frame = ttk.Frame(dockerfile_frame)
        build_dir_frame.pack(fill="x", padx=10, pady=5)
        
        self.build_dir_var = tk.StringVar(value="./docker_build")
        ttk.Entry(build_dir_frame, textvariable=self.build_dir_var).pack(side="left", fill="x", expand=True)
        ttk.Button(build_dir_frame, text="Browse", command=self.browse_build_dir).pack(side="right", padx=(5,0))
    
    def setup_config_tab(self):
        """Setup the configuration tab"""
        # Container settings frame
        container_frame = ttk.LabelFrame(self.config_frame, text="Container Settings")
        container_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(container_frame, text="Container Name Prefix:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.container_prefix_var = tk.StringVar(value=self.config.get("container_prefix", "streamlink-session"))
        ttk.Entry(container_frame, textvariable=self.container_prefix_var, width=30).grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(container_frame, text="Default Quality:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.default_quality_var = tk.StringVar(value=self.config.get("default_quality", "480p"))
        ttk.Combobox(container_frame, textvariable=self.default_quality_var, 
                    values=["best", "worst", "1080p", "720p", "480p", "360p", "240p"]).grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        self.auto_remove_var = tk.BooleanVar(value=self.config.get("auto_remove_containers", True))
        ttk.Checkbutton(container_frame, text="Auto-remove containers when stopped", 
                       variable=self.auto_remove_var).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Docker settings frame
        docker_settings_frame = ttk.LabelFrame(self.config_frame, text="Docker Settings")
        docker_settings_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(docker_settings_frame, text="Docker Image Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.config_docker_image_var = tk.StringVar(value=self.config.get("docker_image", "streamlink-tor"))
        ttk.Entry(docker_settings_frame, textvariable=self.config_docker_image_var, width=40).grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Label(docker_settings_frame, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.config_output_dir_var = tk.StringVar(value=self.config.get("output_directory", ""))
        output_dir_config_frame = ttk.Frame(docker_settings_frame)
        output_dir_config_frame.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        
        ttk.Entry(output_dir_config_frame, textvariable=self.config_output_dir_var).pack(side="left", fill="x", expand=True)
        ttk.Button(output_dir_config_frame, text="Browse", command=lambda: self.browse_directory(self.config_output_dir_var)).pack(side="right")
        
        docker_settings_frame.columnconfigure(1, weight=1)
        
        # Save button
        ttk.Button(self.config_frame, text="Save Configuration", command=self.save_configuration).pack(pady=10)
    
    def setup_logs_tab(self):
        """Setup the logs tab"""
        self.log_text = scrolledtext.ScrolledText(self.logs_frame, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Log controls
        log_controls = ttk.Frame(self.logs_frame)
        log_controls.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(log_controls, text="Clear Logs", command=self.clear_logs).pack(side="left", padx=5)
        ttk.Button(log_controls, text="Save Logs", command=self.save_logs).pack(side="left", padx=5)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Update status bar with latest message
        self.status_var.set(message)
        
        # Force update
        self.root.update_idletasks()
    
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
    
    def browse_build_dir(self):
        """Browse for build directory"""
        directory = filedialog.askdirectory()
        if directory:
            self.build_dir_var.set(directory)
    
    def browse_directory(self, var):
        """Browse for directory"""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)
    
    def save_configuration(self):
        """Save current configuration"""
        self.config["container_prefix"] = self.container_prefix_var.get()
        self.config["default_quality"] = self.default_quality_var.get()
        self.config["auto_remove_containers"] = self.auto_remove_var.get()
        self.config["docker_image"] = self.config_docker_image_var.get()
        self.config["output_directory"] = self.config_output_dir_var.get()
        
        self.save_config()
        self.log_message("Configuration saved")
        messagebox.showinfo("Success", "Configuration saved successfully!")
    
    def check_docker_status(self):
        """Check Docker daemon status"""
        try:
            if not self.docker_available:
                raise Exception(self.docker_error)
            
            # Test Docker connection
            version = self.docker_client.version()
            self.docker_status_var.set(f"✓ Docker is running (Version: {version['Version']})")
            self.log_message(f"Docker status: OK - Version {version['Version']}")
            
            # Check if our image exists
            try:
                image_name = self.config.get("docker_image", "streamlink-tor")
                self.docker_client.images.get(image_name)
                self.log_message(f"Docker image '{image_name}' found")
            except docker.errors.ImageNotFound:
                self.log_message(f"Docker image '{image_name}' not found - you may need to build it")
                
        except Exception as e:
            self.docker_status_var.set(f"✗ Docker error: {str(e)}")
            self.log_message(f"Docker error: {e}")
            self.docker_available = False
    
    def create_docker_files(self):
        """Create Docker files in the specified directory"""
        build_dir = self.build_dir_var.get()
        if not build_dir:
            messagebox.showerror("Error", "Please specify a build directory")
            return
        
        try:
            os.makedirs(build_dir, exist_ok=True)
            
            # Create Dockerfile
            dockerfile_content = '''# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Streamlink and Tor
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    tor \\
    && rm -rf /var/lib/apt/lists/*

# Create tor data directory and set permissions
RUN mkdir -p /app/tor_data && \\
    chmod 700 /app/tor_data

# Install Streamlink 7.5.0
RUN pip install streamlink==7.5.0

# Install cloudscraper, required by the streamlink-plugin-kick
RUN pip install cloudscraper

# Copy the streamlink-plugin-kick plugin into the Streamlink sideload directory
RUN mkdir -p /usr/local/lib/python3.11/site-packages/streamlink/plugins
COPY kick.py /usr/local/lib/python3.11/site-packages/streamlink/plugins/kick.py

# Verify the plugin file is copied (for debugging)
RUN ls -l /usr/local/lib/python3.11/site-packages/streamlink/plugins

# Create Tor configuration
RUN mkdir -p /etc/tor
COPY torrc /etc/tor/torrc

# Copy the startup script
COPY start_with_tor.py /app/start_with_tor.py

# Set the entrypoint to run the startup script
ENTRYPOINT ["python", "/app/start_with_tor.py"]'''
            
            with open(os.path.join(build_dir, "Dockerfile"), 'w') as f:
                f.write(dockerfile_content)
            
            # Create torrc
            torrc_content = '''# Tor configuration file
SOCKSPort 127.0.0.1:9050
DataDirectory /app/tor_data
Log notice stdout
RunAsDaemon 0

# Security settings
CookieAuthentication 0
ControlPort 127.0.0.1:9051

# Enable new circuit creation
NewCircuitPeriod 30

# Disable DNS port (we only need SOCKS)
DNSPort 0

# Run as root (for Docker container)
User root'''
            
            with open(os.path.join(build_dir, "torrc"), 'w') as f:
                f.write(torrc_content)
            
            # Create kick.py (from the documents provided)
            kick_content = '''"""
$description Kick, a gaming livestreaming platform
$url kick.com
$type live, vod
"""

import re
import cloudscraper
import logging

from streamlink.plugin import Plugin, pluginmatcher
from streamlink.plugin.api import validate
from streamlink.stream import HLSStream
from streamlink.utils.parse import parse_json
from streamlink.exceptions import PluginError


log = logging.getLogger(__name__)


@pluginmatcher(
    re.compile(
        # https://github.com/yt-dlp/yt-dlp/blob/9b7a48abd1b187eae1e3f6c9839c47d43ccec00b/yt_dlp/extractor/kick.py#LL33-L33C111
        r"https?://(?:www\\.)?kick\\.com/(?!(?:video|categories|search|auth)(?:[/?#]|$))(?P<channel>[\\w_-]+)$",
    ),
    name="live",
)
@pluginmatcher(
    re.compile(
        # https://github.com/yt-dlp/yt-dlp/blob/2d5cae9636714ff922d28c548c349d5f2b48f317/yt_dlp/extractor/kick.py#LL84C18-L84C104
        r"https?://(?:www\\.)?kick\\.com/video/(?P<video_id>[\\da-f]{8}-(?:[\\da-f]{4}-){3}[\\da-f]{12})",
    ),
    name="vod",
)
@pluginmatcher(
    re.compile(
        r"https?://(?:www\\.)?kick\\.com/(?!(?:video|categories|search|auth)(?:[/?#]|$))(?P<channel>[\\w_-]+)\\?clip=(?P<clip_id>[\\w_]+)$",
    ),
    name="clip",
)
class KICK(Plugin):
    def _get_streams(self):
        API_BASE_URL = "https://kick.com/api"

        _LIVE_SCHEMA = validate.Schema(
            validate.parse_json(),
            {
                "playback_url": validate.url(path=validate.endswith(".m3u8")),
                "livestream": {
                    "is_live": True,
                    "id": int,
                    "session_title": str,
                    "categories": [{"name": str}],
                },
                "user": {"username": str},
            },
            validate.union_get(
                "playback_url",
                ("livestream", "id"),
                ("user", "username"),
                ("livestream", "session_title"),
                ("livestream", "categories", 0, "name"),
            ),
        )

        _VIDEO_SCHEMA = validate.Schema(
            validate.parse_json(),
            {
                "source": validate.url(path=validate.endswith(".m3u8")),
                "id": int,
                "livestream": {
                    "channel": {"user": {"username": str}},
                    "session_title": str,
                    "categories": [{"name": str}],
                },
            },
            validate.union_get(
                "source",
                "id",
                ("livestream", "channel", "user", "username"),
                ("livestream", "session_title"),
                ("livestream", "categories", 0, "name"),
            ),
        )

        _CLIP_SCHEMA = validate.Schema(
            validate.parse_json(),
            {
                "clip": {
                    "video_url": validate.url(path=validate.endswith(".m3u8")),
                    "id": str,
                    "channel": {"username": str},
                    "title": str,
                    "category": {"name": str},
                },
            },
            validate.union_get(
                ("clip", "video_url"),
                ("clip", "id"),
                ("clip", "channel", "username"),
                ("clip", "title"),
                ("clip", "category", "name"),
            ),
        )

        live, vod, clip = (
            self.matches["live"],
            self.matches["vod"],
            self.matches["clip"],
        )

        try:
            scraper = cloudscraper.create_scraper()
            res = scraper.get(
                "{0}/{1}/{2}".format(
                    API_BASE_URL,
                    *(
                        ["v1/channels", self.match["channel"]]
                        if live
                        else (
                            ["v1/video", self.match["video_id"]]
                            if vod
                            else ["v2/clips", self.match["clip_id"]]
                        )
                    )
                )
            )

            url, self.id, self.author, self.title, self.category = (
                _LIVE_SCHEMA if live else (_VIDEO_SCHEMA if vod else _CLIP_SCHEMA)
            ).validate(res.text)

        except (PluginError, TypeError) as err:
            log.debug(err)
            return
        
        finally:
            scraper.close()

        if live or vod:
            yield from HLSStream.parse_variant_playlist(self.session, url).items()
        elif (
            clip and self.author.casefold() == self.match["channel"].casefold()
        ):  # Sanity check if the clip channel is the same as the one in the URL
            yield "source", HLSStream(self.session, url)


__plugin__ = KICK'''
            
            with open(os.path.join(build_dir, "kick.py"), 'w') as f:
                f.write(kick_content)
            
            # Create start_with_tor.py with URL and quality as environment variables
            start_script_content = '''import subprocess
import sys
import time
import socket
import threading
import os
import signal

def check_tor_connection(host='localhost', port=9050, timeout=10):
    """Check if Tor SOCKS proxy is available"""
    try:
        socket.create_connection((host, port), timeout)
        return True
    except (socket.timeout, socket.error):
        return False

def start_tor():
    """Start Tor daemon"""
    print("Starting Tor daemon...")
    
    # Ensure Tor data directory exists with proper permissions
    os.makedirs('/app/tor_data', exist_ok=True)
    os.chmod('/app/tor_data', 0o700)
    
    # Start Tor process
    tor_cmd = ['tor', '-f', '/etc/tor/torrc']
    tor_process = subprocess.Popen(
        tor_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Wait for Tor to start up
    print("Waiting for Tor to establish connection...")
    max_attempts = 60  # Wait up to 60 seconds
    attempt = 0
    
    while attempt < max_attempts:
        if check_tor_connection():
            print("Tor SOCKS proxy is ready!")
            return tor_process
        time.sleep(1)
        attempt += 1
        
        # Check if Tor process is still running
        if tor_process.poll() is not None:
            print("Tor process terminated unexpectedly")
            if tor_process.stdout:
                output = tor_process.stdout.read()
                print(f"Tor output: {output}")
            sys.exit(1)
    
    print("Timeout waiting for Tor to start")
    tor_process.terminate()
    sys.exit(1)

def run_streamlink():
    """Run streamlink with Tor SOCKS5 proxy"""
    print("Starting streamlink with Tor proxy...")
    
    # Get URL and quality from environment variables
    stream_url = os.environ.get('STREAM_URL', 'https://kick.com/asmongold')
    quality = os.environ.get('STREAM_QUALITY', '480p')
    output_file = os.environ.get('OUTPUT_FILE', '-')
    
    print(f"Stream URL: {stream_url}")
    print(f"Quality: {quality}")
    print(f"Output: {output_file}")
    
    cmd = [
        "streamlink",
        "--http-proxy", "socks5h://localhost:9050",
        stream_url,
        quality,
        "--output", output_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running streamlink: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Received interrupt signal, shutting down...")
        sys.exit(0)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start Tor daemon
        tor_process = start_tor()
        
        # Start streamlink in a separate thread so we can monitor Tor
        streamlink_thread = threading.Thread(target=run_streamlink, daemon=True)
        streamlink_thread.start()
        
        # Keep the main thread alive to monitor processes
        try:
            while streamlink_thread.is_alive():
                time.sleep(1)
                
                # Check if Tor process is still running
                if tor_process.poll() is not None:
                    print("Tor process died, restarting...")
                    tor_process = start_tor()
                    
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            # Clean up
            if tor_process.poll() is None:
                print("Terminating Tor process...")
                tor_process.terminate()
                tor_process.wait(timeout=10)
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()'''
            
            with open(os.path.join(build_dir, "start_with_tor.py"), 'w') as f:
                f.write(start_script_content)
            
            self.log_message(f"Docker files created successfully in {build_dir}")
            messagebox.showinfo("Success", f"Docker files created in {build_dir}")
            
        except Exception as e:
            self.log_message(f"Error creating Docker files: {e}")
            messagebox.showerror("Error", f"Failed to create Docker files: {e}")
    
    def build_docker_image(self):
        """Build the Docker image"""
        if not self.docker_available:
            messagebox.showerror("Error", "Docker is not available")
            return
        
        build_dir = self.build_dir_var.get()
        if not build_dir or not os.path.exists(build_dir):
            messagebox.showerror("Error", "Build directory does not exist. Create Docker files first.")
            return
        
        image_name = self.docker_image_var.get()
        if not image_name:
            messagebox.showerror("Error", "Please specify an image name")
            return
        
        def build_worker():
            try:
                self.log_message(f"Building Docker image '{image_name}'...")
                self.log_message("This may take several minutes...")
                
                # Build the image
                image, logs = self.docker_client.images.build(
                    path=build_dir,
                    tag=image_name,
                    rm=True,
                    forcerm=True
                )
                
                # Log build output
                for log in logs:
                    if 'stream' in log:
                        self.log_message(f"Build: {log['stream'].strip()}")
                
                self.log_message(f"Docker image '{image_name}' built successfully!")
                messagebox.showinfo("Success", f"Docker image '{image_name}' built successfully!")
                
            except Exception as e:
                self.log_message(f"Error building Docker image: {e}")
                messagebox.showerror("Error", f"Failed to build Docker image: {e}")
        
        threading.Thread(target=build_worker, daemon=True).start()
    
    def pull_docker_image(self):
        """Pull Docker image from registry"""
        if not self.docker_available:
            messagebox.showerror("Error", "Docker is not available")
            return
        
        image_name = self.docker_image_var.get()
        if not image_name:
            messagebox.showerror("Error", "Please specify an image name")
            return
        
        def pull_worker():
            try:
                self.log_message(f"Pulling Docker image '{image_name}'...")
                image = self.docker_client.images.pull(image_name)
                self.log_message(f"Docker image '{image_name}' pulled successfully!")
                messagebox.showinfo("Success", f"Docker image '{image_name}' pulled successfully!")
                
            except Exception as e:
                self.log_message(f"Error pulling Docker image: {e}")
                messagebox.showerror("Error", f"Failed to pull Docker image: {e}")
        
        threading.Thread(target=pull_worker, daemon=True).start()
    
    def list_docker_images(self):
        """List available Docker images"""
        if not self.docker_available:
            messagebox.showerror("Error", "Docker is not available")
            return
        
        try:
            images = self.docker_client.images.list()
            self.log_message("Available Docker images:")
            for image in images:
                tags = image.tags if image.tags else ['<none>']
                for tag in tags:
                    size_mb = image.attrs['Size'] / (1024 * 1024)
                    self.log_message(f"  {tag} ({size_mb:.1f} MB)")
                    
        except Exception as e:
            self.log_message(f"Error listing Docker images: {e}")
    
    def start_containers(self):
        """Start Docker containers"""
        if not self.docker_available:
            messagebox.showerror("Error", "Docker is not available")
            return
        
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a Kick URL")
            return
        
        quality = self.quality_var.get()
        output_mode = self.output_mode_var.get()
        output_dir = self.output_dir_var.get().strip()
        
        try:
            num_containers = int(self.container_count_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid number of containers")
            return
        
        image_name = self.config.get("docker_image", "streamlink-tor")
        container_prefix = self.config.get("container_prefix", "streamlink-session")
        
        def start_worker():
            for i in range(num_containers):
                try:
                    container_name = f"{container_prefix}-{self.container_counter}"
                    self.container_counter += 1
                    
                    # Prepare environment variables
                    environment = {
                        'STREAM_URL': url,
                        'STREAM_QUALITY': quality
                    }
                    
                    # Prepare volumes and output
                    volumes = {}
                    if output_mode == "file" and output_dir:
                        # Create output filename
                        if num_containers > 1:
                            output_filename = f"stream_session_{self.container_counter-1}.mp4"
                        else:
                            output_filename = "stream.mp4"
                        
                        environment['OUTPUT_FILE'] = f"/output/{output_filename}"
                        volumes[output_dir] = {'bind': '/output', 'mode': 'rw'}
                    else:
                        environment['OUTPUT_FILE'] = '-'  # stdout
                    
                    self.log_message(f"Starting container: {container_name}")
                    self.log_message(f"  URL: {url}")
                    self.log_message(f"  Quality: {quality}")
                    self.log_message(f"  Output: {environment['OUTPUT_FILE']}")
                    
                    # Start container
                    container = self.docker_client.containers.run(
                        image_name,
                        name=container_name,
                        environment=environment,
                        volumes=volumes,
                        detach=True,
                        remove=self.config.get("auto_remove_containers", True),
                        stdin_open=True,
                        tty=True
                    )
                    
                    # Store container info
                    container_info = {
                        'container': container,
                        'name': container_name,
                        'url': url,
                        'quality': quality,
                        'output': environment['OUTPUT_FILE'],
                        'created': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    self.containers[container.id] = container_info
                    
                    # Add to tree view
                    self.containers_tree.insert("", "end", iid=container.id, values=(
                        container.id[:12],  # Short ID
                        container_name,
                        url,
                        quality,
                        "Running",
                        environment['OUTPUT_FILE'],
                        container_info['created']
                    ))
                    
                    self.log_message(f"Container {container_name} started successfully")
                    
                    # Small delay between containers
                    if i < num_containers - 1:
                        time.sleep(2)
                        
                except Exception as e:
                    self.log_message(f"Error starting container {i+1}: {e}")
                    continue
            
            self.log_message(f"Started {num_containers} container(s)")
        
        threading.Thread(target=start_worker, daemon=True).start()
    
    def stop_all_containers(self):
        """Stop all managed containers"""
        if not self.containers:
            self.log_message("No containers to stop")
            return
        
        def stop_worker():
            container_ids = list(self.containers.keys())
            for container_id in container_ids:
                self.stop_container(container_id)
            
            self.log_message("All containers stopped")
        
        threading.Thread(target=stop_worker, daemon=True).start()
    
    def stop_container(self, container_id):
        """Stop a specific container"""
        if container_id not in self.containers:
            return
        
        try:
            container_info = self.containers[container_id]
            container = container_info['container']
            
            self.log_message(f"Stopping container: {container_info['name']}")
            
            # Stop the container
            container.stop(timeout=10)
            
            # Remove from our tracking
            del self.containers[container_id]
            
            # Remove from tree view
            try:
                self.containers_tree.delete(container_id)
            except:
                pass
            
            self.log_message(f"Container {container_info['name']} stopped")
            
        except Exception as e:
            self.log_message(f"Error stopping container {container_id}: {e}")
    
    def refresh_container_status(self):
        """Refresh the status of all containers"""
        if not self.docker_available:
            return
        
        def refresh_worker():
            try:
                # Get all containers
                all_containers = self.docker_client.containers.list(all=True)
                
                # Update status for our managed containers
                for container_id, container_info in list(self.containers.items()):
                    try:
                        # Find the container in the list
                        docker_container = None
                        for c in all_containers:
                            if c.id == container_id:
                                docker_container = c
                                break
                        
                        if docker_container:
                            status = docker_container.status
                            # Update tree view
                            try:
                                self.containers_tree.set(container_id, "Status", status)
                            except:
                                # Container might have been removed from tree
                                pass
                        else:
                            # Container no longer exists
                            self.log_message(f"Container {container_info['name']} no longer exists")
                            del self.containers[container_id]
                            try:
                                self.containers_tree.delete(container_id)
                            except:
                                pass
                                
                    except Exception as e:
                        self.log_message(f"Error refreshing container {container_id}: {e}")
                
                self.log_message("Container status refreshed")
                
            except Exception as e:
                self.log_message(f"Error refreshing container status: {e}")
        
        threading.Thread(target=refresh_worker, daemon=True).start()
    
    def stop_selected_container(self):
        """Stop the selected container from context menu"""
        selection = self.containers_tree.selection()
        if selection:
            container_id = selection[0]
            self.stop_container(container_id)
    
    def remove_selected_container(self):
        """Remove the selected container"""
        selection = self.containers_tree.selection()
        if not selection:
            return
        
        container_id = selection[0]
        if container_id not in self.containers:
            return
        
        try:
            container_info = self.containers[container_id]
            container = container_info['container']
            
            # Stop if running
            if container.status == 'running':
                container.stop(timeout=10)
            
            # Remove container
            container.remove()
            
            # Remove from tracking
            del self.containers[container_id]
            self.containers_tree.delete(container_id)
            
            self.log_message(f"Container {container_info['name']} removed")
            
        except Exception as e:
            self.log_message(f"Error removing container: {e}")
    
    def view_container_logs(self):
        """View logs for the selected container"""
        selection = self.containers_tree.selection()
        if not selection:
            return
        
        container_id = selection[0]
        if container_id not in self.containers:
            return
        
        try:
            container_info = self.containers[container_id]
            container = container_info['container']
            
            # Get logs
            logs = container.logs(tail=100).decode('utf-8')
            
            # Show in a new window
            log_window = tk.Toplevel(self.root)
            log_window.title(f"Container Logs - {container_info['name']}")
            log_window.geometry("800x600")
            
            log_text = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
            log_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            log_text.insert(tk.END, logs)
            log_text.see(tk.END)
            
        except Exception as e:
            self.log_message(f"Error viewing container logs: {e}")
            messagebox.showerror("Error", f"Failed to view logs: {e}")
    
    def show_container_menu(self, event):
        """Show context menu for containers"""
        item = self.containers_tree.identify_row(event.y)
        if item:
            self.containers_tree.selection_set(item)
            self.container_menu.post(event.x_root, event.y_root)
    
    def clear_logs(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """Save logs to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Logs saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        # Stop all containers
        if self.containers:
            self.log_message("Stopping all containers before closing...")
            for container_id in list(self.containers.keys()):
                self.stop_container(container_id)
        
        # Save configuration
        self.save_config()
        
        self.root.destroy()

def main():
    # Check if docker library is available
    try:
        import docker
    except ImportError:
        messagebox.showerror("Error", "Docker library not found. Please install it with: pip install docker")
        return
    
    root = tk.Tk()
    app = StreamlinkDockerGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()

if __name__ == "__main__":
    main()