package com.vpnproxy.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.util.Log
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import androidx.core.app.NotificationCompat
import com.vpnproxy.tun2.tun2mobile.Tun2mobile
import java.io.IOException
import java.net.InetAddress
import java.net.NetworkInterface
import java.util.Collections

/**
 * 前台 VPN 服务：本地 SOCKS5 + tun2socks 将系统流量导入该 SOCKS。
 * 必须先 protect 到 VPS 的 TLS 套接字，再 establish TUN，避免流量回环。
 */
class TunVpnService : VpnService() {

    private var tunnel: TunnelSession? = null
    private var socks: Socks5Server? = null
    private var worker: Thread? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopAll()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                stopForeground(STOP_FOREGROUND_DETACH)
            } else {
                @Suppress("DEPRECATION")
                stopForeground(true)
            }
            stopSelf()
            return START_NOT_STICKY
        }

        val host = intent?.getStringExtra(EXTRA_HOST) ?: return START_NOT_STICKY
        val port = intent.getIntExtra(EXTRA_PORT, 18443)
        val user = intent.getStringExtra(EXTRA_USER) ?: return START_NOT_STICKY
        val pass = intent.getStringExtra(EXTRA_PASS) ?: return START_NOT_STICKY
        val socksPort = intent.getIntExtra(EXTRA_SOCKS_PORT, 1080)

        stopAll()

        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            // IMPORTANCE_LOW 在多数机型上不在状态栏显示图标，需 DEFAULT 及以上
            nm.createNotificationChannel(
                NotificationChannel(
                    CHANNEL_ID,
                    getString(R.string.channel_proxy),
                    NotificationManager.IMPORTANCE_DEFAULT,
                ).apply {
                    setShowBadge(true)
                },
            )
        }
        val notif = buildForegroundNotification(socksPort, "正在连接…")
        @Suppress("DEPRECATION")
        startForeground(NOTIF_ID, notif)

        worker = Thread({
            var pfd: ParcelFileDescriptor? = null
            try {
                resources.openRawResource(R.raw.ca).use { caIn ->
                    val t = TunnelSession(host, port, caIn, user, pass)
                    t.connect()
                    if (!t.protectForVpn(this@TunVpnService)) {
                        throw IOException("VPN protect 失败，无法排除到服务器的连接")
                    }
                    tunnel = t
                    val s = Socks5Server("127.0.0.1", socksPort, t) { }
                    socks = s
                    s.start()
                    val proxyUrl = "socks5://127.0.0.1:$socksPort"
                    pfd = Builder()
                        .setSession("VpnProxy")
                        .setMtu(MTU)
                        .addAddress("10.0.0.2", 32)
                        .addRoute("0.0.0.0", 0)
                        .addDnsServer("8.8.8.8")
                        .addDnsServer("8.8.4.4")
                        .addDnsServer("1.1.1.1")
                        .apply {
                            try {
                                addRoute(InetAddress.getByName("::"), 0)
                            } catch (_: Exception) {
                            }
                        }
                        .establish()
                    if (pfd == null) {
                        throw IOException("无法建立 VPN 接口（可能被其他 VPN 占用）")
                    }
                    val tunFd = pfd!!.detachFd()
                    val bindLo = loopbackIfaceName()
                    try {
                        Tun2mobile.startTun(tunFd.toLong(), MTU.toLong(), proxyUrl, bindLo)
                    } catch (e: Exception) {
                        try {
                            ParcelFileDescriptor.adoptFd(tunFd).close()
                        } catch (_: Exception) {
                        }
                        throw IOException("tun2socks 启动失败: ${e.message}", e)
                    }
                    pfd = null
                    Handler(Looper.getMainLooper()).post {
                        val n = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                        n.notify(NOTIF_ID, buildForegroundNotification(socksPort, "VPN 已连接 · 状态栏应显示钥匙图标"))
                    }
                    while (!Thread.currentThread().isInterrupted) {
                        try {
                            Thread.sleep(5000)
                        } catch (_: InterruptedException) {
                            break
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "VPN 工作线程失败", e)
                Handler(Looper.getMainLooper()).post {
                    // 不再显示通知栏错误日志
                    // 改为发送到应用内日志系统
                    sendErrorToApp(e.message ?: e.javaClass.simpleName)
                    
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                        stopForeground(STOP_FOREGROUND_DETACH)
                    } else {
                        @Suppress("DEPRECATION")
                        stopForeground(true)
                    }
                    stopSelf()
                }
            } finally {
                try {
                    Tun2mobile.stopTun()
                } catch (_: Throwable) {
                }
                try {
                    pfd?.close()
                } catch (_: Exception) {
                }
                socks?.stop()
                socks = null
                tunnel?.shutdown()
                tunnel = null
            }
        }, "tunvpn-worker").also { it.start() }

        return START_STICKY
    }

    private fun stopAll() {
        worker?.interrupt()
        try {
            worker?.join(4000)
        } catch (_: Exception) {
        }
        worker = null
        try {
            Tun2mobile.stopTun()
        } catch (_: Throwable) {
        }
        socks?.stop()
        socks = null
        tunnel?.shutdown()
        tunnel = null
    }

    override fun onDestroy() {
        stopAll()
        super.onDestroy()
    }

    /** tun2socks 连本机 SOCKS 的出站必须走回环接口，否则 VPN 路由可导致 127.0.0.1 不可达。 */
    private fun loopbackIfaceName(): String {
        return try {
            val list = Collections.list(NetworkInterface.getNetworkInterfaces())
            for (ni in list) {
                if (ni.isLoopback) return ni.name
            }
            "lo"
        } catch (_: Exception) {
            "lo"
        }
    }

    private fun buildForegroundNotification(socksPort: Int, body: String): Notification {
        val pi = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE,
        )
        val b = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText("$body\nSOCKS5：127.0.0.1:$socksPort"))
            .setSmallIcon(R.drawable.ic_stat_vpn)
            .setContentIntent(pi)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setCategory(Notification.CATEGORY_SERVICE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            b.setForegroundServiceBehavior(NotificationCompat.FOREGROUND_SERVICE_IMMEDIATE)
        }
        return b.build()
    }

    private fun sendErrorToApp(reason: String) {
        // 发送错误到应用内日志系统
        val intent = Intent("APP_INTERNAL_ERROR_LOG").apply {
            putExtra("error", reason)
            putExtra("timestamp", System.currentTimeMillis())
        }
        sendBroadcast(intent)
        Log.e(TAG, "应用内错误日志: $reason")
    }

    companion object {
        private const val TAG = "TunVpnService"
        const val CHANNEL_ID = "vpnproxy_fgs"
        const val NOTIF_ID = 1001
        const val ACTION_STOP = "com.vpnproxy.app.STOP"
        const val EXTRA_HOST = "host"
        const val EXTRA_PORT = "port"
        const val EXTRA_USER = "user"
        const val EXTRA_PASS = "pass"
        const val EXTRA_SOCKS_PORT = "socks_port"
        private const val MTU = 1500
    }
}
