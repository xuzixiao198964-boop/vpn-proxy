package com.vpnproxy.app



import java.io.IOException

import java.net.InetAddress

import java.net.ServerSocket

import java.net.Socket

import java.net.SocketException

import java.util.concurrent.atomic.AtomicBoolean



class Socks5Server(

    private val listenHost: String,

    private val listenPort: Int,

    private val tunnel: TunnelSession,

    private val onLog: (String) -> Unit,

) {

    private val running = AtomicBoolean(false)

    private var serverSocket: ServerSocket? = null

    private var acceptThread: Thread? = null



    /**

     * 必须在当前线程先完成 bind，再让 tun2socks 连 127.0.0.1:port。

     * 若 bind 放在异步线程里，会出现「TUN 已起但 SOCKS 尚未监听」的竞态，代理全挂。

     */

    fun start() {

        if (!running.compareAndSet(false, true)) return

        serverSocket = ServerSocket(listenPort, 128, java.net.InetAddress.getByName(listenHost))

        val ss = serverSocket!!

        acceptThread = Thread({

            while (running.get()) {

                try {

                    val sock = ss.accept()

                    Thread({ handleClient(sock) }, "socks-${sock.inetAddress}").start()

                } catch (_: SocketException) {

                    if (!running.get()) break

                } catch (e: Exception) {

                    if (running.get()) onLog("SOCKS accept: ${e.message}")

                }

            }

        }, "socks-accept").also { it.start() }

    }



    fun stop() {

        running.set(false)

        try {

            serverSocket?.close()

        } catch (_: Exception) {

        }

        serverSocket = null

        try {

            acceptThread?.join(2000)

        } catch (_: Exception) {

        }

        acceptThread = null

    }



    private fun handleClient(sock: Socket) {

        sock.soTimeout = 0

        val ins = sock.getInputStream()

        val out = sock.getOutputStream()

        try {

            val ver = ins.read()

            if (ver != 0x05) return

            val nmeth = ins.read()

            if (nmeth < 0) return

            val methods = ByteArray(nmeth)

            TunnelSession.readExact(ins, methods)

            out.write(byteArrayOf(0x05, 0x00))

            out.flush()

            val req = ByteArray(4)

            TunnelSession.readExact(ins, req)

            if (req[0] != 5.toByte() || req[1] != 1.toByte()) return

            val atyp = req[3].toInt() and 0xff

            val host: String = when (atyp) {

                1 -> {

                    val b = ByteArray(4)

                    TunnelSession.readExact(ins, b)

                    "${b[0].toInt() and 0xff}.${b[1].toInt() and 0xff}.${b[2].toInt() and 0xff}.${b[3].toInt() and 0xff}"

                }

                3 -> {

                    val ln = ins.read()

                    if (ln < 0) return

                    val hb = ByteArray(ln)

                    TunnelSession.readExact(ins, hb)

                    String(hb, Charsets.UTF_8)

                }

                4 -> {

                    val b = ByteArray(16)

                    TunnelSession.readExact(ins, b)

                    InetAddress.getByAddress(b).hostAddress ?: return

                }

                else -> return

            }

            val pb = ByteArray(2)

            TunnelSession.readExact(ins, pb)

            val port = ((pb[0].toInt() and 0xff) shl 8) or (pb[1].toInt() and 0xff)

            val handle = try {

                tunnel.openStream(host, port)

            } catch (e: Exception) {

                out.write(byteArrayOf(0x05, 0x05, 0x00, 0x01, 0, 0, 0, 0, 0, 0))

                out.flush()

                onLog("转发失败: ${e.message}")

                return

            }

            out.write(byteArrayOf(0x05, 0x00, 0x00, 0x01, 0, 0, 0, 0, 0, 0))

            out.flush()

            val up = Thread({

                try {

                    val buf = ByteArray(65536)

                    while (true) {

                        val n = ins.read(buf)

                        if (n <= 0) break

                        handle.send(buf.copyOf(n))

                    }

                } catch (_: IOException) {

                } finally {

                    handle.close()

                }

            }, "socks-up-${handle.id}")

            up.start()

            try {

                while (true) {

                    val chunk = handle.readChunk() ?: break

                    out.write(chunk)

                    out.flush()

                }

            } catch (_: IOException) {

            } finally {

                try {

                    up.join(8000)

                } catch (_: Exception) {

                }

                try {

                    sock.close()

                } catch (_: Exception) {

                }

            }

        } catch (_: Exception) {

            try {

                sock.close()

            } catch (_: Exception) {

            }

        }

    }

}

