package it.unibo

import io.ktor.utils.io.ByteWriteChannel
import io.ktor.utils.io.writeStringUtf8

/**
 * A message received by a [Process].
 * @property text the text of the message
 * @property sendChannel the writable channel to send a reply to
 */
data class ReceivedMessage(val text: String, val sendChannel: ByteWriteChannel) {
    suspend fun reply(message: String) {
        if (!sendChannel.isClosedForWrite) {
            sendChannel.writeStringUtf8("$message\n")
        }
    }
}
