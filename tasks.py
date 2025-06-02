# tasks.py

import os
from invoke import task
from fabric import Connection

# --- 全局配置变量 ---
# 请根据你的实际情况修改这些值

# 本地项目根目录（用于 rsync 或其他本地操作）
# Fabric 脚本文件（tasks.py）所在的目录
LOCAL_FABFILE_DIR = os.path.dirname(os.path.abspath(__file__))

# 远程服务器上的路径配置
# 你的站点根目录，所有部署文件将放在这里
REMOTE_SITE_PATH = "/home/opaimon/azure.paimoe.tech"
# Django 项目的实际根目录（通常是 REMOTE_SITE_PATH/your_project_name）
# 在你的例子中，项目目录是 todolist
REMOTE_PROJECT_ROOT = f"{REMOTE_SITE_PATH}/todolist"
# 虚拟环境路径，位于 Django 项目根目录内
REMOTE_VENV_PATH = f"{REMOTE_PROJECT_ROOT}/.venv"
# Gunicorn Unix Socket 的路径，用于 Nginx 与 Gunicorn 通信
REMOTE_GUNICORN_SOCKET_PATH = f"/run/gunicorn/{os.path.basename(REMOTE_SITE_PATH)}.socket"
# Nginx 站点配置文件的路径（sites-available）
REMOTE_NGINX_SITE_AVAILABLE = f"/etc/nginx/sites-available/{os.path.basename(REMOTE_SITE_PATH)}.conf"
# Nginx 站点配置文件的链接路径（sites-enabled）
REMOTE_NGINX_SITE_ENABLED = f"/etc/nginx/sites-enabled/{os.path.basename(REMOTE_SITE_PATH)}.conf"
# 静态文件收集目录，对应 Django settings.py 中的 STATIC_ROOT
REMOTE_STATIC_ROOT_PATH = f"{REMOTE_SITE_PATH}/static"
# 数据库文件存放目录 (如果使用 SQLite)
REMOTE_DATABASE_ROOT_PATH = f"{REMOTE_SITE_PATH}/database"
# 环境变量文件的路径
REMOTE_ENV_VARS_FILE_PATH = f"{REMOTE_SITE_PATH}/env_vars.conf"
REMOTE_BIN_PATH = f"/home/opaimon/.local/bin/"

# 服务器连接信息
SERVER_IP = "4.194.57.235"
DOMAIN_NAME = "azure.paimoe.tech"
REMOTE_USER = "opaimon" # SSH 登录用户和 Gunicorn 运行用户
REMOTE_SSH_PORT = 5987 # SSH 端口

