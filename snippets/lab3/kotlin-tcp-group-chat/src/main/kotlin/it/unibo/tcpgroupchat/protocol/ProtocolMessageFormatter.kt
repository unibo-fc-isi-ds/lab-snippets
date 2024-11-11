package it.unibo.tcpgroupchat.protocol

import it.unibo.tcpgroupchat.GroupChat

/**
 * A mapper of [ProtocolMessage]s to print-ready formatted strings for the terminal.
 */
object ProtocolMessageFormatter {
    /**
     * Formats a [ProtocolMessage] for printing.
     * @param message the message to format
     * @param chat the chat to get usernames from
     * @return the formatted message
     */
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

/**
 * @see ProtocolMessageFormatter.format

 */
fun ProtocolMessage.format(chat: GroupChat) = ProtocolMessageFormatter.format(this, chat)
