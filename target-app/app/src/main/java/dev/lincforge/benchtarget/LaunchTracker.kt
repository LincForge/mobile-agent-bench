package dev.lincforge.benchtarget

import android.content.SharedPreferences
import android.util.Log
import dev.lincforge.benchtarget.core.SyncPolicy

/**
 * SPEC.md § Screens 6: launchCount is a persisted counter incremented on every
 * cold start and reset by `pm clear`. The sync component's init decision reads
 * the counter BEFORE this launch's increment (see SyncPolicy) — that ordering
 * is what makes launches #3 and #5 the buttonless ones from cleared data.
 */
object LaunchTracker {
    private const val KEY = "launchCount"
    private var handled = false

    var totalLaunches: Int = 0
        private set
    var retrySyncVisible: Boolean = true
        private set

    fun onColdStart(prefs: SharedPreferences) {
        if (handled) return
        handled = true
        val prior = prefs.getInt(KEY, 0)
        retrySyncVisible = SyncPolicy.showRetrySync(prior)
        totalLaunches = prior + 1
        // commit(): must survive an immediate force-stop between bench launches.
        prefs.edit().putInt(KEY, totalLaunches).commit()
        Log.d(LOG_TAG, "SyncComponent init: launchCount=$prior skip=${!retrySyncVisible}")
    }
}
