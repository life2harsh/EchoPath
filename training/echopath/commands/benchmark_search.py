from __future__ import annotations


def run_benchmark_search(args) -> None:
    print("EchoPath search benchmark scaffold")
    print(f"Manifest: {args.manifest or 'data/library/tracks.json'}")
    print("")
    print("Planned output metrics:")
    print("- runtime")
    print("- nodes expanded")
    print("- total path smoothness cost")
    print("- target hit rate")
    print("- artist and genre diversity")
