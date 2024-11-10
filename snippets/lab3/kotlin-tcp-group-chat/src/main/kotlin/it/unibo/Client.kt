package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.Socket
import io.ktor.network.sockets.TcpSocketBuilder
import io.ktor.network.sockets.openReadChannel
import io.ktor.network.sockets.openWriteChannel
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
 *
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
                    onDisconnect(
                        ReceivedMessage(
                            ProtocolMessage(uuid, EventType.DISCONNECT),
                            sendChannel,
                        ),
                    )
                    stop()
                }
                else ->
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
        withContext(Dispatchers.IO) {
            socket.close()
            selectorManager.close()
            exitProcess(0)
        }
    }
}
