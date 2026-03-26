package com.vpnproxy.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.ParcelFileDescriptor
import androidx.core.app.NotificationCompat
import com.vpnproxy.tun2.tun2mobile.Tun2mobile
import java.io.IOException
import java.net.InetAddress
import java.net.NetworkInterface
import java.util.Collections

/**
 * 增强版 VPN 服务 - 集成可选择日志和修复停止问题
 */
class EnhancedTunVpnService : VpnService() {

    companion object {
        const val ACTION_STOP = "com.vpnproxy.app.STOP"
        const val EXTRA_HOST = "host"
        const val EXTRA_PORT = "port"
        const val EXTRA_USER = "user"
        const val EXTRA_PASS = "pass"
        const val EXTRA_SOCKS_PORT = "socks_port"
        
        const val NOTIFICATION_CHANNEL_ID = "vpn_proxy_channel"
        const val NOTIFICATION_ID = 1001
        
        private var instance: EnhancedTunVpnService? = null
        
        fun isRunning(): Boolean {
            return instance?.isServiceRunning ?: false
        }
    }

    private var tunnel: TunnelSession? = null
    private var socks: Socks5Server? = null
    private var worker: Thread? = null
    private var vpnInterface: ParcelFileDescriptor? = null
    
    private val handler = Handler(Looper.getMainLooper())
    private var isServiceRunning = false
    private var stopRequested = false

    inner class LocalBinder : android.os.Binder() {
        fun getService(): EnhancedTunVpnService = this@EnhancedTunVpnService
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        SelectableLogUtils.logServiceLifecycle("EnhancedTunVpnService", "onCreate")
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        SelectableLogUtils.logServiceLifecycle("EnhancedTunVpnService", "onStartCommand", 
            "action: ${intent?.action}, flags: $flags")
        
        if (intent?.action == ACTION_STOP) {
            SelectableLogUtils.logConnectionState("停止请求", "收到停止意图")
            stopRequested = true
            stopAll()
            cleanupAndStop()
            return START_NOT_STICKY
        }

        val host = intent?.getStringExtra(EXTRA_HOST) ?: run {
            SelectableLogUtils.e("Service", "启动失败: 主机地址为空")
            stopSelf()
            return START_NOT_STICKY
        }
        
        val port = intent.getIntExtra(EXTRA_PORT, 18443)
        val user = intent.getStringExtra(EXTRA_USER) ?: run {
            SelectableLogUtils.e("Service", "启动失败: 用户名为空")
            stopSelf()
            return START_NOT_STICKY
        }
        
        val pass = intent.getStringExtra(EXTRA_PASS) ?: ""
        val socksPort = intent.getIntExtra(EXTRA_SOCKS_PORT, 1080)

        SelectableLogUtils.logConnectionState("启动", "主机: $host:$port, 用户: $user, SOCKS: $socksPort")

        // 如果已经在运行，先停止
        if (isServiceRunning) {
            SelectableLogUtils.w("Service", "服务已在运行，先停止")
            stopAll()
        }

        worker = Thread({
            try {
                isServiceRunning = true
                stopRequested = false
                
                // 建立隧道
                SelectableLogUtils.i("Tunnel", "建立隧道连接...")
                tunnel = TunnelSession(host, port, user, pass).apply {
                    start()
                }
                
                // 启动 SOCKS5 服务器
                SelectableLogUtils.i("SOCKS", "启动 SOCKS5 服务器 (端口: $socksPort)...")
                socks = Socks5Server(tunnel!!, socksPort).apply {
                    start()
                }
                
                // 建立 TUN 接口
                SelectableLogUtils.i("TUN", "建立 TUN 接口...")
                establishTun(socksPort)
                
                // 更新通知
                updateNotification("VPN 运行中", "流量经 SOCKS5 127.0.0.1:$socksPort")
                SelectableLogUtils.logConnectionState("运行中", "VPN 服务已启动")
                
            } catch (e: Exception) {
                SelectableLogUtils.e("Service", "VPN 服务启动失败", e)
                cleanupAndStop()
            }
        }, "tunvpn-worker").also { it.start() }

        return START_STICKY
    }

    /**
     * 建立 TUN 接口
     */
    private fun establishTun(socksPort: Int) {
        SelectableLogUtils.i("TUN", "配置 TUN 接口...")
        
        val builder = Builder()
            .setSession("VPN Proxy Tunnel")
            .addAddress("10.0.0.2", 32)
            .addRoute("0.0.0.0", 0)
            .addDnsServer("8.8.8.8")
            .addDnsServer("8.8.4.4")
            .setMtu(1500)
            .setBlocking(true)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            builder.setMetered(false)
        }

        vpnInterface = builder.establish()
        SelectableLogUtils.i("TUN", "TUN 接口已建立: ${vpnInterface?.fd}")
        
