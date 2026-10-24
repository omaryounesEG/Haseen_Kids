import sys
import os
import unittest
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_suite():
    print("=" * 70)
    print("🛡️  حَصِين للأطفال | HASEEN KIDS - MASTER VERIFICATION SUITE")
    print("=" * 70)
    start_total = time.perf_counter()

    # 1. Functional Tests
    print("\n[1/4] Running Functional Core Unit Tests...")
    import tests.test_haseen as t_func
    loader = unittest.TestLoader()
    suite_func = loader.loadTestsFromModule(t_func)
    runner = unittest.TextTestRunner(verbosity=1)
    res_func = runner.run(suite_func)

    # 2. Bug & Edge Cases Tests
    print("\n[2/4] Running Bug & Security Edge Case Tests...")
    import tests.test_bugs_edge_cases as t_bugs
    suite_bugs = loader.loadTestsFromModule(t_bugs)
    res_bugs = runner.run(suite_bugs)

    # 3. Performance & Benchmark Tests
    print("\n[3/4] Running Performance & Resource Benchmarks...")
    import tests.test_performance as t_perf
    t_perf.benchmark_filter_engine()
    t_perf.benchmark_memory_and_cpu()
    t_perf.benchmark_local_proxy_latency()

    # 4. UI / UX Tests
    print("\n[4/4] Running Automated Headless UI & UX Tests...")
    import tests.test_ui_ux as t_ui
    suite_ui = loader.loadTestsFromModule(t_ui)
    res_ui = runner.run(suite_ui)

    end_total = time.perf_counter()
    duration = end_total - start_total

    print("\n" + "=" * 70)
    print("📋 FINAL COMPREHENSIVE TEST REPORT SUMMARY")
    print("=" * 70)
    total_tests = res_func.testsRun + res_bugs.testsRun + res_ui.testsRun
    total_failures = len(res_func.failures) + len(res_bugs.failures) + len(res_ui.failures)
    total_errors = len(res_func.errors) + len(res_bugs.errors) + len(res_ui.errors)

    print(f"• Total Automated Unit & Integration Tests: {total_tests}")
    print(f"• Functional Tests: {res_func.testsRun} (Failures: {len(res_func.failures)}, Errors: {len(res_func.errors)})")
    print(f"• Bug & Edge Case Tests: {res_bugs.testsRun} (Failures: {len(res_bugs.failures)}, Errors: {len(res_bugs.errors)})")
    print(f"• UI & UX Tests: {res_ui.testsRun} (Failures: {len(res_ui.failures)}, Errors: {len(res_ui.errors)})")
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
