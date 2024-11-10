package it.unibo

import kotlinx.coroutines.CoroutineScope

/**
 *
 */
interface Process {
    val scope: CoroutineScope

    suspend fun start()

    suspend fun update()

    suspend fun stop()
}
