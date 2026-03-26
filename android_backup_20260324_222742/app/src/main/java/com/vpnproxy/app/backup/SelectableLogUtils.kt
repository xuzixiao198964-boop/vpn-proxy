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
 * 增强的日志工具类 - 支持可选择和复制的日志
 */
object SelectableLogUtils {
    
    private const val TAG = "VpnProxy"
    private val logQueue = ConcurrentLinkedQueue<LogEntry>()
    private const val MAX_LOG_ENTRIES = 1000
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())
    
    data class LogEntry(
        val timestamp: String,
        val level: String,
        val tag: String,
        val message: String,
        val stackTrace: String? = null
    )
    
    // 日志级别
    const val LEVEL_VERBOSE = 0
    const val LEVEL_DEBUG = 1
    const val LEVEL_INFO = 2
    const val LEVEL_WARN = 3
    const val LEVEL_ERROR = 4
    
    var logLevel = LEVEL_DEBUG  // 默认日志级别
    var enableAndroidLog = true  // 是否同时输出到 Android Log
    
    /**
     * 记录详细日志
     */
    fun v(tag: String = TAG, message: String, throwable: Throwable? = null) {
        logInternal("V", tag, message, throwable)
        if (enableAndroidLog && logLevel <= LEVEL_VERBOSE) {
            Log.v(tag, message, throwable)
        }
    }
    
    fun d(tag: String = TAG, message: String, throwable: Throwable? = null) {
        logInternal("D", tag, message, throwable)
        if (enableAndroidLog && logLevel <= LEVEL_DEBUG) {
            Log.d(tag, message, throwable)
        }
    }
    
    fun i(tag: String = TAG, message: String, throwable: Throwable? = null) {
        logInternal("I", tag, message, throwable)
        if (enableAndroidLog && logLevel <= LEVEL_INFO) {
            Log.i(tag, message, throwable)
        }
    }
    
    fun w(tag: String = TAG, message: String, throwable: Throwable? = null) {
        logInternal("W", tag, message, throwable)
        if (enableAndroidLog && logLevel <= LEVEL_WARN) {
            Log.w(tag, message, throwable)
        }
    }
    
    fun e(tag: String = TAG, message: String, throwable: Throwable? = null) {
        logInternal("E", tag, message, throwable)
        if (enableAndroidLog && logLevel <= LEVEL_ERROR) {
            Log.e(tag, message, throwable)
        }
    }
    
    /**
     * 内部日志记录
     */
    private fun logInternal(level: String, tag: String, message: String, throwable: Throwable?) {
        val timestamp = dateFormat.format(Date())
        val stackTrace = throwable?.let { getStackTraceString(it) }
        
        val entry = LogEntry(timestamp, level, tag, message, stackTrace)
        logQueue.add(entry)
        
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
     * 获取格式化后的日志（用于显示）
     */
    fun getFormattedLogs(): String {
        return logQueue.joinToString("\n") { entry ->
            buildString {
                append(entry.timestamp)
                append(" [").append(entry.level).append("] ")
                append(entry.tag).append(": ")
                append(entry.message)
                entry.stackTrace?.let {
                    append("\n").append(it)
                }
            }
        }
    }
    
    /**
     * 获取纯文本日志（用于复制）
     */
    fun getPlainLogs(): String {
        return logQueue.joinToString("\n") { entry ->
            "${entry.timestamp} [${entry.level}] ${entry.tag}: ${entry.message}" +
            (entry.stackTrace?.let { "\n$it" } ?: "")
        }
    }
    
    /**
     * 获取最近 N 条日志
     */
    fun getRecentLogs(count: Int = 100): String {
        val logs = logQueue.toList()
        val startIndex = maxOf(0, logs.size - count)
        return logs.subList(startIndex, logs.size).joinToString("\n") { entry ->
            "${entry.timestamp} [${entry.level}] ${entry.tag}: ${entry.message}"
        }
    }
    
    /**
     * 获取所有日志条目
     */
    fun getAllEntries(): List<LogEntry> {
        return logQueue.toList()
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
    fun copyLogsToClipboard(context: Context) {
        val logs = getPlainLogs()
        if (logs.isNotEmpty()) {
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("VpnProxy Logs", logs)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(context, "日志已复制到剪贴板", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(context, "暂无日志可复制", Toast.LENGTH_SHORT).show()
        }
    }
    
    /**
     * 复制指定日志到剪贴板
     */
    fun copyLogToClipboard(context: Context, logText: String) {
        if (logText.isNotEmpty()) {
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = ClipData.newPlainText("VpnProxy Log", logText)
            clipboard.setPrimaryClip(clip)
            Toast.makeText(context, "已复制到剪贴板", Toast.LENGTH_SHORT).show()
        }
    }
    
    /**
     * 生成诊断报告
     */
    fun generateDiagnosticReport(context: Context): String {
        val sb = StringBuilder()
        
        sb.append("=== VPN Proxy 诊断报告 ===\n")
        sb.append("生成时间: ").append(dateFormat.format(Date())).append("\n")
        sb.append("\n")
        
        // 应用信息
        sb.append("应用信息:\n")
        try {
            val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
            sb.append("  包名: ").append(packageInfo.packageName).append("\n")
            sb.append("  版本: ").append(packageInfo.versionName).append("\n")
            sb.append("  版本号: ").append(packageInfo.versionCode).append("\n")
        } catch (e: Exception) {
            sb.append("  获取应用信息失败: ").append(e.message).append("\n")
        }
        
        // 日志统计
        sb.append("\n日志统计:\n")
        val entries = getAllEntries()
        val levelCount = entries.groupingBy { it.level }.eachCount()
        sb.append("  总日志数: ").append(entries.size).append("\n")
        levelCount.forEach { (level, count) ->
            sb.append("  ").append(level).append(": ").append(count).append(" 条\n")
        }
        
        // 最近错误
        val errors = entries.filter { it.level == "E" }.takeLast(5)
        if (errors.isNotEmpty()) {
            sb.append("\n最近错误:\n")
            errors.forEach { error ->
                sb.append("  ").append(error.timestamp).append(": ").append(error.message).append("\n")
                error.stackTrace?.let {
                    sb.append("    堆栈: ").append(it.split("\n").firstOrNull()).append("\n")
                }
            }
        }
        
        // 最近日志（摘要）
        sb.append("\n最近日志摘要（最后20条）:\n")
        val recentLogs = getRecentLogs(20)
        sb.append(recentLogs)
        
        return sb.toString()
    }
    
    /**
     * 记录连接状态变化
     */
    fun logConnectionState(state: String, details: String = "") {
        i("Connection", "状态: $state ${if (details.isNotEmpty()) "($details)" else ""}")
    }
    
    /**
     * 记录停止操作
     */
    fun logStopOperation(caller: String, success: Boolean, message: String = "") {
        val status = if (success) "成功" else "失败"
        w("Stop", "$caller 停止操作: $status ${if (message.isNotEmpty()) "($message)" else ""}")
    }
    
    /**
     * 记录服务生命周期
     */
    fun logServiceLifecycle(service: String, action: String, details: String = "") {
        i("Service", "$service: $action ${if (details.isNotEmpty()) "($details)" else ""}")
    }
}