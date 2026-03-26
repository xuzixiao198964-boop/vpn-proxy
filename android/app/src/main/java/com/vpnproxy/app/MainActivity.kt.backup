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

        }

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

}

