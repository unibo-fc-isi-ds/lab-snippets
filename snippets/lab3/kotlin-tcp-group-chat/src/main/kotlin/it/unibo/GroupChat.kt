package it.unibo

import java.util.*

/**
 *
 */
class GroupChat {
    private val names = mutableMapOf<UUID, String>()
    private val online = mutableSetOf<UUID>()

    val onlineNames: Set<String>
        get() = online.mapNotNull { names[it] }.toSet()

    fun join(
        uuid: UUID,
        name: String,
    ) {
        names[uuid] = name
        online.add(uuid)
    }

    fun leave(uuid: UUID) {
        names.remove(uuid)
        online.remove(uuid)
    }

    fun getName(uuid: UUID): String? = names[uuid]
}