        // 启动 tun2socks
        val loopbackIface = loopbackIfaceName()
        SelectableLogUtils.i("TUN", "启动 tun2socks (回环接口: $loopbackIface)...")
        
        Tun2mobile.startTun(
            vpnInterface!!.fd,
            "127.0.0.1",
            socksPort,
            loopbackIface,
            "10.0.0.2",
            "10.0.0.1",
            1500
        )
        
        SelectableLogUtils.i("TUN", "tun2socks 已启动")
    }

    /**
     * 停止所有组件
     */
    private fun stopAll() {
        SelectableLogUtils.logStopOperation("stopAll", true, "开始停止所有组件")
        
        stopRequested = true
        
        // 停止工作线程
        worker?.interrupt()
        try {
            worker?.join(5000)
            SelectableLogUtils.i("Thread", "工作线程已停止")
        } catch (e: Exception) {
            SelectableLogUtils.w("Thread", "停止工作线程超时", e)
        }
        worker = null

        // 停止 tun2socks
        try {
            Tun2mobile.stopTun()
            SelectableLogUtils.i("TUN", "tun2socks 已停止")
        } catch (e: Throwable) {
            SelectableLogUtils.w("TUN", "停止 tun2socks 失败", e)
        }

        // 停止 SOCKS5 服务器
        socks?.stop()
        socks = null
        SelectableLogUtils.i("SOCKS", "SOCKS5 服务器已停止")

        // 停止隧道
        tunnel?.shutdown()
        tunnel = null
        SelectableLogUtils.i("Tunnel", "隧道连接已关闭")

        // 关闭 TUN 接口
        try {
            vpnInterface?.close()
            SelectableLogUtils.i("TUN", "TUN 接口已关闭")
        } catch (e: IOException) {
            SelectableLogUtils.w("TUN", "关闭 TUN 接口失败", e)
        }
        vpnInterface = null
        
        isServiceRunning = false
        SelectableLogUtils.logConnectionState("已停止", "所有组件已停止")
    }

    /**
     * 清理并停止服务
     */
    private fun cleanupAndStop() {
        SelectableLogUtils.logServiceLifecycle("EnhancedTunVpnService", "cleanupAndStop")
        
        stopAll()
        
        // 移除前台通知
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_DETACH)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        
        // 停止服务
        stopSelf()
        
        SelectableLogUtils.logServiceLifecycle("EnhancedTunVpnService", "已停止")
    }

    override fun onDestroy() {
        SelectableLogUtils.logServiceLifecycle("EnhancedTunVpnService", "onDestroy")
        
        if (isServiceRunning) {
            SelectableLogUtils.w("Service", "服务被销毁但仍在运行，执行清理")
            cleanupAndStop()
        }
        
        instance = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? {
        SelectableLogUtils.d("Service", "服务被绑定")
        return LocalBinder()
    }

    override fun onRevoke() {
        SelectableLogUtils.logConnectionState("被撤销", "VPN 权限被系统撤销")
        cleanupAndStop()
        super.onRevoke()
    }

    /**
     * 获取回环接口名称
     */
    private fun loopbackIfaceName(): String {
        return try {
            val list = Collections.list(NetworkInterface.getNetworkInterfaces())
            for (ni in list) {
                if (ni.isLoopback) {
                    val name = ni.name
                    SelectableLogUtils.d("Network", "找到回环接口: $name")
                    return name
                }
            }
            SelectableLogUtils.w("Network", "未找到回环接口，使用默认 'lo'")
            "lo"
        } catch (e: Exception) {
            SelectableLogUtils.w("Network", "获取网络接口失败", e)
            "lo"
        }
    }

    /**
     * 创建通知渠道
     */
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "VPN 代理服务",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "VPN 代理服务运行状态"
                setShowBadge(false)
            }
            
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
            SelectableLogUtils.i("Notification", "通知渠道已创建")
        }
    }

    /**
     * 更新通知
     */
    private fun updateNotification(title: String, body: String) {
        val intent = Intent(this, EnhancedMainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        startForeground(NOTIFICATION_ID, notification)
        SelectableLogUtils.d("Notification", "通知已更新: $title - $body")
    }

    /**
     * 检查服务是否在运行
     */
    fun isRunning(): Boolean = isServiceRunning && !stopRequested
    
    /**
     * 获取服务状态信息
     */
    fun getStatusInfo(): String {
        return buildString {
            append("服务状态: ").append(if (isServiceRunning) "运行中" else "已停止").append("\n")
            append("停止请求: ").append(if (stopRequested) "是" else "否").append("\n")
            append("工作线程: ").append(if (worker?.isAlive == true) "活跃" else "停止").append("\n")
            append("隧道: ").append(if (tunnel != null) "已连接" else "未连接").append("\n")
            append("SOCKS5: ").append(if (socks != null) "运行中" else "已停止").append("\n")
            append("TUN 接口: ").append(if (vpnInterface != null) "已建立" else "未建立")
        }
    }
}