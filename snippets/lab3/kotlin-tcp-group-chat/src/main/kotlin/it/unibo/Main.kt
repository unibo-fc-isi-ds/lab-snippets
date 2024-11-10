package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking

/**
 *
 */
fun main() =
    runBlocking {
        val selectorManager = SelectorManager(Dispatchers.IO)
        val socketBuilder = aSocket(selectorManager).tcp()
        val server = Server(this, "127.0.0.1", 9002, socketBuilder)
        while (true) {
            server.update()
        }
    }
