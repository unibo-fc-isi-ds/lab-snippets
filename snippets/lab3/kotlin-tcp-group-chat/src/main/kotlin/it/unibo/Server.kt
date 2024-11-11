@file:Suppress("ktlint:standard:no-wildcard-imports")

package it.unibo

import io.ktor.network.sockets.*
import io.ktor.utils.io.ByteWriteChannel
import io.ktor.utils.io.readUTF8Line
import it.unibo.protocol.ProtocolMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * A TCP server that listens for incoming connections
 * and handles messages from [Client]s according to a [ProtocolMessage] schema.
 * @property socketBuilder the builder to create the server socket from
 * @property onReceive callback to handle incoming messages
 */
class Server(
    override val scope: CoroutineScope,
    override val host: String,
    override val port: Int,
    private val socketBuilder: TcpSocketBuilder,
    private val onReceive: ServerCallback,
) : Addressable, Process {
    private lateinit var serverSocket: ServerSocket

    // Client channels to send messages to.
    private var sendChannels = mutableSetOf<ByteWriteChannel>()

    override val isRunning: Boolean
        get() = !serverSocket.isClosed

    override suspend fun start() {
        serverSocket = socketBuilder.bind(host, port)
        println("Server is listening at ${serverSocket.localAddress}")
    }

    override suspend fun update() {
        val socket = serverSocket.accept()

        scope.launch(Dispatchers.IO) {
            val receiveChannel = socket.openReadChannel()
            val sendChannel = socket.openWriteChannel(autoFlush = true)
            sendChannels.add(sendChannel)

            try {
                while (true) {
                    val message =
                        receiveChannel.readUTF8Line()
                            ?.let(ProtocolMessage::decode)
                            ?: continue
                    onReceive(ReceivedMessage(message, sendChannels))
                }
            } catch (e: Throwable) {
                e.printStackTrace()
                stop()
            }
        }
    }

    override suspend fun stop() {
        if (!isRunning) return
        scope.launch {
            serverSocket.close()
        }
    }
}
