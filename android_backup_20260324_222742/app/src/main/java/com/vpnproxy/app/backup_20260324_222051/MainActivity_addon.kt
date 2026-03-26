// 添加到 MainActivity.kt 文件末尾的代码

import com.vpnproxy.app.LogUtils  // 需要添加这个导入

// 在 onCreate 方法中，找到 btnStop 的点击监听器之后添加：

/*
        btnStop.setOnClickListener {
            // ... 现有代码 ...
        }

        // 添加诊断按钮监听
        val btnDiagnostic = findViewById<Button>(R.id.btnDiagnostic)
        btnDiagnostic.setOnClickListener {
            val host = editHost.text.toString().trim()
            val port = editPort.text.toString().trim().toIntOrNull() ?: 18443
            val user = editUser.text.toString().trim()
            DiagnosticActivity.start(this, host, port, user)
        }
*/

// 在 startVpnService 方法的最后添加日志记录：

/*
        findViewById<Button>(R.id.btnStart).isEnabled = false
        findViewById<Button>(R.id.btnStop).isEnabled = true
        
        // 记录连接尝试
        LogUtils.i("MainActivity", "尝试连接到服务器: $host:$port, 用户: $user")
*/