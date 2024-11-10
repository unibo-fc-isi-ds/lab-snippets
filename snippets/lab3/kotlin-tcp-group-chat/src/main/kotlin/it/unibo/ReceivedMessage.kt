package it.unibo

import io.ktor.utils.io.ByteWriteChannel
import io.ktor.utils.io.writeStringUtf8

/**
 * A message received by the server.
 * @property text the text of the message
 * @property sendChannel the channel to send a reply to the client
 */
data class ReceivedMessage(val text: String, val sendChannel: ByteWriteChannel) {
    suspend fun reply(message: String) {
        if (!sendChannel.isClosedForWrite) {
            sendChannel.writeStringUtf8("$message\n")
        }
    }
}
