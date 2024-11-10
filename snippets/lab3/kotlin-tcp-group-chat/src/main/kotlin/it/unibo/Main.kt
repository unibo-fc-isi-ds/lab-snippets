package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking

/**
 *
 */
fun main(vararg args: String) {
    val (type, host, port) = args

    runBlocking {
        val selectorManager = SelectorManager(Dispatchers.IO)
        val socketBuilder = aSocket(selectorManager).tcp()

        val process =
            when (type) {
                "server" ->
                    Server(this, host, port.toInt(), socketBuilder) { message ->
                        println("Received ${message.text}")
                        message.reply("Echo: ${message.text}")
                    }

                "client" -> Client(this, host, port.toInt(), socketBuilder, selectorManager)
                else -> throw IllegalArgumentException("Invalid type $type")
            }

        process.start()

        while (true) {
            process.update()
        }
    }
}
