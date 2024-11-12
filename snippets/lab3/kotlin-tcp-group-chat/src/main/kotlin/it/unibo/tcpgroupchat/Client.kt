package it.unibo.tcpgroupchat

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.Socket
import io.ktor.network.sockets.TcpSocketBuilder
import io.ktor.network.sockets.isClosed
import io.ktor.network.sockets.openReadChannel
import io.ktor.network.sockets.openWriteChannel
import io.ktor.server.engine.internal.ClosedChannelException
import io.ktor.utils.io.ByteReadChannel
import io.ktor.utils.io.ByteWriteChannel
import io.ktor.utils.io.readUTF8Line
import it.unibo.tcpgroupchat.protocol.EventType
import it.unibo.tcpgroupchat.protocol.ProtocolMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID
import kotlin.system.exitProcess

/**
 * A TCP client that connects to a [Server] and sends messages according to a [ProtocolMessage] schema.
 * @property socketBuilder the builder to create the client socket from
 * @property selectorManager the selector manager to handle the client socket
 * @property onConnect callback to handle the connection event
 * @property onReceiveFromServer callback to handle incoming messages from the server
 * @property onReceiveFromInput callback to handle incoming messages from stdin
 * @property onDisconnect callback to handle the disconnection event
 * @property exitOnStop whether to exit the process when the client stops
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
    private val exitOnStop: Boolean = true,
    val uuid: UUID = UUID.randomUUID(),
) : Addressable, Process {
    private lateinit var socket: Socket
    private lateinit var sendChannel: ByteWriteChannel

    override val isRunning: Boolean
        get() = !socket.isClosed

    override suspend fun start() {
        socket = socketBuilder.connect(host, port)
    }

    override suspend fun update() {
        if (!isRunning) return

        val receiveChannel: ByteReadChannel

        try {
            receiveChannel = socket.openReadChannel()
            sendChannel = socket.openWriteChannel(autoFlush = true)
        } catch (e: ClosedChannelException) {
            stop()
            return
        }

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
                        return@launch
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
                    stop()
                    return
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
            if (::sendChannel.isInitialized) {
                onDisconnect(
                    ReceivedMessage(
                        ProtocolMessage(uuid, EventType.DISCONNECT),
                        sendChannel,
                    ),
                )
            }

            socket.close()

            if (exitOnStop) {
                selectorManager.close()
                exitProcess(0)
            }
        }
    }
}
