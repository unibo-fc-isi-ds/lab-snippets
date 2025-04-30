package it.unibo.tcpgroupchat

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import it.unibo.tcpgroupchat.protocol.EventType
import it.unibo.tcpgroupchat.protocol.ProtocolMessage
import it.unibo.tcpgroupchat.protocol.format
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlin.system.exitProcess

/**
 * Creates a server task.
 * @param factory the factory to create the server from
 * @param log whether to log the messages to stdout or not
 * @return the new server
 */
fun createServer(
    factory: ProcessFactory,
    log: (String) -> Unit = { if (GlobalOptions.logOnlyFromServer) println(it) },
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

        val formatted = message.message.format(chat)
        log(formatted)

        message.replyBroadcast(ProtocolMessage(message.uuid, EventType.TEXT, formatted))
    }
}

/**
 * Creates a client task.
 * @param factory the factory to create the client from
 * @param name the name of the client, chosen by the user itself during the setup
 * @return the new client
 */
fun createClient(
    factory: ProcessFactory,
    name: String,
): Process {
    fun log(text: String = "") {
        if (GlobalOptions.clientCanLog) {
            println(text)
        }
    }

    return factory.createClient(
        onConnect = { message ->
            log("=== Welcome $name ===")
            log("ID: $uuid")
            log()
            message.replyBroadcast(ProtocolMessage(uuid, EventType.CONNECT, name))
        },
        onReceiveFromServer = { message ->
            if (message.uuid != uuid) {
                log(message.text)
            }
        },
        onReceiveFromInput = { message ->
            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, message.text))
        },
        onDisconnect = {
            log("=== Goodbye $name ===")
            it.replyBroadcast(ProtocolMessage(uuid, EventType.DISCONNECT))
        },
    )
}

/**
 * Main entry point.
 * The first argument is expected to be in the form of `host:port`.
 */
fun main(vararg args: String) {
    val (host, port) =
        args.first()
            .split(":")
            .let { (host, port) -> host to port.toInt() }

    if (GlobalOptions.clientCanLog) {
        println("Welcome to the group chat! Please enter your name:")
    }
    val name = readlnOrNull() ?: exitProcess(1)

    runBlocking {
        val selectorManager = SelectorManager(Dispatchers.IO)
        val socketBuilder = aSocket(selectorManager).tcp()

        val factory = ProcessFactory(this, host, port, socketBuilder, selectorManager)

        // A peer is mainly a client, but it can also act as a server if needed.
        val peer =
            Peer(
                this,
                { createClient(factory, name) },
                { createServer(factory) },
            )

        peer.start()
    }
}
