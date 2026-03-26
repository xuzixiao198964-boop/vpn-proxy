package com.vpnproxy.app

import android.content.Intent
import android.os.Bundle
import android.text.method.ScrollingMovementMethod
import android.view.Menu
import android.view.MenuItem
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * 可选择文本的日志查看界面
 */
class SelectableLogActivity : AppCompatActivity() {
    
    private lateinit var textLogs: TextView
    private lateinit var btnRefresh: Button
    private lateinit var btnCopyAll: Button
    private lateinit var btnClear: Button
    private lateinit var btnBack: Button
    private lateinit var btnDiagnostic: Button
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_selectable_log)
        
        // 初始化视图
        textLogs = findViewById(R.id.textSelectableLogs)
        btnRefresh = findViewById(R.id.btnRefreshLogs)
        btnCopyAll = findViewById(R.id.btnCopyAllLogs)
        btnClear = findViewById(R.id.btnClearLogs)
        btnBack = findViewById(R.id.btnBackFromLogs)
        btnDiagnostic = findViewById(R.id.btnGenerateDiagnostic)
        
        // 设置文本可选择
        textLogs.setTextIsSelectable(true)
        textLogs.movementMethod = ScrollingMovementMethod()
        
        // 加载初始日志
        refreshLogs()
        
        // 按钮点击事件
        btnRefresh.setOnClickListener {
            refreshLogs()
        }
        
        btnCopyAll.setOnClickListener {
            val logs = textLogs.text.toString()
            if (logs.isNotEmpty()) {
                SelectableLogUtils.copyLogToClipboard(this, logs)
            } else {
                SelectableLogUtils.copyLogsToClipboard(this)
            }
        }
        
        btnClear.setOnClickListener {
            SelectableLogUtils.clearLogs()
            refreshLogs()
        }
        
        btnBack.setOnClickListener {
            finish()
        }
        
        btnDiagnostic.setOnClickListener {
            generateDiagnosticReport()
        }
        
        // 添加长按复制单行功能
        textLogs.setOnLongClickListener {
            val selectedText = textLogs.text.substring(
                textLogs.selectionStart,
                textLogs.selectionEnd
            )
            if (selectedText.isNotEmpty()) {
                SelectableLogUtils.copyLogToClipboard(this, selectedText)
                true
            } else {
                false
            }
        }
    }
    
    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.log_menu, menu)
        return true
    }
    
    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.menu_copy_all -> {
                SelectableLogUtils.copyLogsToClipboard(this)
                true
            }
            R.id.menu_clear_logs -> {
                SelectableLogUtils.clearLogs()
                refreshLogs()
                true
            }
            R.id.menu_export_logs -> {
                exportLogs()
                true
            }
            R.id.menu_settings -> {
                openLogSettings()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }
    
    /**
     * 刷新日志显示
     */
    private fun refreshLogs() {
        val logs = SelectableLogUtils.getFormattedLogs()
        textLogs.text = if (logs.isNotEmpty()) {
            logs
        } else {
            "暂无日志记录\n\n点击刷新按钮或开始使用应用来生成日志"
        }
        
        // 自动滚动到底部
        textLogs.post {
            val scrollAmount = textLogs.layout.getLineTop(textLogs.lineCount) - textLogs.height
            if (scrollAmount > 0) {
                textLogs.scrollTo(0, scrollAmount)
            } else {
                textLogs.scrollTo(0, 0)
            }
        }
    }
    
    /**
     * 生成诊断报告
     */
    private fun generateDiagnosticReport() {
        val report = SelectableLogUtils.generateDiagnosticReport(this)
        
        // 显示在日志区域
        textLogs.text = report
        
        // 复制到剪贴板
        SelectableLogUtils.copyLogToClipboard(this, report)
    }
    
    /**
     * 导出日志到文件
     */
    private fun exportLogs() {
        // 这里可以添加导出到文件的功能
        // 暂时只复制到剪贴板
        SelectableLogUtils.copyLogsToClipboard(this)
    }
    
    /**
     * 打开日志设置
     */
    private fun openLogSettings() {
        // 这里可以添加日志设置界面
        // 暂时只显示提示
        SelectableLogUtils.i("Settings", "打开日志设置")
    }
    
    override fun onResume() {
        super.onResume()
        refreshLogs()
    }
}"