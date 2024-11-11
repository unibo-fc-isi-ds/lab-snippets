package it.unibo.tcpgroupchat

/**
 * An action to be performed by a [Client] when a message is received.
 */
typealias ClientCallback = suspend Client.(ReceivedMessage) -> Unit

/**
 * An action to be performed by a [Server] when a message is received.
 */
typealias ServerCallback = suspend Server.(ReceivedMessage) -> Unit
