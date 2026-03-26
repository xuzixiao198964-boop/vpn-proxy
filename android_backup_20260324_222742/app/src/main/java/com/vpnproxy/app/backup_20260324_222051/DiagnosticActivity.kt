package com.vpnproxy.app

import android.content.Intent
import android.os.Bundle
import android.text.method.ScrollingMovementMethod
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * 诊断信息页面，显示日志和网络诊断信息
 */
class DiagnosticActivity : AppCompatActivity() {
    
    private lateinit var textDiagnosticInfo: TextView
    private lateinit var textLogs: TextView
    private lateinit var btnRefresh: Button
    private lateinit var btnCopyDiagnostic: Button
    private lateinit var btnCopyLogs: Button
    private lateinit var btnBack: Button
    private lateinit var btnTestConnection: Button
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_diagnostic)
        
        // 初始化视图
        textDiagnosticInfo = findViewById(R.id.textDiagnosticInfo)
        textLogs = findViewById(R.id.textLogs)
        btnRefresh = findViewById(R.id.btnRefresh)
        btnCopyDiagnostic = findViewById(R.id.btnCopyDiagnostic)
        btnCopyLogs = findViewById(R.id.btnCopyLogs)
        btnBack = findViewById(R.id.btnBack)
        btnTestConnection = findViewById(R.id.btnTestConnection)
        
        // 设置滚动
        textDiagnosticInfo.movementMethod = ScrollingMovementMethod()
        textLogs.movementMethod = ScrollingMovementMethod()
        
        // 加载数据
        refreshDiagnosticInfo()
        refreshLogs()
        
        // 按钮点击事件
        btnRefresh.setOnClickListener {
            refreshDiagnosticInfo()
            refreshLogs()
        }
        
        btnCopyDiagnostic.setOnClickListener {
            val diagnosticText = textDiagnosticInfo.text.toString()
            if (diagnosticText.isNotEmpty()) {
                LogUtils.copyLogsToClipboard(this, diagnosticText)
            }
        }
        
        btnCopyLogs.setOnClickListener {
            val logsText = textLogs.text.toString()
            if (logsText.isNotEmpty()) {
                LogUtils.copyLogsToClipboard(this, logsText)
            }
        }
        
        btnBack.setOnClickListener {
            finish()
        }
        
        btnTestConnection.setOnClickListener {
            // 获取主Activity中的服务器配置
            val host = intent.getStringExtra("host") ?: ""
            val port = intent.getIntExtra("port", 18443)
            val username = intent.getStringExtra("username") ?: ""
            
            if (host.isNotEmpty() && username.isNotEmpty()) {
                testConnection(host, port, username)
            } else {
                textLogs.text = "错误: 未提供服务器配置信息\n请从主页面进入诊断页面"
            }
        }
    }
    
    /**
     * 刷新诊断信息
     */
    private fun refreshDiagnosticInfo() {
        val diagnosticInfo = LogUtils.generateDiagnosticInfo(this)
        textDiagnosticInfo.text = diagnosticInfo
    }
    
    /**
     * 刷新日志
     */
    private fun refreshLogs() {
        val logs = LogUtils.getRecentLogs(100)
        textLogs.text = if (logs.isNotEmpty()) {
            logs
        } else {
            "暂无日志记录"
        }
    }
    
    /**
     * 测试连接
     */
    private fun testConnection(host: String, port: Int, username: String) {
        textLogs.text = "开始连接测试...\n"
        
        // 在后台线程执行测试
        Thread {
            val testResults = mutableMapOf<String, String>()
            
            try {
                // 测试1: DNS解析
                LogUtils.i("ConnectionTest", "测试DNS解析: $host")
                runOnUiThread {
                    textLogs.append("1. DNS解析测试...\n")
                }
                
                try {
                    val addresses = java.net.InetAddress.getAllByName(host)
                    testResults["DNS解析"] = "成功 - 解析到 ${addresses.size} 个IP地址"
                    runOnUiThread {
                        textLogs.append("   成功: 解析到 ${addresses.size} 个IP\n")
                        for (addr in addresses) {
                            textLogs.append("     - ${addr.hostAddress}\n")
                        }
                    }
                } catch (e: Exception) {
                    testResults["DNS解析"] = "失败 - ${e.message}"
                    runOnUiThread {
                        textLogs.append("   失败: ${e.message}\n")
                    }
                }
                
                // 测试2: 端口连接
                LogUtils.i("ConnectionTest", "测试端口连接: $host:$port")
                runOnUiThread {
                    textLogs.append("\n2. 端口连接测试 ($host:$port)...\n")
                }
                
                try {
                    val socket = java.net.Socket()
                    socket.soTimeout = 5000
                    socket.connect(java.net.InetSocketAddress(host, port), 5000)
                    socket.close()
                    testResults["端口连接"] = "成功 - 端口可访问"
                    runOnUiThread {
                        textLogs.append("   成功: 端口可访问\n")
                    }
                } catch (e: Exception) {
                    testResults["端口连接"] = "失败 - ${e.message}"
                    runOnUiThread {
                        textLogs.append("   失败: ${e.message}\n")
                    }
                }
                
                // 测试3: HTTP访问测试 (Google)
                LogUtils.i("ConnectionTest", "测试HTTP访问")
                runOnUiThread {
                    textLogs.append("\n3. HTTP访问测试 (Google)...\n")
                }
                
                try {
                    val url = java.net.URL("https://www.google.com")
                    val connection = url.openConnection() as java.net.HttpURLConnection
                    connection.connectTimeout = 10000
                    connection.readTimeout = 10000
                    connection.requestMethod = "HEAD"
                    
                    val responseCode = connection.responseCode
                    testResults["HTTP访问"] = if (responseCode == 200) {
                        "成功 - HTTP 200"
                    } else {
                        "异常 - HTTP $responseCode"
                    }
                    runOnUiThread {
                        textLogs.append("   响应码: $responseCode\n")
                    }
                    connection.disconnect()
                } catch (e: Exception) {
                    testResults["HTTP访问"] = "失败 - ${e.message}"
                    runOnUiThread {
                        textLogs.append("   失败: ${e.message}\n")
                    }
                }
                
                // 生成测试报告
                val report = LogUtils.generateConnectionTestReport(host, port, username, testResults)
                
                runOnUiThread {
                    textLogs.append("\n" + "="*40 + "\n")
                    textLogs.append("连接测试完成!\n")
                    textLogs.append("="*40 + "\n")
                    
                    // 显示测试摘要
                    textLogs.append("\n测试摘要:\n")
                    for ((testName, result) in testResults) {
                        val status = if ("成功" in result) "✅" else "❌"
                        textLogs.append("$status $testName: $result\n")
                    }
                    
                    // 添加复制测试报告按钮
                    textLogs.append("\n提示: 点击'复制诊断信息'可复制完整测试报告\n")
                }
                
                // 保存测试报告到诊断信息
                runOnUiThread {
                    textDiagnosticInfo.text = report + "\n\n" + textDiagnosticInfo.text.toString()
                }
                
            } catch (e: Exception) {
                LogUtils.e("ConnectionTest", "连接测试异常", e)
                runOnUiThread {
                    textLogs.append("\n测试异常: ${e.message}\n")
                    textLogs.append("堆栈跟踪: ${LogUtils.getStackTraceString(e)}\n")
                }
            }
        }.start()
    }
    
    companion object {
        /**
         * 启动诊断页面
         */
        fun start(context: AppCompatActivity, host: String = "", port: Int = 18443, username: String = "") {
            val intent = Intent(context, DiagnosticActivity::class.java).apply {
                putExtra("host", host)
                putExtra("port", port)
                putExtra("username", username)
            }
            context.startActivity(intent)
        }
    }
}