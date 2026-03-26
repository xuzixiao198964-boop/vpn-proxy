#!/usr/bin/env python3
"""
非交互执行一条远程命令（用于脚本自动化）。依赖: pip install paramiko

默认连接当前测试 VPS（可被环境变量覆盖）。环境变量 SSH_PASSWORD 若设置则优先于脚本内测试密码。

用法:
  python ssh_exec.py "uname -a"
  python ssh_exec.py root@104.244.90.202 "uptime"
"""
import os
import sys

try:
    import paramiko
except ImportError:
    print("请先安装: pip install paramiko", file=sys.stderr)
    sys.exit(1)

# --- 测试环境默认值（上线/换机后请修改或删除，改用 SSH_PASSWORD / 密钥）---
TEST_HOST = "104.244.90.202"
TEST_USER = "root"
TEST_PASSWORD = "v9wSxMxg92dp"


def main() -> None:
    password = os.environ.get("SSH_PASSWORD") or TEST_PASSWORD

    if len(sys.argv) == 2:
        command = sys.argv[1]
        user, host = TEST_USER, TEST_HOST
    elif len(sys.argv) >= 3:
        target = sys.argv[1]
        command = sys.argv[2]
        if "@" in target:
            user, host = target.split("@", 1)
        else:
            user, host = "root", target
    else:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, 22, user, password, timeout=20)
        _, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        code = stdout.channel.recv_exit_status()
        if out:
            sys.stdout.write(out)
        if err:
            sys.stderr.write(err)
        sys.exit(code)
    finally:
        client.close()


if __name__ == "__main__":
    main()
