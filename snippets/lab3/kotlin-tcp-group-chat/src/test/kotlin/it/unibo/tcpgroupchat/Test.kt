package it.unibo.tcpgroupchat

import io.ktor.network.selector.SelectorManager
import io.ktor.network.sockets.aSocket
import it.unibo.tcpgroupchat.protocol.EventType
import it.unibo.tcpgroupchat.protocol.ProtocolMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.concurrent.thread
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 *
 */
class Test {
    private val selectorManager = SelectorManager(Dispatchers.IO)
    private val socketBuilder = aSocket(selectorManager).tcp()

    private fun CoroutineScope.processFactory(
        host: String = "localhost",
        port: Int = 9002,
    ) = ProcessFactory(this, host, port, socketBuilder, selectorManager)

    @BeforeTest
    fun setup() {
        with(GlobalOptions) {
            exitOnStop = false
            logOnlyFromServer = true
            logUUIDs = false
        }
    }

    @Test
    fun chat() {
        val log = StringBuilder()

        fun log(text: String = "") {
            println("[LOG] $text")
            log.append(text)
            log.append("\n")
        }

        suspend fun startPeer(index: Int): Process =
            coroutineScope {
                val factory = processFactory()

                fun createClient(index: Int): Process {
                    val name = "client$index"
                    return factory.createClient(
                        onConnect = { message ->
                            assertEquals(36, uuid.toString().length)
                            message.replyBroadcast(ProtocolMessage(uuid, EventType.CONNECT, name))

                            delay(500L + index * 100L)
                            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, "I'm $name"))

                            delay(600L + index * 100L)
                            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, "I'm $name again"))

                            delay((6 - index) * 1500L)
                            this.stop()
                        },
                        onReceiveFromServer = {},
                        onReceiveFromInput = {},
                        onDisconnect = { message ->
                            message.replyBroadcast(ProtocolMessage(uuid, EventType.TEXT, "Leaving!"))
                            message.replyBroadcast(ProtocolMessage(uuid, EventType.DISCONNECT))
                        },
                    )
                }

                Peer(
                    this,
                    { createClient(index) },
                    { createServer(factory, log = { log(it) }) },
                ).also {
                    it.start()
                }
            }

        thread {
            runBlocking {
                repeat(4) {
                    launch(Dispatchers.IO) {
                        delay((500 * it).toLong())
                        println("Starting peer $it")
                        startPeer(it)
                    }
                }
            }
        }

        Thread.sleep(15000)
        println("\n\nLOG:")
        println(log.toString())

        assertEquals(
            log.trim(),
            javaClass.getResourceAsStream("/output.txt")!!.bufferedReader().readText().trim(),
        )
    }
}
