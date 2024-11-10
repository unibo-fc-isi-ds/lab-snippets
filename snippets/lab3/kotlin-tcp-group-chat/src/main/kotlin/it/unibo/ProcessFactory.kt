package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.TcpSocketBuilder
import kotlinx.coroutines.CoroutineScope

/**
 *
 */
class ProcessFactory(
    private val scope: CoroutineScope,
    override val host: String,
    override val port: Int,
    private val socketBuilder: TcpSocketBuilder,
    private val selectorManager: SelectorManager,
) : Addressable {
    fun createServer(onReceive: ServerCallback) =
        Server(
            scope,
            host,
            port,
            socketBuilder,
            onReceive,
        )

    fun createClient(
        onConnect: ClientCallback,
        onReceiveFromServer: ClientCallback,
        onReceiveFromInput: ClientCallback,
        onDisconnect: ClientCallback,
    ) = Client(
        scope,
        host,
        port,
        socketBuilder,
        selectorManager,
        onConnect,
        onReceiveFromServer,
        onReceiveFromInput,
        onDisconnect,
    )
}
