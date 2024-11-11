package it.unibo

import java.util.*

/**
 * A data structure for group chat information.
 * This structure is handled only by the main [Server].
 */
class GroupChat {
    /**
     * The names of the users ([Client]s) in the chat, associated with their unique ID.
     */
    private val names = mutableMapOf<UUID, String>()

    /**
     * The unique IDs of the users ([Client]s) currently online.
     */
    private val online = mutableSetOf<UUID>()

    /**
     * The names of the users ([Client]s) currently online.
     */
    val onlineNames: Set<String>
        get() = online.mapNotNull { names[it] }.toSet()

    /**
     * Adds a user to the chat.
     * @param uuid the unique ID of the user
     * @param name the name of the user
     */
    fun join(
        uuid: UUID,
        name: String,
    ) {
        names[uuid] = name
        online.add(uuid)
    }

    /**
     * Removes a user from the chat.
     * @param uuid the unique ID of the user
     */
    fun leave(uuid: UUID) {
        online.remove(uuid)
    }

    /**
     * Gets the name of a user.
     * @param uuid the unique ID of the user
     * @return the name of the user, or `null` if the user is not found
     */
    fun getName(uuid: UUID): String? = names[uuid]
}
