package it.unibo

import kotlinx.coroutines.CoroutineScope

/**
 *
 */
interface Process {
    val scope: CoroutineScope

    val isRunning: Boolean

    suspend fun start()

    suspend fun update()

    suspend fun stop()
}
