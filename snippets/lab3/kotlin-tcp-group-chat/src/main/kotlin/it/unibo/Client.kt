package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.Socket
import io.ktor.network.sockets.TcpSocketBuilder
import io.ktor.network.sockets.openReadChannel
import io.ktor.network.sockets.openWriteChannel
import io.ktor.utils.io.readUTF8Line
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
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
    private val onReceiveFromServer: Callback,
    private val onReceiveFromInput: Callback,
) : Addressable, Process {
    private lateinit var socket: Socket

    override suspend fun start() {
        socket = socketBuilder.connect(host, port)
        println("Connected to ${socket.remoteAddress}")
    }

    override suspend fun update() {
        val receiveChannel = socket.openReadChannel()
        val sendChannel = socket.openWriteChannel(autoFlush = true)

        // Messages received from the server.
        scope.launch(Dispatchers.IO) {
            while (true) {
                when (val message = receiveChannel.readUTF8Line()) {
                    null -> stop()
                    else -> onReceiveFromServer(ReceivedMessage(message, sendChannel))
                }
            }
        }

        // Messages received from stdin.
        while (true) {
            when (val message = readlnOrNull()) {
                null -> stop()
                else -> onReceiveFromInput(ReceivedMessage(message, sendChannel))
            }
        }
    }

    override suspend fun stop() {
        withContext(Dispatchers.IO) {
            println("Server closed a connection")
            socket.close()
            selectorManager.close()
            exitProcess(0)
        }
    }
}
