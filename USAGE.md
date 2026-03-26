# VPN 代理隧道 — 使用说明

## 架构说明（重要）

| 组件 | 运行位置 |
|------|----------|
| **服务端** `server/run.py` | **应部署在 VPS（搬瓦工等公网服务器）上**，监听 `0.0.0.0:18443`（TLS），负责鉴权与出站转发 |
| **Windows 客户端** | 仅在你自己的 **Windows 电脑**上运行，**图形界面**，本地开 SOCKS5 连到 VPS |
| **Android 客户端** | 仅在 **手机**上安装，连到同一台 VPS |

**你的 Windows 电脑不需要、也不应该长期运行服务端进程**；服务端进程只在 **VPS** 上常驻。  
本机执行 `python server/run.py` 或 `scripts/verify_local.py` 仅用于开发/联调。

---

默认测试账号（首次在 **VPS** 上启动服务端时自动写入数据库）：

- 用户名：`demo`
- 密码：`demo123`

上线后请在 VPS 上修改密码或新增用户。

---

## 一、服务端：部署在 VPS 上

### 1. 上传项目

将整个 `vpn-proxy-client` 目录上传到 VPS（如 `/opt/vpn-proxy-client`），或使用：

```text
powershell -ExecutionPolicy Bypass -File scripts\deploy_server_to_vps.ps1 -VpsHost 你的服务器IP
```

（需本机已可用 `ssh`/`scp`，密码或密钥登录均可。）

### 2. 安装依赖并启动

在 **VPS** 上执行：

```text
cd /opt/vpn-proxy-client
pip3 install -r server/requirements.txt
python3 server/run.py
```

- 证书生成在 `server/data/certs/`（`server.crt` 给客户端，`server.key` 仅留在服务器）。
- 用户库：`server/data/users.db`。
- **防火墙 / 安全组**：放行 **TCP 18443**（与 SSH 22 无关）。

### 3. 把 CA 证书给客户端

从 VPS 下载 **`server/data/certs/server.crt`**：

- **Windows 图形界面**：在「CA 证书路径」中指向你保存的 `server.crt`。
- **Android**：放入 `android/app/src/main/res/raw/ca.crt`（内容同 `server.crt`）；或使用本仓库已编译好的 APK 时，若你更换了服务端证书，需重新放入 `ca.crt` 后重新编译。

---

## 二、本地一键验证（仅开发机）

在 **开发用电脑**上（可与 VPS 无关）用于自测隧道：

```text
python scripts/verify_local.py
```

出现 **`VERIFY_OK`** 即表示本机隧道 + SOCKS 正常（需本机可访问公网）。

---

## 三、Windows：图形界面客户端

### 1. 依赖

```text
pip install -r windows_client/requirements.txt
```

### 2. 启动方式（任选）

- **双击**：项目根目录下的 **`启动Windows图形界面.bat`**
- **命令行**：

```text
cd vpn-proxy-client
python -m windows_client.app_gui
```

### 3. 界面操作

1. **服务端地址**填 **VPS 公网 IP 或域名**，端口 **18443**（若未改）。
2. 填写 **用户名 / 密码**、**CA 证书路径**（VPS 上的 `server.crt` 拷到本机后的路径）。
3. 点击 **启动代理**：本机 **SOCKS5** 默认 **`127.0.0.1:1080`**。
4. 在浏览器或其它软件中配置 SOCKS5（支持远程 DNS 的选 `socks5h` 语义）。
5. **停止** 即断开。

密码不会写入配置文件；仅保存主机、端口、用户名、证书路径等到用户目录 `~/.vpnproxy_client.json`。

---

## 四、Android 客户端

### 已编译好的 APK（本机已构建）

调试包路径：

```text
dist\VpnProxyClient-debug.apk
```

（完整路径：`vpn-proxy-client\dist\VpnProxyClient-debug.apk`，约 5.5MB。）  
复制到手机安装即可（需在系统设置中允许安装未知来源应用）。

### 自行重新编译（可选）

本机已配置并可编译的环境示例：

- **JDK**：`E:\work\tools\jdk17-extract\jdk-17.0.18+8`
- **Android SDK**：`E:\work\tools\android-sdk`（已含 platform-34、build-tools 34.0.0）
- 在 `android\` 目录执行：`gradlew.bat assembleDebug`

生成 APK：`android\app\build\outputs\apk\debug\app-debug.apk`

### 使用

1. 安装 APK 后，填写 **VPS 地址**、**18443**、**demo / demo123**（或你的账号）。
2. 点 **启动代理**，通知栏会显示前台服务；手机侧 **SOCKS5 为 127.0.0.1:你填的端口**（默认 1080）。
3. Android 13+ 建议授予 **通知** 权限。

### 模拟器联调（本机验证 APK，可选）

已安装：**Emulator**、`system-images;android-34;google_apis;x86_64`、AVD 名称 **`vpnproxy_e2e`**（数据目录 **`E:\work\android_sdk_home`**，避免占满 C 盘）。

在 **Windows x86 模拟器**上运行需要 **CPU 虚拟化加速**其一：

- **推荐**：以**管理员**运行  
  `E:\work\tools\android-sdk\extras\google\Android_Emulator_Hypervisor_Driver\silent_install.bat`  
  安装 **Android Emulator Hypervisor Driver (AEHD)**；或  
- 在「启用或关闭 Windows 功能」中打开 **Windows 虚拟机监控程序平台 (WHPX)**，并保证 BIOS 中已开启虚拟化。

未安装加速驱动时，x86_64 模拟器会报错或 `adb` 长期 **offline**；使用 **`-accel off`** 可启动但极慢且本环境曾出现 **adb offline**，**不推荐**依赖此模式做日常验证。

装好加速后，可在项目根目录执行：

```text
powershell -ExecutionPolicy Bypass -File scripts\verify_emulator_e2e.ps1
```

成功会输出 **`EMULATOR_E2E_OK`**。更省事的方式是直接把 **`dist\VpnProxyClient-debug.apk`** 装到**真机**验证。

---

## 五、一键自动化验证（开发机）

在项目根目录：

```text
pip install -r requirements-all.txt requests pysocks
powershell -ExecutionPolicy Bypass -File scripts\verify_all.ps1
```

成功末尾输出 **`ALL_CHECKS_OK`**（含：隧道 `VERIFY_OK`、Gradle 构建与 lint、`aapt` 包名校验）。

---

## 六、安全提示

- 默认账号仅作测试；生产环境务必改密。
- 勿将 `server.key` 发给客户端；仅分发 `server.crt`。
- 妥善保管 VPS root 密码，优先使用 SSH 密钥。
