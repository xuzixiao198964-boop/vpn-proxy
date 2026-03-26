package com.vpnproxy.app

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.net.VpnService
import android.os.Bundle
import android.os.IBinder
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

/**
 * 增强的主界面 - 修复停止问题和状态显示
 */
class EnhancedMainActivity : AppCompatActivity() {
    
    private lateinit var editServer: EditText
    private lateinit var editPort: EditText
    private lateinit var editUsername: EditText
    private lateinit var editPassword: EditText
    private lateinit var btnConnect: Button
    private lateinit var btnDisconnect: Button
    private lateinit var btnLogs: Button
    private lateinit var textStatus: TextView
    private lateinit var textConnectionInfo: TextView
    
    private var isConnecting = false
    private var isConnected = false
    
    private val vpnServiceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            SelectableLogUtils.i("Activity", "VPN 服务已连接")
            updateUIState()
        }
        
        override fun onServiceDisconnected(name: ComponentName?) {
            SelectableLogUtils.i("Activity", "VPN 服务已断开")
            isConnected = false
            updateUIState()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // 初始化视图
        initViews()
        
        // 设置默认值
        setDefaultValues()
        
        // 更新初始状态
        updateUIState()
        
        // 记录启动
        SelectableLogUtils.logServiceLifecycle("EnhancedMainActivity", "onCreate")
    }
    
    override fun onResume() {
        super.onResume()
        // 检查服务状态
        checkServiceStatus()
        updateUIState()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        try {
            unbindService(vpnServiceConnection)
        } catch (e: Exception) {
            // 忽略未绑定服务的异常
        }
        SelectableLogUtils.logServiceLifecycle("EnhancedMainActivity", "onDestroy")
    }
    
    /**
     * 初始化视图
     */
    private fun initViews() {
        editServer = findViewById(R.id.editServer)
        editPort = findViewById(R.id.editPort)
        editUsername = findViewById(R.id.editUsername)
        editPassword = findViewById(R.id.editPassword)
        btnConnect = findViewById(R.id.btnConnect)
        btnDisconnect = findViewById(R.id.btnDisconnect)
        btnLogs = findViewById(R.id.btnLogs)
        textStatus = findViewById(R.id.textStatus)
        textConnectionInfo = findViewById(R.id.textConnectionInfo)
        
        // 设置按钮点击事件
        btnConnect.setOnClickListener {
            connectVpn()
        }
        
        btnDisconnect.setOnClickListener {
            disconnectVpn()
        }
        
        btnLogs.setOnClickListener {
            openLogsActivity()
        }
        
        // 长按日志按钮查看快速日志
        btnLogs.setOnLongClickListener {
            showQuickLogs()
            true
        }
    }
    
    /**
     * 设置默认值
     */
    private fun setDefaultValues() {
        editServer.setText("104.244.90.202")
        editPort.setText("18443")
        editUsername.setText("demo")
        editPassword.setText("demo123")
    }
    
    /**
     * 连接 VPN
     */
    private fun connectVpn() {
        if (isConnecting || isConnected) {
            Toast.makeText(this, "正在连接或已连接", Toast.LENGTH_SHORT).show()
            return
        }
        
        val server = editServer.text.toString().trim()
        val portStr = editPort.text.toString().trim()
        val username = editUsername.text.toString().trim()
        val password = editPassword.text.toString().trim()
        
        // 验证输入
        if (server.isEmpty()) {
            Toast.makeText(this, "请输入服务器地址", Toast.LENGTH_SHORT).show()
            return
        }
        
        val port = try {
            portStr.toInt()
        } catch (e: NumberFormatException) {
            Toast.makeText(this, "端口号格式错误", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (port < 1 || port > 65535) {
            Toast.makeText(this, "端口号范围错误 (1-65535)", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (username.isEmpty()) {
            Toast.makeText(this, "请输入用户名", Toast.LENGTH_SHORT).show()
            return
        }
        
        // 记录连接尝试
        SelectableLogUtils.logConnectionState("连接中", "server=$server:$port, user=$username")
        
        // 准备 VPN 服务
        val intent = VpnService.prepare(this)
        if (intent != null) {
            // 需要 VPN 权限
            startActivityForResult(intent, VPN_REQUEST_CODE)
            SelectableLogUtils.i("Activity", "请求 VPN 权限")
        } else {
            // 已有权限，直接启动
            startVpnService(server, port, username, password)
        }
    }
    
    /**
     * 启动 VPN 服务
     */
    private fun startVpnService(server: String, port: Int, username: String, password: String) {
        isConnecting = true
        updateUIState()
        
        SelectableLogUtils.i("Activity", "启动 VPN 服务: $server:$port")
        
        val serviceIntent = Intent(this, EnhancedTunVpnService::class.java).apply {
            putExtra("server", server)
            putExtra("port", port)
            putExtra("username", username)
            putExtra("password", password)
        }
        
        // 启动服务
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
        
        // 绑定服务以获取状态
        bindService(
            serviceIntent,
            vpnServiceConnection,
            Context.BIND_AUTO_CREATE
        )
        
        // 更新状态
        textStatus.text = "正在连接..."
        textConnectionInfo.text = "服务器: $server:$port\n用户: $username"
        
        Toast.makeText(this, "正在连接 VPN...", Toast.LENGTH_SHORT).show()
    }
    
    /**
     * 断开 VPN
     */
    private fun disconnectVpn() {
        if (!isConnected && !isConnecting) {
            Toast.makeText(this, "未连接 VPN", Toast.LENGTH_SHORT).show()
            return
        }
        
        SelectableLogUtils.logStopOperation("Activity", true, "用户点击断开按钮")
        
        // 发送停止意图
        val stopIntent = Intent(this, EnhancedTunVpnService::class.java).apply {
            action = EnhancedTunVpnService.STOP_ACTION
        }
        
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            startForegroundService(stopIntent)
        } else {
            startService(stopIntent)
        }
        
        // 更新状态
        isConnecting = false
        isConnected = false
        updateUIState()
        
        Toast.makeText(this, "正在断开 VPN...", Toast.LENGTH_SHORT).show()
    }
    
    /**
     * 打开日志界面
     */
    private fun openLogsActivity() {
        val intent = Intent(this, SelectableLogActivity::class.java)
        startActivity(intent)
    }
    
    /**
     * 显示快速日志
     */
    private fun showQuickLogs() {
        val recentLogs = SelectableLogUtils.getRecentLogs(10)
        if (recentLogs.isNotEmpty()) {
            Toast.makeText(this, "最近10条日志已复制", Toast.LENGTH_SHORT).show()
            SelectableLogUtils.copyLogToClipboard(this, recentLogs)
        } else {
            Toast.makeText(this, "暂无日志", Toast.LENGTH_SHORT).show()
        }
    }
    
    /**
     * 检查服务状态
     */
    private fun checkServiceStatus() {
        isConnected = EnhancedTunVpnService.isRunning
        isConnecting = false // 假设不在连接中
        
        if (isConnected) {
            SelectableLogUtils.d("Activity", "检测到 VPN 服务正在运行")
        }
    }
    
    /**
     * 更新 UI 状态
     */
    private fun updateUIState() {
        runOnUiThread {
            when {
                isConnecting -> {
                    btnConnect.isEnabled = false
                    btnConnect.text = "连接中..."
                    btnDisconnect.isEnabled = true
                    btnDisconnect.text = "停止"
                    textStatus.text = "正在连接..."
                    textStatus.setTextColor(getColor(android.R.color.holo_orange_dark))
                }
                isConnected -> {
                    btnConnect.isEnabled = false
                    btnConnect.text = "已连接"
                    btnDisconnect.isEnabled = true
                    btnDisconnect.text = "断开连接"
                    textStatus.text = "已连接"
                    textStatus.setTextColor(getColor(android.R.color.holo_green_dark))
                }
                else -> {
                    btnConnect.isEnabled = true
                    btnConnect.text = "连接"
                    btnDisconnect.isEnabled = false
                    btnDisconnect.text = "断开连接"
                    textStatus.text = "未连接"
                    textStatus.setTextColor(getColor(android.R.color.holo_red_dark))
                    
                    // 显示最后错误（如果有）
                    EnhancedTunVpnService.lastError?.let { error ->
                        textConnectionInfo.text = "最后错误: $error"
                    }
                }
            }
            
            // 更新连接信息
            if (!isConnected && !isConnecting) {
                val server = editServer.text.toString().trim()
                val port = editPort.text.toString().trim()
                val username = editUsername.text.toString().trim()
                
                if (server.isNotEmpty() && port.isNotEmpty()) {
                    textConnectionInfo.text = "准备连接: $server:$port\n用户: $username"
                } else {
                    textConnectionInfo.text = "请输入连接信息"
                }
            }
        }
    }
    
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        
        if (requestCode == VPN_REQUEST_CODE) {
            if (resultCode == RESULT_OK) {
                // VPN 权限已授予
                val server = editServer.text.toString().trim()
                val port = editPort.text.toString().trim().toIntOrNull() ?: 18443
                val username = editUsername.text.toString().trim()
                val password = editPassword.text.toString().trim()
                
                startVpnService(server, port, username, password)
                SelectableLogUtils.i("Activity", "VPN 权限已授予，开始连接")
            } else {
                // 用户拒绝了 VPN 权限
                isConnecting = false
                updateUIState()
                Toast.makeText(this, "需要 VPN 权限才能连接", Toast.LENGTH_LONG).show()
                SelectableLogUtils.logConnectionState("权限拒绝", "用户未授予 VPN 权限")
            }
        }
    }
    
    companion object {
        private const val VPN_REQUEST_CODE = 1001
    }
}