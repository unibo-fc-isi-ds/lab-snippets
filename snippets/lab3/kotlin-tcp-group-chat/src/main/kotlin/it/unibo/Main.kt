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
        },
        onReceiveFromInput = { message ->
            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, message.text))
        },
        onDisconnect = {
            println("=== Goodbye $name ===")
            it.replyBroadcast(ProtocolMessage(uuid, EventType.DISCONNECT))
        },
    )
}

/**q
 *
 */
fun main(vararg args: String) {
    val (host, port) =
        args.first()
            .split(":")
            .let { (host, port) -> host to port.toInt() }

    println("Welcome to the group chat! Please enter your name:")
    val name = readlnOrNull() ?: exitProcess(1)

    runBlocking {
        val selectorManager = SelectorManager(Dispatchers.IO)
        val socketBuilder = aSocket(selectorManager).tcp()

        val factory = ProcessFactory(this, host, port, socketBuilder, selectorManager)

        val peer =
            Peer(
                this,
                { createClient(factory, name) },
                { createServer(factory, log = false) },
            )

        peer.start()
    }
}
