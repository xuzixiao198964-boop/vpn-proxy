package com.vpnproxy.app

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private val vpnPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult(),
    ) { result ->
        if (result.resultCode == RESULT_OK) {
            startVpnService()
        } else {
            Toast.makeText(this, "需要 VPN 权限才能将系统流量导入代理", Toast.LENGTH_LONG).show()
        }
    }

    /** Android 13+：无此权限时前台通知可能被系统隐藏，状态栏无图标 */
    private val notifPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) {
        launchVpnPrepareFlow()
    }

    private lateinit var editHost: EditText
    private lateinit var editPort: EditText
    private lateinit var editUser: EditText
    private lateinit var editPass: EditText
    private lateinit var editSocks: EditText
    private lateinit var textStatus: TextView
    private lateinit var textLogs: TextView
    private val logEntries = mutableListOf<String>()
    private val maxLogEntries = 50

    // 广播接收器，用于接收应用内日志
    private val logReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                "APP_INTERNAL_ERROR_LOG" -> {
                    val error = intent.getStringExtra("error") ?: "未知错误"
                    val timestamp = intent.getLongExtra("timestamp", System.currentTimeMillis())
                    addLogEntry("ERROR", error, timestamp)
                }
                "APP_INTERNAL_LOG" -> {
                    val type = intent.getStringExtra("type") ?: "INFO"
                    val message = intent.getStringExtra("message") ?: ""
                    val timestamp = intent.getLongExtra("timestamp", System.currentTimeMillis())
                    addLogEntry(type, message, timestamp)
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        editHost = findViewById(R.id.editHost)
        editPort = findViewById(R.id.editPort)
        editUser = findViewById(R.id.editUser)
        editPass = findViewById(R.id.editPass)
        editSocks = findViewById(R.id.editSocksPort)
        val btnStart = findViewById<Button>(R.id.btnStart)
        val btnStop = findViewById<Button>(R.id.btnStop)
        textStatus = findViewById(R.id.textStatus)
        textLogs = findViewById(R.id.textLogs)

        // 设置默认值（SSH服务器信息）
        editHost.setText("104.244.90.202")
        editPort.setText("22")
        editUser.setText("root")
        editPass.setText("v9wSxMxg92dp")
        editSocks.setText("1080")

        // 注册广播接收器
        val filter = IntentFilter().apply {
            addAction("APP_INTERNAL_ERROR_LOG")
            addAction("APP_INTERNAL_LOG")
        }
        registerReceiver(logReceiver, filter)

        btnStart.setOnClickListener {
            val host = editHost.text.toString().trim()
            val user = editUser.text.toString().trim()
            if (host.isEmpty() || user.isEmpty()) {
                Toast.makeText(this, "请填写地址与用户名", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            if (Build.VERSION.SDK_INT >= 33) {
                when {
                    ContextCompat.checkSelfPermission(
                        this,
                        Manifest.permission.POST_NOTIFICATIONS,
                    ) == PackageManager.PERMISSION_GRANTED -> launchVpnPrepareFlow()
                    else -> notifPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                }
            } else {
                launchVpnPrepareFlow()
            }
        }

        btnStop.setOnClickListener {
            val stopIntent = Intent(this, TunVpnService::class.java).apply {
                action = TunVpnService.ACTION_STOP
            }
            startService(stopIntent)
            textStatus.text = "状态：未连接"
            btnStart.isEnabled = true
            btnStop.isEnabled = false
            addLogEntry("INFO", "VPN连接已停止", System.currentTimeMillis())
        }

        // 添加初始日志
        addLogEntry("INFO", "应用启动", System.currentTimeMillis())
        addLogEntry("INFO", "SSH服务器已预配置: 104.244.90.202:22", System.currentTimeMillis())
    }

    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(logReceiver)
    }

    private fun launchVpnPrepareFlow() {
        val prep = VpnService.prepare(this)
        if (prep != null) {
            vpnPermissionLauncher.launch(prep)
        } else {
            startVpnService()
        }
    }

    private fun startVpnService() {
        val host = editHost.text.toString().trim()
        val port = editPort.text.toString().trim().toIntOrNull() ?: 18443
        val user = editUser.text.toString().trim()
        val pass = editPass.text.toString()
        val socksPort = editSocks.text.toString().trim().toIntOrNull() ?: 1080
        if (host.isEmpty() || user.isEmpty()) {
            Toast.makeText(this, "请填写地址与用户名", Toast.LENGTH_SHORT).show()
            return
        }

        addLogEntry("INFO", "正在连接到 $host:$port...", System.currentTimeMillis())

        val svcIntent = Intent(this, TunVpnService::class.java).apply {
            putExtra(TunVpnService.EXTRA_HOST, host)
            putExtra(TunVpnService.EXTRA_PORT, port)
            putExtra(TunVpnService.EXTRA_USER, user)
            putExtra(TunVpnService.EXTRA_PASS, pass)
            putExtra(TunVpnService.EXTRA_SOCKS_PORT, socksPort)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            ContextCompat.startForegroundService(this, svcIntent)
        } else {
            startService(svcIntent)
        }
        textStatus.text = "状态：VPN 已启动（系统流量经 SOCKS5 127.0.0.1:$socksPort）"
        findViewById<Button>(R.id.btnStart).isEnabled = false
        findViewById<Button>(R.id.btnStop).isEnabled = true
    }

    private fun addLogEntry(type: String, message: String, timestamp: Long) {
        val timeStr = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date(timestamp))
        val entry = "[$timeStr] [$type] $message"
        
        logEntries.add(entry)
        if (logEntries.size > maxLogEntries) {
            logEntries.removeAt(0)
        }
        
        updateLogDisplay()
    }

    private fun updateLogDisplay() {
        val logText = logEntries.joinToString("\n")
        textLogs.text = logText
    }
}