package it.unibo.protocol

import java.util.*

/**
 *
 */
data class ProtocolMessage(
    val uuid: UUID,
    val type: EventType,
    val text: String = "",
) {
    fun encode(): String {
        return "${type.code}$uuid$text"
    }

    companion object {
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

enum class EventType(val code: Byte) {
    TEXT(0),
    CONNECT(1),
    DISCONNECT(2),
}
