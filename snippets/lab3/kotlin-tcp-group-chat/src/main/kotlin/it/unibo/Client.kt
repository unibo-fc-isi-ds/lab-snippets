package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.Socket
import io.ktor.network.sockets.TcpSocketBuilder
import io.ktor.network.sockets.openReadChannel
import io.ktor.network.sockets.openWriteChannel
import io.ktor.utils.io.readUTF8Line
import io.ktor.utils.io.writeStringUtf8
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlin.system.exitProcess

/**
 *
 */
class Client(
    override val scope: CoroutineScope,
    override val host: String,
    override val port: Int,
    private val socketBuilder: TcpSocketBuilder,
    private val selectorManager: SelectorManager,
) : Addressable, Process {
    private lateinit var socket: Socket

    override suspend fun start() {
        socket = socketBuilder.connect(host, port)
        println("Connected to ${socket.remoteAddress}")
    }

    override suspend fun update() {
        val receiveChannel = socket.openReadChannel()
        val sendChannel = socket.openWriteChannel(autoFlush = true)

        scope.launch(Dispatchers.IO) {
            while (true) {
                val greeting = receiveChannel.readUTF8Line()
                if (greeting != null) {
                    println(greeting)
                } else {
                    stop()
                }
            }
        }

        while (true) {
            val message = readlnOrNull() ?: continue
            println("Sending $message")
            sendChannel.writeStringUtf8("$message\n")
        }
    }

    override suspend fun stop() {
        scope.launch {
            println("Server closed a connection")
            socket.close()
            selectorManager.close()
            exitProcess(0)
        }
    }
}
