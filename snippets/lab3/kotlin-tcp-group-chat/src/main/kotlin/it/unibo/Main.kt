package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import it.unibo.protocol.EventType
import it.unibo.protocol.ProtocolMessage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlin.system.exitProcess

private fun formatMessage(
    message: ProtocolMessage,
    chat: GroupChat,
): String {
    return when (message.type) {
        EventType.CONNECT -> {
            "[${message.uuid}] ${message.text} has joined the chat. Now online: ${chat.onlineNames}"
        }
        EventType.DISCONNECT -> {
            "[${message.uuid}] ${chat.getName(message.uuid)} has left the chat. Now online: ${chat.onlineNames}"
        }
        EventType.TEXT -> {
            "[${message.uuid}] ${chat.getName(message.uuid)}: ${message.text}"
        }
    }
}

fun createServer(factory: ProcessFactory): Process {
    val chat = GroupChat()

    return factory.createServer { message ->
        when (message.type) {
            EventType.CONNECT -> {
                chat.join(message.uuid, message.text)
            }

            EventType.DISCONNECT -> {
                chat.leave(message.uuid)
            }

            EventType.TEXT -> {
                message.replyBroadcast(message.message)
            }
        }

        println(formatMessage(message.message, chat))
    }
}

fun createClient(factory: ProcessFactory): Process {
    println("Welcome to the group chat! Please enter your name:")
    val name = readlnOrNull() ?: exitProcess(1)

    return factory.createClient(
        onConnect = { message ->
            println("=== Welcome $name ===")
            println("ID: $uuid")
            println()
            message.replyBroadcast(ProtocolMessage(uuid, EventType.CONNECT, name))
        },
        onReceiveFromServer = { message ->
            if (message.uuid != uuid) {
                println("Received from server: ${message.message.text}")
            }
        },
        onReceiveFromInput = { message ->
            println("Received from stdin: ${message.message.text}")
            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, message.message.text))
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
