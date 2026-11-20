"""Windowed executable entry point (no console or external Python required)."""
import sys

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test-report":
        from mc_finder.diagnostics import run
        raise SystemExit(run(sys.argv[2]))
    from mc_finder.app import main
    raise SystemExit(main())
