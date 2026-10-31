import sys
import os
import tempfile
import unittest
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Run the whole suite against a throw-away database so the real install is never
# touched (no test domains leak into the parent's whitelist).
_TEST_DB = os.path.join(tempfile.gettempdir(), "haseen_test_suite.db")
if os.path.exists(_TEST_DB):
    try:
        os.remove(_TEST_DB)
    except Exception:
        pass
os.environ["HASEEN_DB"] = _TEST_DB

def _seed_test_db():
    """The suite relies on the built-in whitelist/blacklist being present."""
    try:
        from database.seed_lists import seed_database
        seed_database(only_if_empty=False)
    except Exception as e:
        print(f"(warning: could not seed test DB: {e})")

def run_suite():
    print("=" * 70)
    print("🛡️  حَصِين للأطفال | HASEEN KIDS - MASTER VERIFICATION SUITE")
    print("=" * 70)
    start_total = time.perf_counter()
    _seed_test_db()

    # 1. Functional Tests
    print("\n[1/5] Running Functional Core Unit Tests...")
    import tests.test_haseen as t_func
    loader = unittest.TestLoader()
    suite_func = loader.loadTestsFromModule(t_func)
    runner = unittest.TextTestRunner(verbosity=1)
    res_func = runner.run(suite_func)

    # 2. Bug & Edge Cases Tests
    print("\n[2/5] Running Bug & Security Edge Case Tests...")
    import tests.test_bugs_edge_cases as t_bugs
    suite_bugs = loader.loadTestsFromModule(t_bugs)
    res_bugs = runner.run(suite_bugs)

    # 3. Performance & Benchmark Tests
    print("\n[3/5] Running Performance & Resource Benchmarks...")
    import tests.test_performance as t_perf
    t_perf.benchmark_filter_engine()
    t_perf.benchmark_memory_and_cpu()
    t_perf.benchmark_local_proxy_latency()

    # 4. UI / UX Tests
    print("\n[4/5] Running Automated Headless UI & UX Tests...")
    import tests.test_ui_ux as t_ui
    suite_ui = loader.loadTestsFromModule(t_ui)
    res_ui = runner.run(suite_ui)

    # 5. v1.2.0 feature tests: whitelist everywhere, YouTube embeds,
    #    offline recovery/removal, kid theme
    print("\n[5/5] Running Feature Tests (v1.2.0 + v1.3.0)...")
    import tests.test_v120_features as t_new
    suite_new = loader.loadTestsFromModule(t_new)
    res_new = runner.run(suite_new)

    end_total = time.perf_counter()
    duration = end_total - start_total

    print("\n" + "=" * 70)
    print("📋 FINAL COMPREHENSIVE TEST REPORT SUMMARY")
    print("=" * 70)
    total_tests = res_func.testsRun + res_bugs.testsRun + res_ui.testsRun + res_new.testsRun
    total_failures = (len(res_func.failures) + len(res_bugs.failures)
                      + len(res_ui.failures) + len(res_new.failures))
    total_errors = (len(res_func.errors) + len(res_bugs.errors)
                    + len(res_ui.errors) + len(res_new.errors))

    print(f"• Total Automated Unit & Integration Tests: {total_tests}")
    print(f"• Functional Tests: {res_func.testsRun} (Failures: {len(res_func.failures)}, Errors: {len(res_func.errors)})")
    print(f"• Bug & Edge Case Tests: {res_bugs.testsRun} (Failures: {len(res_bugs.failures)}, Errors: {len(res_bugs.errors)})")
    print(f"• UI & UX Tests: {res_ui.testsRun} (Failures: {len(res_ui.failures)}, Errors: {len(res_ui.errors)})")
    print(f"• Feature Tests (1.2/1.3): {res_new.testsRun} (Failures: {len(res_new.failures)}, Errors: {len(res_new.errors)})")
    print(f"• Total Duration: {duration:.2f} seconds")

    if total_failures == 0 and total_errors == 0:
        print("\n🎉 ALL TESTS PASSED WITH 100% SUCCESS RATE! SYSTEM READY FOR DEPLOYMENT.")
        return 0
    else:
        print(f"\n⚠️ FAILED: {total_failures} failures, {total_errors} errors.")
        return 1

if __name__ == "__main__":
    code = run_suite()
    sys.exit(code)
