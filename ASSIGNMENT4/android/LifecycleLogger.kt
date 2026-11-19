// Assignment 4, Part II Task 1.3 — lifecycle callback instrumentation
class MainActivity : AppCompatActivity() {
    private var counter = 0
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        counter = savedInstanceState?.getInt("counter") ?: 0
        Log.i("LifecycleLogger", "onCreate restored=${savedInstanceState != null} counter=$counter")
    }
    override fun onStart() { super.onStart(); Log.i("LifecycleLogger", "onStart") }
    override fun onResume() { super.onResume(); counter++; Log.i("LifecycleLogger", "onResume counter=$counter") }
    override fun onPause() { Log.i("LifecycleLogger", "onPause"); super.onPause() }
    override fun onStop() { Log.i("LifecycleLogger", "onStop"); super.onStop() }
    override fun onDestroy() { Log.i("LifecycleLogger", "onDestroy"); super.onDestroy() }
    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putInt("counter", counter)
        Log.i("LifecycleLogger", "onSaveInstanceState counter=$counter")
    }
}
