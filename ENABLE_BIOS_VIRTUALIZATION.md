# 🚨 必须启用BIOS虚拟化

## 🔍 问题诊断
**VirtualizationFirmwareEnabled: False** 表示CPU虚拟化在BIOS/UEFI中未启用。

## 🛠️ 解决方案

### 步骤1：进入BIOS/UEFI设置
1. **重启计算机**
2. 在启动时按特定键进入BIOS/UEFI（通常是：`F2`, `F10`, `F12`, `Del`, `Esc`）
3. 对于Windows 10/11，也可以：
   - 设置 → 更新与安全 → 恢复 → 高级启动 → 立即重新启动
   - 疑难解答 → 高级选项 → UEFI固件设置

### 步骤2：启用虚拟化
在BIOS/UEFI中查找并启用：
1. **Intel CPU**: 
   - `Intel Virtualization Technology (VT-x)`
   - `Intel VT-d` (可选)
   
2. **AMD CPU**:
   - `SVM Mode` (Secure Virtual Machine)
   - `AMD-V`

3. **常见位置**:
   - Advanced → CPU Configuration
   - Security → Virtualization
   - System Configuration → Virtualization Technology

### 步骤3：保存并重启
1. 保存更改（通常是F10）
2. 退出BIOS/UEFI
3. 计算机将重启

### 步骤4：验证虚拟化已启用
重启后，在Windows中验证：
```powershell
# 方法1: 系统信息
systeminfo | findstr /i "虚拟化"

# 方法2: PowerShell
Get-WmiObject -Class Win32_Processor | Select-Object VirtualizationFirmwareEnabled

# 方法3: 任务管理器
# 打开任务管理器 → 性能 → CPU → 查看"虚拟化"状态
```

## ⚙️ 启用后的配置

### 1. 运行修复脚本（管理员权限）
```cmd
fix_hyperv_aehd.bat
```

### 2. 重启计算机
```cmd
shutdown /r /t 0
```

### 3. 验证所有功能
```powershell
# 检查Hyper-V状态
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V

# 检查AEHD驱动
sc query aehd

# 检查模拟器加速
emulator -accel-check
```

## 📋 验证清单
- [ ] BIOS虚拟化已启用
- [ ] Windows Hypervisor Platform 已启用
- [ ] Hyper-V 已启用
- [ ] AEHD驱动已安装并运行
- [ ] 模拟器加速检查通过

## ⏱️ 预计时间
- BIOS设置: 5-10分钟
- Windows功能启用: 5分钟
- 重启: 2-3分钟
- **总计**: 12-18分钟

## 🔗 参考资料
- [Intel虚拟化技术](https://www.intel.com/content/www/us/en/virtualization/virtualization-technology/intel-virtualization-technology.html)
- [AMD虚拟化](https://www.amd.com/en/technologies/virtualization)
- [Microsoft Hyper-V文档](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/)

## ⚠️ 注意事项
1. **不同主板BIOS界面不同**，请参考主板手册
2. **某些品牌机可能限制虚拟化**，需要检查支持文档
3. **启用后可能需要完全关机再开机**（不仅仅是重启）