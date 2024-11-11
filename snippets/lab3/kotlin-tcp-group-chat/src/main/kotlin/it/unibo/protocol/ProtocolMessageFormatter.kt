package it.unibo.protocol

import it.unibo.GroupChat

/**
 *
 */
object ProtocolMessageFormatter {
    fun format(
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
}

fun ProtocolMessage.format(chat: GroupChat) = ProtocolMessageFormatter.format(this, chat)
