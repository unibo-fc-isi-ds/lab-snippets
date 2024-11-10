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
    fun createServer(onReceive: Callback) =
        Server(
            scope,
            host,
            port,
            socketBuilder,
            onReceive,
        )

    fun createClient(
        onReceiveFromServer: Callback,
        onReceiveFromInput: Callback,
    ) = Client(
        scope,
        host,
        port,
        socketBuilder,
        selectorManager,
        onReceiveFromServer,
        onReceiveFromInput,
    )
}
