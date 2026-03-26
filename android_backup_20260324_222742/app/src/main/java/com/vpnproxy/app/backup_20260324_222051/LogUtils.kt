package com.vpnproxy.app

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.util.Log
import android.widget.Toast
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ConcurrentLinkedQueue

/**
 * 增强的日志工具类，支持：
 * 1. 详细的日志记录
 * 2. 日志复制功能
 * 3. 网络诊断信息
 * 4. 错误堆栈跟踪
 */
object LogUtils {
    
    private const val TAG = "VpnProxy"
    private val logQueue = ConcurrentLinkedQueue<String>()
    private const val MAX_LOG_ENTRIES = 1000
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())
    
    // 日志级别
    const val LEVEL_VERBOSE = 0
    const val LEVEL_DEBUG = 1
    const val LEVEL_INFO = 2
    const val LEVEL_WARN = 3
    const val LEVEL_ERROR = 4
    
    var logLevel = LEVEL_DEBUG  // 默认日志级别
    
    /**
     * 记录详细日志
     */
    fun v(tag: String = TAG, message: String, throwable: Throwable? = null) {
        if (logLevel <= LEVEL_VERBOSE) {
            Log.v(tag, message, throwable)
            addToLogQueue("V", tag, message, throwable)
        }
    }
    
    fun d(tag: String = TAG, message: String, throwable: Throwable? = null) {
        if (logLevel <= LEVEL_DEBUG) {
            Log.d(tag, message, throwable)
            addToLogQueue("D", tag, message, throwable)
        }
    }
    
    fun i(tag: String = TAG, message: String, throwable: Throwable? = null) {
        if (logLevel <= LEVEL_INFO) {
            Log.i(tag, message, throwable)
            addToLogQueue("I", tag, message, throwable)
        }
    }
    
    fun w(tag: String = TAG, message: String, throwable: Throwable? = null) {
        if (logLevel <= LEVEL_WARN) {
            Log.w(tag, message, throwable)
            addToLogQueue("W", tag, message, throwable)
        }
    }
    
    fun e(tag: String = TAG, message: String, throwable: Throwable? = null) {
        if (logLevel <= LEVEL_ERROR) {
            Log.e(tag, message, throwable)
            addToLogQueue("E", tag, message, throwable)
        }
    }
    
    /**
     * 添加日志到队列
     */
    private fun addToLogQueue(level: String, tag: String, message: String, throwable: Throwable?) {
        val timestamp = dateFormat.format(Date())
        val logEntry = StringBuilder()
            .append(timestamp)
            .append(" [").append(level).append("] ")
            .append(tag).append(": ")
            .append(message)
        
        if (throwable != null) {
            logEntry.append("\n").append(getStackTraceString(throwable))
        }
        
        logQueue.add(logEntry.toString())
        
        // 限制队列大小
        while (logQueue.size > MAX_LOG_ENTRIES) {
            logQueue.poll()
        }
    }
    
    /**
     * 获取堆栈跟踪字符串
     */
    fun getStackTraceString(throwable: Throwable): String {
        val sw = StringWriter()
        val pw = PrintWriter(sw)
        throwable.printStackTrace(pw)
        pw.flush()
        return sw.toString()
    }
    
    /**
     * 获取所有日志
     */
    fun getAllLogs(): String {
        return logQueue.joinToString("\n")
    }
    
    /**
     * 获取最近 N 条日志
     */
    fun getRecentLogs(count: Int = 100): String {
        val logs = logQueue.toList()
        val startIndex = maxOf(0, logs.size - count)
        return logs.subList(startIndex, logs.size).joinToString("\n")
    }
    
    /**
     * 清空日志
     */
    fun clearLogs() {
        logQueue.clear()
    }
    
    /**
     * 复制日志到剪贴板
     */
    fun copyLogsToClipboard(context: Context, logs: String) {
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = ClipData.newPlainText("VpnProxy Logs", logs)
        clipboard.setPrimaryClip(clip)
        Toast.makeText(context, "日志已复制到剪贴板", Toast.LENGTH_SHORT).show()
    }
    
    /**
     * 生成网络诊断信息
     */
    fun generateDiagnosticInfo(context: Context): String {
        val sb = StringBuilder()
        
        sb.append("=== VPN Proxy 诊断信息 ===\n")
        sb.append("生成时间: ").append(dateFormat.format(Date())).append("\n")
        sb.append("\n")
        
        // 应用信息
        sb.append("应用信息:\n")
        try {
            val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
            sb.append("  版本: ").append(packageInfo.versionName).append("\n")
            sb.append("  版本号: ").append(packageInfo.versionCode).append("\n")
        } catch (e: Exception) {
            sb.append("  获取应用信息失败: ").append(e.message).append("\n")
        }
        
        // 设备信息
        sb.append("\n设备信息:\n")
        sb.append("  Android 版本: ").append(Build.VERSION.RELEASE).append("\n")
        sb.append("  SDK 版本: ").append(Build.VERSION.SDK_INT).append("\n")
        sb.append("  设备型号: ").append(Build.MODEL).append("\n")
        sb.append("  品牌: ").append(Build.BRAND).append("\n")
        
        // 网络信息
        sb.append("\n网络信息:\n")
        try {
            val networkInterfaces = NetworkInterface.getNetworkInterfaces()
            for (ni in Collections.list(networkInterfaces)) {
                if (ni.isUp && !ni.isLoopback) {
                    sb.append("  接口: ").append(ni.displayName).append("\n")
                    val addresses = ni.inetAddresses
                    while (addresses.hasMoreElements()) {
                        val addr = addresses.nextElement()
                        sb.append("    IP: ").append(addr.hostAddress).append("\n")
                    }
                }
            }
        } catch (e: Exception) {
            sb.append("  获取网络信息失败: ").append(e.message).append("\n")
        }
        
        // 最近日志
        sb.append("\n最近日志 (最后50条):\n")
        sb.append(getRecentLogs(50))
        
        return sb.toString()
    }
    
    /**
     * 生成连接测试报告
     */
    fun generateConnectionTestReport(
        host: String,
        port: Int,
        username: String,
        testResults: Map<String, String>
    ): String {
        val sb = StringBuilder()
        
        sb.append("=== 连接测试报告 ===\n")
        sb.append("测试时间: ").append(dateFormat.format(Date())).append("\n")
        sb.append("服务器: ").append(host).append(":").append(port).append("\n")
        sb.append("用户名: ").append(username).append("\n")
        sb.append("\n")
        
        sb.append("测试结果:\n")
        for ((testName, result) in testResults) {
            sb.append("  ").append(testName).append(": ").append(result).append("\n")
        }
        
        sb.append("\n相关日志:\n")
        sb.append(getRecentLogs(30))
        
        return sb.toString()
    }
}