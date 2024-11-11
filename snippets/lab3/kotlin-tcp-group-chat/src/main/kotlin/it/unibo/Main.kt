package it.unibo

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import it.unibo.protocol.EventType
import it.unibo.protocol.ProtocolMessage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.net.ConnectException
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

fun createServer(
    factory: ProcessFactory,
    log: Boolean,
): Process {
    val chat = GroupChat()

    return factory.createServer { message ->
        when (message.type) {
            EventType.CONNECT -> {
                chat.join(message.uuid, message.text)
            }

            EventType.DISCONNECT -> {
                chat.leave(message.uuid)
            }

            else -> {}
        }

        val formatted = formatMessage(message.message, chat)
        if (log) println(formatted)
        message.replyBroadcast(ProtocolMessage(message.uuid, EventType.TEXT, formatted))
    }
}

fun createClient(
    factory: ProcessFactory,
    name: String,
): Process {
    return factory.createClient(
        onConnect = { message ->
            println("=== Welcome $name ===")
            println("ID: $uuid")
            println()
            message.replyBroadcast(ProtocolMessage(uuid, EventType.CONNECT, name))
        },
        onReceiveFromServer = { message ->
            if (message.uuid != uuid) {
                println(message.text)
            }
        }, // fix server being unresponsive after client disconnection
        onReceiveFromInput = { message ->
            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, message.text))
        },
        onDisconnect = {
            println("=== Goodbye $name ===")
            it.replyBroadcast(ProtocolMessage(uuid, EventType.DISCONNECT))
        },
    )
}

/**
 *
 */
fun main(vararg args: String) {
    val (host, port) = args

    println("Welcome to the group chat! Please enter your name:")
    val name = readlnOrNull() ?: exitProcess(1)

    runBlocking {
        val selectorManager = SelectorManager(Dispatchers.IO)
        val socketBuilder = aSocket(selectorManager).tcp()

        val factory = ProcessFactory(this, host, port.toInt(), socketBuilder, selectorManager)

        val client = createClient(factory, name)
        var server: Process? = null

        try {
            client.start()
        } catch (e: ConnectException) {
            server = createServer(factory, log = false)
            server.start()
            client.start()
        }

        launch(Dispatchers.IO) {
            while (true) {
                client.update()
            }
        }

        if (server != null) {
            launch {
                while (true) {
                    server.update()
                }
            }
        }
    }
}
