import os
import sys
import time
import signal
import platform
import argparse
import subprocess
from pathlib import Path

# Cấu hình encoding UTF-8 để hỗ trợ tiếng Việt trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Export hàm khởi tạo mô hình toàn cục từ src.models (Single Source of Truth)
from src.models import setup_global_models

def print_banner():
    """In tiêu đề hệ thống trực quan."""
    print("=" * 65)
    print("  🚀 APPOTA NEXTGEN - ENTERPRISE SECURE RAG FULLSTACK SYSTEM")
    print("  • Backend: FastAPI (RBAC Security, Hybrid Search, FlashRank)")
    print("  • Frontend: Next.js 16 (App Router, TypeScript, UI Client)")
    print("=" * 65)

def terminate_process(proc, name="tiến trình"):
    """Dọn dẹp và kết thúc an toàn subprocess (xử lý process tree trên Windows)."""
    if proc is None or proc.poll() is not None:
        return

    print(f"\n[Shutdown] Đang dừng {name} (PID: {proc.pid})...")
    try:
        if platform.system() == "Windows":
            # Sử dụng taskkill /T /F để đóng sạch toàn bộ process tree (Node/Python)
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            proc.terminate()
            proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

def run_backend(host="0.0.0.0", port=8000, reload=True):
    """Khởi chạy máy chủ FastAPI Backend bằng Uvicorn."""
    print(f"[Backend] Khởi chạy FastAPI tại http://{host}:{port} ...")
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "app:app",
        "--host", host,
        "--port", str(port),
    ]
    if reload:
        cmd.append("--reload")

    return subprocess.Popen(cmd, cwd=str(BASE_DIR))

def run_frontend(port=3000):
    """Khởi chạy ứng dụng Next.js Frontend."""
    if not FRONTEND_DIR.exists():
        print(f"[Frontend] ❌ Không tìm thấy thư mục frontend tại {FRONTEND_DIR}")
        return None

    # Kiểm tra node_modules
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("[Frontend] 📦 Chưa phát hiện node_modules. Đang chạy 'npm install'...")
        install_cmd = "npm install" if platform.system() != "Windows" else "npm.cmd install"
        subprocess.run(install_cmd, shell=True, cwd=str(FRONTEND_DIR), check=True)

    print(f"[Frontend] Khởi chạy Next.js tại http://localhost:{port} ...")
    dev_cmd = f"npm run dev -- -p {port}" if platform.system() != "Windows" else f"npm.cmd run dev -- -p {port}"
    return subprocess.Popen(dev_cmd, shell=True, cwd=str(FRONTEND_DIR))

def wait_for_backend_ready(port=8000, timeout=45):
    """Thăm dò định kỳ kiểm tra xem FastAPI Backend đã sẵn sàng nhận kết nối hay chưa."""
    import urllib.request
    url = f"http://127.0.0.1:{port}/api/health"
    print(f"[System] ⏳ Đang chờ FastAPI Backend khởi tạo mô hình và Qdrant DB ({url})...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    print("[System] ✅ FastAPI Backend đã sẵn sàng phục vụ API!")
                    return True
        except Exception:
            pass
        time.sleep(1)
    print("[System] ⚠️ Backend mất nhiều thời gian hơn dự kiến, tiếp tục khởi động Frontend...")
    return False

def run_fullstack(host="0.0.0.0", backend_port=8000, frontend_port=3000, reload=True):
    """Khởi chạy đồng thời cả FastAPI Backend và Next.js Frontend."""
    print_banner()
    
    backend_proc = None
    frontend_proc = None

    def signal_handler(sig, frame):
        print("\n\n[System] Đã nhận tín hiệu dừng (Ctrl+C). Đang dọn dẹp hệ thống...")
        terminate_process(frontend_proc, "Next.js Frontend")
        terminate_process(backend_proc, "FastAPI Backend")
        print("[System] ✅ Toàn bộ dịch vụ đã dừng an toàn. Tạm biệt!\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. Khởi động Backend
        backend_proc = run_backend(host=host, port=backend_port, reload=reload)
        
        # Chờ backend hoàn tất nạp model và mở cổng API trước khi bật Frontend
        wait_for_backend_ready(port=backend_port, timeout=45)

        # 2. Khởi động Frontend
        frontend_proc = run_frontend(port=frontend_port)

        print("\n" + "-" * 65)
        print("  ✅ CÁC ĐỊA CHỈ TRUY CẬP HỆ THỐNG:")
        print(f"  🌐 Next.js Web UI : http://localhost:{frontend_port}")
        print(f"  🚀 FastAPI Backend: http://localhost:{backend_port}")
        print(f"  📄 Swagger Docs   : http://localhost:{backend_port}/docs")
        print(f"  📚 ReDoc          : http://localhost:{backend_port}/redoc")
        print("-" * 65)
        print("  💡 Nhấn Ctrl + C để dừng đồng thời cả 2 dịch vụ.\n")

        # Giữ process chính chạy và kiểm tra liveness của 2 tiến trình con
        while True:
            time.sleep(1)
            if backend_proc and backend_proc.poll() is not None:
                print("\n[Cảnh báo] FastAPI Backend đã dừng!")
                break
            if frontend_proc and frontend_proc.poll() is not None:
                print("\n[Cảnh báo] Next.js Frontend đã dừng!")
                break

    except KeyboardInterrupt:
        signal_handler(None, None)
    finally:
        terminate_process(frontend_proc, "Next.js Frontend")
        terminate_process(backend_proc, "FastAPI Backend")

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Trình khởi chạy Appota NextGen Enterprise Secure RAG Fullstack (FastAPI + Next.js)"
    )
    parser.add_argument(
        "--all", action="store_true", default=False,
        help="Khởi chạy cả FastAPI Backend và Next.js Frontend (Mặc định)"
    )
    parser.add_argument(
        "-b", "--backend", action="store_true",
        help="Chỉ khởi chạy FastAPI Backend"
    )
    parser.add_argument(
        "-f", "--frontend", action="store_true",
        help="Chỉ khởi chạy Next.js Frontend"
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0",
        help="Host cho Backend FastAPI (Mặc định: 0.0.0.0)"
    )
    parser.add_argument(
        "--backend-port", type=int, default=8000,
        help="Cổng kết nối Backend FastAPI (Mặc định: 8000)"
    )
    parser.add_argument(
        "--frontend-port", type=int, default=3000,
        help="Cổng kết nối Next.js Frontend (Mặc định: 3000)"
    )
    parser.add_argument(
        "--no-reload", action="store_true",
        help="Tắt chế độ Hot Reload của Uvicorn"
    )

    args = parser.parse_args(argv)

    if args.backend:
        print_banner()
        proc = run_backend(host=args.host, port=args.backend_port, reload=not args.no_reload)
        try:
            proc.wait()
        except KeyboardInterrupt:
            terminate_process(proc, "FastAPI Backend")
    elif args.frontend:
        print_banner()
        proc = run_frontend(port=args.frontend_port)
        if proc:
            try:
                proc.wait()
            except KeyboardInterrupt:
                terminate_process(proc, "Next.js Frontend")
    else:
        # Mặc định: Chạy cả Fullstack Backend + Frontend
        run_fullstack(
            host=args.host,
            backend_port=args.backend_port,
            frontend_port=args.frontend_port,
            reload=not args.no_reload
        )

if __name__ == "__main__":
    main()