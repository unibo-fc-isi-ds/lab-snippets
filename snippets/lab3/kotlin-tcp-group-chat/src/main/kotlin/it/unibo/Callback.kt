package it.unibo

typealias ClientCallback = suspend Client.(ReceivedMessage) -> Unit
typealias ServerCallback = suspend Server.(ReceivedMessage) -> Unit
