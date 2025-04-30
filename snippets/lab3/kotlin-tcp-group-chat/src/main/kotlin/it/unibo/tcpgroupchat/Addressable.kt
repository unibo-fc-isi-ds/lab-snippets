package it.unibo.tcpgroupchat

/**
 * An addressable entity in the network.
 */
interface Addressable {
    /**
     * The host.
     */
    val host: String

    /**
     * The port.
     */
    val port: Int
}
