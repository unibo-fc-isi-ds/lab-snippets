package it.unibo

import io.ktor.network.sockets.ServerSocket
import io.ktor.network.sockets.TcpSocketBuilder
import io.ktor.network.sockets.openReadChannel
import io.ktor.network.sockets.openWriteChannel
import io.ktor.utils.io.readUTF8Line
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
    private val onReceive: suspend (ReceivedMessage) -> Unit,
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

            try {
                while (true) {
                    val message = receiveChannel.readUTF8Line()
                    if (message != null) {
                        onReceive(ReceivedMessage(message, sendChannel))
                    }
                }
            } catch (e: Throwable) {
                e.printStackTrace()
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
