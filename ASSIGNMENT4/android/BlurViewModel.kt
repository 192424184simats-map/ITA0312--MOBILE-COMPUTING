// Assignment 4, Part II Task 2 — background image-row processing (MVVM)
// Requires AndroidX lifecycle-viewmodel-ktx and kotlinx-coroutines.
sealed interface UiState {
    data object Idle : UiState
    data object Running : UiState
    data class Done(val pixels: IntArray) : UiState
}

fun blurRows(src: IntArray, dst: IntArray, width: Int, height: Int,
             radius: Int, yStart: Int, yEnd: Int) {
    // Simple box blur. Clamp edges; process only rows [yStart, yEnd).
    for (y in yStart until yEnd) {
        for (x in 0 until width) {
            var a = 0L; var r = 0L; var g = 0L; var b = 0L; var count = 0
            for (dy in -radius..radius) for (dx in -radius..radius) {
                val yy = (y + dy).coerceIn(0, height - 1)
                val xx = (x + dx).coerceIn(0, width - 1)
                val c = src[yy * width + xx]
                a += (c ushr 24) and 0xff
                r += (c ushr 16) and 0xff
                g += (c ushr 8) and 0xff
                b += c and 0xff
                count++
            }
            dst[y * width + x] =
                ((a / count).toInt() shl 24) or ((r / count).toInt() shl 16) or
                ((g / count).toInt() shl 8) or (b / count).toInt()
        }
    }
}

class BlurViewModel : ViewModel() {
    val state = MutableStateFlow<UiState>(UiState.Idle)
    fun blur(src: IntArray, width: Int, height: Int) = viewModelScope.launch {
        state.value = UiState.Running
        val dst = IntArray(src.size)
        val chunks = 4
        withContext(Dispatchers.Default) {
            (0 until chunks).map { part ->
                async {
                    blurRows(src, dst, width, height, 8,
                        part * height / chunks, (part + 1) * height / chunks)
                }
            }.awaitAll()
        }
        state.value = UiState.Done(dst)
    }
}
