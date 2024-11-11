package it.unibo.protocol

import java.util.*

/**
 * The protocol used by clients and servers to communicate.
 * This is a simple text-based protocol and is composed by:
 * - a 1-byte event type: 0 for text messages, 1 for connection events, 2 for disconnection events
 * - a 36-byte client UUID
 * - a variable-length text message
 * @property uuid the unique identifier of the sender client
 * @property type the type of the event
 * @property text the text message
 */
data class ProtocolMessage(
    val uuid: UUID,
    val type: EventType,
    val text: String = "",
) {
    /**
     * Encodes the message into a sendable string.
     * @return the encoded message
     */
    fun encode(): String {
        return "${type.code}$uuid$text"
    }

    companion object {
        /**
         * Decodes a raw message from a received string.
         * @param encoded the encoded message
         * @return the decoded message
         */
        fun decode(encoded: String): ProtocolMessage {
            val rawType = encoded[0].digitToInt().toByte()
            val type =
                EventType.entries.find { it.code == rawType }
                    ?: throw IllegalArgumentException("Invalid event type $rawType")

            val uuid = UUID.fromString(encoded.substring(1, 37))
            val text = encoded.substring(37)

            return ProtocolMessage(uuid, type, text)
        }
    }
}

/**
 * The types of events that can be sent and received in a [ProtocolMessage].
 * @property code the code of the event
 */
enum class EventType(val code: Byte) {
    TEXT(0),
    CONNECT(1),
    DISCONNECT(2),
}
