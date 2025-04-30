package it.unibo.tcpgroupchat

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.ConnectException

/**
 * A peer contains a [Client]. If, at connection time, the server is not available,
 * the peer also acts as a [Server], thus becoming the 'leader' of the connection.
 */
class Peer(
    override val scope: CoroutineScope,
    createClient: () -> Process,
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
                while (server!!.isRunning) {
                    server!!.update()
                }
            }
        }

        scope.launch(Dispatchers.IO) {
            while (client.isRunning) {
                client.update()
            }
        }
    }

    /**
     * @throws UnsupportedOperationException the peer is updated automatically in a loop within [start].
     */
    override suspend fun update() = throw UnsupportedOperationException()

    override suspend fun stop() {
        server?.stop()
        client.stop()
    }
}
