package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlin.system.exitProcess

fun createServer(factory: ProcessFactory): Process {
    val chat = GroupChat()

    return factory.createServer { message ->
        println("Received ${message.text}")
        message.reply("Echo: ${message.text}")
    }
}

fun createClient(factory: ProcessFactory): Process {
    println("Welcome to the group chat! Please enter your name:")
    val name = readlnOrNull() ?: exitProcess(1)

    return factory.createClient(
        onConnect = {
            println("=== Welcome $name ===")
            println("ID: $uuid")
            println()
        },
        onReceiveFromServer = { message ->
            println("Received from server: ${message.text}")
        },
        onReceiveFromInput = { message ->
            println("Received from stdin: ${message.text}")
            message.reply("Sending.")
        },
        onDisconnect = {
            println("=== Goodbye $name ===")
        },
    )
}

/**
 *
 */
fun main(vararg args: String) {
    val (type, host, port) = args

    runBlocking {
        val selectorManager = SelectorManager(Dispatchers.IO)
        val socketBuilder = aSocket(selectorManager).tcp()

        val factory = ProcessFactory(this, host, port.toInt(), socketBuilder, selectorManager)

        val process =
            when (type) {
                "server" -> createServer(factory)
                "client" -> createClient(factory)
                else -> throw IllegalArgumentException("Invalid type $type")
            }

        process.start()

        while (true) {
            process.update()
        }
    }
}
