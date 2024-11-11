package it.unibo

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.ConnectException

/**
 *
 */
class Peer(
    override val scope: CoroutineScope,
    private val createClient: () -> Process,
    private val createServer: () -> Process,
) : Process {
    private val client: Process = createClient()
    private var server: Process? = null

    override val isRunning: Boolean
        get() = client.isRunning && (server?.isRunning ?: true)

    override suspend fun start() {
        try {
            client.start()
        } catch (e: ConnectException) {
            server = createServer()
            server!!.start()
            client.start()
        }

        if (server != null) {
            scope.launch {
                while (true) {
                    server!!.update()
                }
            }
        }

        scope.launch(Dispatchers.IO) {
            while (true) {
                client.update()
            }
        }
    }

    override suspend fun update() = throw UnsupportedOperationException()

    override suspend fun stop() {
        server?.stop()
        client.stop()
    }
}
