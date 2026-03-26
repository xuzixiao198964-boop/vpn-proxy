package com.vpnproxy.app

import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.EOFException
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.net.SocketException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.KeyStore
import java.security.SecureRandom
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import javax.net.ssl.SSLContext
import kotlin.random.Random
import javax.net.ssl.SSLSocket
import javax.net.ssl.TrustManagerFactory
import android.net.VpnService

class TunnelSession(
    private val host: String,
    private val port: Int,
    private val caInputStream: InputStream,
    private val user: String,
    private val password: String,
) {
    private var socket: SSLSocket? = null
    private val streams = ConcurrentHashMap<Int, LinkedBlockingQueue<ByteArray?>>()
    private val openLatches = ConcurrentHashMap<Int, CountDownLatch>()
    private val openFail = ConcurrentHashMap<Int, AtomicReference<String?>>()
    private val writeLock = Any()
    @Volatile
    private var readerRunning = false
    private var readerThread: Thread? = null

    fun connect() {
        val cf = java.security.cert.CertificateFactory.getInstance("X.509")
        val ca = cf.generateCertificate(caInputStream)
        val ks = KeyStore.getInstance(KeyStore.getDefaultType())
        ks.load(null, null)
        ks.setCertificateEntry("ca", ca)
        val tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm())
        tmf.init(ks)
        val ctx = SSLContext.getInstance("TLS")
        ctx.init(null, tmf.trustManagers, SecureRandom())
        val sock = ctx.socketFactory.createSocket(host, port) as SSLSocket
        sock.startHandshake()
        socket = sock
        val out = sock.getOutputStream()
        val ins = sock.getInputStream()
        val login = JSONObject()
            .put("cmd", "login")
            .put("user", user)
            .put("pass", password)
            .toString() + "\n"
        out.write(login.toByteArray(Charsets.UTF_8))
        out.flush()
        val line = readLineBytes(ins)
        val jo = JSONObject(String(line, Charsets.UTF_8))
        if (!jo.optBoolean("ok", false)) {
            try {
                sock.close()
            } catch (_: Exception) {
            }
            throw IOException("登录失败：用户名或密码错误")
        }
        readerRunning = true
        readerThread = Thread({ readLoop(ins) }, "tunnel-read").also { it.start() }
    }

    /** 在 establish() TUN 之前调用，使到 VPS 的 TLS 连接不进入 VPN 路由，避免回环。 */
    fun protectForVpn(vpn: VpnService): Boolean {
        val s = socket ?: return false
        return vpn.protect(s)
    }

    private fun readLoop(ins: InputStream) {
        try {
            while (readerRunning) {
                val header = ByteArray(9)
                readExact(ins, header)
                val type = header[0].toInt() and 0xff
                val bb = ByteBuffer.wrap(header, 1, 8).order(ByteOrder.BIG_ENDIAN)
                val sid = bb.int
                val len = bb.int
                if (len < 0 || len > 512 * 1024) break
                val payload = if (len > 0) ByteArray(len).also { readExact(ins, it) } else ByteArray(0)
                when (type) {
                    0 -> handleControl(payload)
                    1 -> streams[sid]?.offer(payload)
                }
            }
        } catch (_: EOFException) {
        } catch (_: SocketException) {
        } catch (e: Exception) {
            e.printStackTrace()
        } finally {
            readerRunning = false
            for (q in streams.values) {
                q.offer(null)
            }
        }
    }

    private fun handleControl(payload: ByteArray) {
        val c = JSONObject(String(payload, Charsets.UTF_8))
        when (c.optInt("op")) {
            2 -> {
                val id = c.getInt("id")
                openLatches[id]?.countDown()
            }
            3 -> {
                val id = c.getInt("id")
                openFail.getOrPut(id) { AtomicReference(null) }.set(c.optString("msg", "错误"))
                openLatches[id]?.countDown()
            }
            5 -> {
                val id = c.getInt("id")
                streams[id]?.offer(null)
            }
        }
    }

    fun openStream(dstHost: String, dstPort: Int): StreamHandle {
        val id = nextStreamId()
        val q = LinkedBlockingQueue<ByteArray?>()
        streams[id] = q
        val latch = CountDownLatch(1)
        openLatches[id] = latch
        openFail[id] = AtomicReference(null)
        val out = socket?.getOutputStream() ?: throw IOException("未连接")
        val ctl = JSONObject().put("op", 1).put("id", id).put("host", dstHost).put("port", dstPort)
        synchronized(writeLock) {
            out.write(packControl(0, ctl))
            out.flush()
        }
        if (!latch.await(30, TimeUnit.SECONDS)) {
            cleanup(id)
            throw IOException("打开转发超时")
        }
        val err = openFail.remove(id)?.get()
        openLatches.remove(id)
        if (err != null) {
            cleanup(id)
            throw IOException(err)
        }
        return StreamHandle(id, q, this)
    }

    fun sendData(streamId: Int, data: ByteArray) {
        val out = socket?.getOutputStream() ?: return
        synchronized(writeLock) {
            out.write(packData(streamId, data))
            out.flush()
        }
    }

    fun closeStream(streamId: Int) {
        streams.remove(streamId)
        val out = socket?.getOutputStream() ?: return
        val ctl = JSONObject().put("op", 4).put("id", streamId)
        synchronized(writeLock) {
            try {
                out.write(packControl(0, ctl))
                out.flush()
            } catch (_: Exception) {
            }
        }
    }

    fun shutdown() {
        readerRunning = false
        try {
            socket?.close()
        } catch (_: Exception) {
        }
        socket = null
        try {
            readerThread?.join(2000)
        } catch (_: Exception) {
        }
        readerThread = null
        streams.clear()
    }

    private fun cleanup(id: Int) {
        streams.remove(id)
        openLatches.remove(id)
        openFail.remove(id)
    }

    private fun nextStreamId(): Int {
        while (true) {
            val x = Random.nextInt(1, Int.MAX_VALUE - 1)
            if (!streams.containsKey(x)) return x
        }
    }

    class StreamHandle(
        val id: Int,
        private val incoming: LinkedBlockingQueue<ByteArray?>,
        private val tunnel: TunnelSession,
    ) {
        fun readChunk(): ByteArray? {
            try {
                return incoming.take()
            } catch (_: InterruptedException) {
                Thread.currentThread().interrupt()
                return null
            }
        }
        fun send(data: ByteArray) = tunnel.sendData(id, data)
        fun close() = tunnel.closeStream(id)
    }

    companion object {
        fun readLineBytes(ins: InputStream): ByteArray {
            val baos = ByteArrayOutputStream()
            while (true) {
                val b = ins.read()
                if (b < 0) throw EOFException()
                if (b == '\n'.code) break
                baos.write(b)
            }
            return baos.toByteArray()
        }

        fun readExact(ins: InputStream, buf: ByteArray) {
            var o = 0
            while (o < buf.size) {
                val n = ins.read(buf, o, buf.size - o)
                if (n < 0) throw EOFException()
                o += n
            }
        }

        fun packControl(streamId: Int, json: JSONObject): ByteArray {
            val raw = json.toString().toByteArray(Charsets.UTF_8)
            val buf = ByteBuffer.allocate(9 + raw.size).order(ByteOrder.BIG_ENDIAN)
            buf.put(0.toByte())
            buf.putInt(streamId)
            buf.putInt(raw.size)
            buf.put(raw)
            return buf.array()
        }

        fun packData(streamId: Int, chunk: ByteArray): ByteArray {
            val buf = ByteBuffer.allocate(9 + chunk.size).order(ByteOrder.BIG_ENDIAN)
            buf.put(1.toByte())
            buf.putInt(streamId)
            buf.putInt(chunk.size)
            buf.put(chunk)
            return buf.array()
        }
    }
}
