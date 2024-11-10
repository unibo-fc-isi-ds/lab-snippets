package it.unibo

import io.ktor.network.sockets.ServerSocket
import io.ktor.network.sockets.TcpSocketBuilder
import io.ktor.network.sockets.openReadChannel
import io.ktor.network.sockets.openWriteChannel
import io.ktor.utils.io.readUTF8Line
import io.ktor.utils.io.writeStringUtf8
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

/**
 *
 */
class Server(
    override val scope: CoroutineScope,
    override val host: String,
    override val port: Int,
    private val socketBuilder: TcpSocketBuilder,
) : Addressable, Process {
    private lateinit var serverSocket: ServerSocket

    override suspend fun start() {
        serverSocket = socketBuilder.bind(host, port)
        println("Server is listening at ${serverSocket.localAddress}")
    }

    override suspend fun update() {
        val socket = serverSocket.accept()
        println("Accepted $socket")

        scope.launch {
            val receiveChannel = socket.openReadChannel()
            val sendChannel = socket.openWriteChannel(autoFlush = true)
            sendChannel.writeStringUtf8("Please enter your name\n")
            try {
                while (true) {
                    val name = receiveChannel.readUTF8Line()
                    sendChannel.writeStringUtf8("Hello, $name!\n")
                }
            } catch (e: Throwable) {
                stop()
            }
        }
    }

    override suspend fun stop() {
        scope.launch {
            serverSocket.close()
        }
    }
}
