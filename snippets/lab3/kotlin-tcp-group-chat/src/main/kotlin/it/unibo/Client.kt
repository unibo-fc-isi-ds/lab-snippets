@file:Suppress("ktlint:standard:no-wildcard-imports")

package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.*
import io.ktor.utils.io.readUTF8Line
import it.unibo.protocol.EventType
import it.unibo.protocol.ProtocolMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.*
import kotlin.system.exitProcess

/**
 * A TCP client that connects to a [Server] and sends messages according to a [ProtocolMessage] schema.
 * @property socketBuilder the builder to create the client socket from
 * @property selectorManager the selector manager to handle the client socket
 * @property onConnect callback to handle the connection event
 * @property onReceiveFromServer callback to handle incoming messages from the server
 * @property onReceiveFromInput callback to handle incoming messages from stdin
 * @property onDisconnect callback to handle the disconnection event
 * @property uuid the unique identifier of the client
 */
class Client(
    override val scope: CoroutineScope,
    override val host: String,
    override val port: Int,
    private val socketBuilder: TcpSocketBuilder,
    private val selectorManager: SelectorManager,
    private val onConnect: ClientCallback,
    private val onReceiveFromServer: ClientCallback,
    private val onReceiveFromInput: ClientCallback,
    private val onDisconnect: ClientCallback,
    val uuid: UUID = UUID.randomUUID(),
) : Addressable, Process {
    private lateinit var socket: Socket

    override val isRunning: Boolean
        get() = !socket.isClosed

    override suspend fun start() {
        socket = socketBuilder.connect(host, port)
    }

    override suspend fun update() {
        val receiveChannel = socket.openReadChannel()
        val sendChannel = socket.openWriteChannel(autoFlush = true)

        println("Connected to ${socket.remoteAddress}")
        onConnect(
            ReceivedMessage(
                ProtocolMessage(uuid, EventType.CONNECT),
                sendChannel,
            ),
        )

        // Messages received from the server.
        scope.launch(Dispatchers.IO) {
            while (true) {
                when (val message = receiveChannel.readUTF8Line()) {
                    null -> {
                        println("Server closed the connection.")
                        stop()
                    }

                    else ->
                        onReceiveFromServer(
                            ReceivedMessage(
                                ProtocolMessage.decode(message),
                                sendChannel,
                            ),
                        )
                }
            }
        }

        // Messages received from stdin.
        while (true) {
            when (val message = readlnOrNull()) {
                null -> {
                    // End of input (Ctrl+D).
                    onDisconnect(
                        ReceivedMessage(
                            ProtocolMessage(uuid, EventType.DISCONNECT),
                            sendChannel,
                        ),
                    )
                    stop()
                }

                else ->
                    // Message callback.
                    onReceiveFromInput(
                        ReceivedMessage(
                            ProtocolMessage(uuid, EventType.TEXT, message),
                            sendChannel,
                        ),
                    )
            }
        }
    }

    override suspend fun stop() {
        if (!isRunning) return
        withContext(Dispatchers.IO) {
            socket.close()
            selectorManager.close()
            exitProcess(0)
        }
    }
}
