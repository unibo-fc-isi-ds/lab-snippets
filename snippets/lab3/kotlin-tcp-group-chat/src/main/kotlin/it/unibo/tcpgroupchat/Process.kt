package it.unibo.tcpgroupchat

import kotlinx.coroutines.CoroutineScope

/**
 * A task that can be started, updated and stopped.
 */
interface Process {
    /**
     * The coroutine scope of the process.
     */
    val scope: CoroutineScope

    /**
     * Whether the process is running.
     */
    val isRunning: Boolean

    /**
     * Starts the process.
     */
    suspend fun start()

    /**
     * Updates the process. Should be called continuously.
     */
    suspend fun update()

    /**
     * Stops the process.
     */
    suspend fun stop()
}
