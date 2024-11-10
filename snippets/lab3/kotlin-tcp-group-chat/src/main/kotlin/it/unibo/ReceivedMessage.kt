package it.unibo

import io.ktor.utils.io.ByteWriteChannel
import io.ktor.utils.io.writeStringUtf8
import it.unibo.protocol.ProtocolMessage

/**
 * A message received by a [Process].
 * @property message the received message
 * @property sendChannel the writable channel to send a reply to
 */
data class ReceivedMessage(val message: ProtocolMessage, val sendChannel: ByteWriteChannel) {
    val uuid get() = message.uuid
    val type get() = message.type
    val text get() = message.text

    suspend fun reply(message: ProtocolMessage) {
        if (!sendChannel.isClosedForWrite) {
            sendChannel.writeStringUtf8("${message.encode()}\n")
        }
    }
}