@task
def deploy(ctx): # ctx 是 invoke.Context 对象
    """
    Deploys the Django application to the remote server.
    """
    # 在任务内部创建 Fabric Connection 对象
    c = Connection(
        host=DOMAIN_NAME, # 或者 SERVER_IP，使用域名更通用
        port=REMOTE_SSH_PORT,
        user=REMOTE_USER
        # 如果需要密码认证，可以添加 connect_kwargs={"password": "your_ssh_password"}
        # 强烈建议使用 SSH 密钥认证，将密钥添加到 SSH 代理或 ~/.ssh 目录
    )

    print(f"--- Starting deployment to {c.host}:{c.port} as {c.user} ---")

    # 1. 确保远程站点根目录和子目录存在
    print(f"Ensuring remote directories exist: {REMOTE_SITE_PATH}, {REMOTE_PROJECT_ROOT}, {REMOTE_DATABASE_ROOT_PATH}")
    c.run(f"mkdir -p {REMOTE_SITE_PATH}", warn=True)
    c.run(f"mkdir -p {REMOTE_PROJECT_ROOT}", warn=True)
    c.run(f"mkdir -p {REMOTE_DATABASE_ROOT_PATH}", warn=True)

    # 2. 拉取最新源代码（使用 git clone 或 git fetch + reset --hard）
    repo_url = "https://github.com/OPaimon/todolist.git"
    local_commit = os.popen("git log -n 1 --format=%H").read().strip()
    with c.cd(REMOTE_PROJECT_ROOT):
        # 检查 .git 目录是否存在
        result = c.run("test -d .git", warn=True)
        if result.failed:
            print("Cloning repository...")
            c.run(f"git clone {repo_url} .")
        else:
            print("Fetching latest changes...")
            c.run("git fetch")
        print(f"Resetting to local commit {local_commit}...")
        c.run(f"git reset --hard {local_commit}")

    # 3. 创建并同步虚拟环境依赖
    with c.cd(REMOTE_PROJECT_ROOT):
        print("Synchronizing dependencies with uv...")
        # uv sync 在 .venv 不存在时会自动创建虚拟环境并安装依赖
        c.run(f"{REMOTE_BIN_PATH}uv sync")

    # 5. 收集静态文件
    with c.cd(REMOTE_PROJECT_ROOT):
        print("Collecting static files...")
        c.run(f"{REMOTE_VENV_PATH}/bin/python manage.py collectstatic --noinput")
        # 设置静态文件目录的权限，确保 Nginx 可以读取
        print(f"Setting permissions for static files: {REMOTE_STATIC_ROOT_PATH}")
        c.run(f"sudo chown -R {REMOTE_USER}:{REMOTE_USER} {REMOTE_STATIC_ROOT_PATH}")
        c.run(f"sudo chmod -R 755 {REMOTE_STATIC_ROOT_PATH}") # 确保 Nginx 可以进入目录并读取文件


    # 6. 运行数据库迁移
    with c.cd(REMOTE_PROJECT_ROOT):
        print("Applying database migrations...")
        c.run(f"{REMOTE_VENV_PATH}/bin/python manage.py migrate")
        # 设置数据库文件（如果使用 SQLite）的权限
        print(f"Setting permissions for database directory: {REMOTE_DATABASE_ROOT_PATH}")
        c.run(f"sudo chown -R {REMOTE_USER}:{REMOTE_USER} {REMOTE_DATABASE_ROOT_PATH}")
        c.run(f"sudo chmod -R 750 {REMOTE_DATABASE_ROOT_PATH}") # 数据库文件通常只需要拥有者和组读写


    # 7. 更新 Gunicorn Systemd Service 文件
    print("Updating Gunicorn Systemd service file...")

    # 读取模板内容
    template_path = os.path.join(LOCAL_FABFILE_DIR, "deploy_tools", "gunicorn-systemd.template.service")
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # 替换模板变量
    service_content = (
        template_content
        .replace("DOMAIN_NAME", DOMAIN_NAME)
        .replace("REMOTE_USER", REMOTE_USER)
        .replace("SERVER_IP", SERVER_IP)
    )

    service_file_name = f"{DOMAIN_NAME.replace('.', '_')}.service"
    remote_service_path = f"/etc/systemd/system/{service_file_name}"

    # 上传并写入 service 文件
    c.run(f"echo '{service_content}' | sudo tee {remote_service_path}")

    # 8. 重新加载 Systemd 配置并启动/重启 Gunicorn
    print("Reloading Systemd daemon and restarting Gunicorn service...")
    c.run("sudo systemctl daemon-reload")
    c.run(f"sudo systemctl enable {service_file_name}", warn=True) # enable warn=True, 首次启用
    c.run(f"sudo systemctl restart {service_file_name}")

    # 9. 更新 Nginx 配置
    print("Updating Nginx configuration...")
    nginx_template_path = os.path.join(LOCAL_FABFILE_DIR, "deploy_tools", "nginx.template.conf")
    with open(nginx_template_path, "r", encoding="utf-8") as f:
        nginx_template_content = f.read()
    nginx_conf_content = (
        nginx_template_content
        .replace("DOMAIN_NAME", DOMAIN_NAME)
    )
    # 上传并写入 Nginx 配置文件
    c.run(f"echo '{nginx_conf_content}' | sudo tee {REMOTE_NGINX_SITE_AVAILABLE}")

    # 10. 激活 Nginx 站点 (如果尚未激活)
    print("Ensuring Nginx site is enabled...")
    c.run(f"sudo ln -sf {REMOTE_NGINX_SITE_AVAILABLE} {REMOTE_NGINX_SITE_ENABLED}", warn=True)

    # 11. 测试 Nginx 配置并重启 Nginx
    print("Testing Nginx configuration and reloading...")
    c.run("sudo nginx -t") # 测试 Nginx 配置是否有效
    c.run("sudo systemctl reload nginx") # 平滑重启 Nginx

    print(f"--- Deployment to {c.host} complete! Visit http://{DOMAIN_NAME} ---")