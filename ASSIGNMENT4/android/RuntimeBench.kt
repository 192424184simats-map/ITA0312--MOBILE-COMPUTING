// Assignment 4, Part II Task 3 — runtime workloads and timing
object RuntimeBench {
    fun cpuBound(): Int {
        var count = 0
        for (n in 2..2_000_000) {
            var prime = true
            var divisor = 2
            while (divisor * divisor <= n) {
                if (n % divisor == 0) { prime = false; break }
                divisor++
            }
            if (prime) count++
        }
        return count
    }
    fun allocationHeavy(): Int {
        var retained = 0
        repeat(1_000_000) {
            val item = ByteArray(64)
            retained += item.size
        }
        return retained
    }
    inline fun <T> measure(tag: String, block: () -> T): T {
        val start = SystemClock.elapsedRealtime()
        val gcBefore = Debug.getRuntimeStat("art.gc.gc-count").toInt()
        val result = block()
        val elapsed = SystemClock.elapsedRealtime() - start
        val gcAfter = Debug.getRuntimeStat("art.gc.gc-count").toInt()
        Log.i("RuntimeBench", "$tag ms=$elapsed gcs=${gcAfter - gcBefore}")
        return result
    }
}
