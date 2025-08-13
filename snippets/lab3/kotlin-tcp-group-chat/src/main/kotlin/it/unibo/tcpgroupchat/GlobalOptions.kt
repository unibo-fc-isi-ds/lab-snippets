package it.unibo.tcpgroupchat

/**
 * Execution options. The default values apply for the 'main' execution type.
 * Unit tests may change these values.
 */
object GlobalOptions {
    /**
     * Whether to exit the program when a client stops.
     */
    var exitOnStop = true

    /**
     * Whether to log messages only from the server instead of the client.
     */
    var logOnlyFromServer: Boolean = false

    /**
     * Whether to log UUIDs in the messages.
     */
    var logUUIDs = true

    val clientCanLog: Boolean
        get() = !logOnlyFromServer
}
