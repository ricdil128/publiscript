try:
    from ui.book_builder import AIBookBuilder
    from analysis.analyzers import (
        _analyze_market_crisp,
        _analyze_market_legacy,
        resume_analysis,
        continue_analysis,
        _continue_analysis_crisp,
        complete_analysis,
        _complete_analysis_crisp,
        _complete_analysis_legacy
    )
    from generators.crisp_generator import _generate_book_crisp
    from generators.legacy_generator import _generate_book_legacy
    from generators.common_generator import generate_book

    print("✅ Import OK")
except Exception as e:
    print("❌ Errore negli import:", e)
