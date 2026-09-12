package me.manga.kira.backend.common.infrastructure.persistence

/**
 * Unused low-level operations, not lifecycle admission. The future real root must drain both
 * participants before release. Only the exact prebound retained controller may invoke operations.
 */
internal sealed interface PersistenceTimerReferenceCalls {
    fun acquireReference(): PersistenceTimerAction

    fun captureThread(): PersistenceTimerAction

    fun releaseOwnedReference(): PersistenceTimerAction

    /** Nonwaiting observations only; never acquires, schedules, releases or upgrades attempt policy. */
    fun observe(): PersistenceTimerObservation
}

internal data class PersistenceTimerObservation(
    val guard: PersistenceTimerCall,
    val utility: PersistenceTimerCall,
    val acquisition: PersistenceTimerCall,
    val scheduling: PersistenceTimerCall,
    val release: PersistenceTimerCall,
    val referenceReturned: Boolean,
    val stockTimerReturned: Boolean,
    val capture: PersistenceTimerCapture,
)
