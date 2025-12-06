#!/usr/bin/env python3
"""
Test script to verify signal-type-specific prompts
"""

from perplexity_analyzer import StockAnalyzer

def test_prompts():
    """Test all signal types to verify correct prompt generation"""
    analyzer = StockAnalyzer()

    test_cases = [
        ('AAPL', '2025-11-20', 'BUY'),
        ('TSLA', '2025-10-15', 'SELL'),
        ('NVDA', '2025-09-10', 'STRONG BUY'),
        ('GOOGL', '2025-08-25', 'WARNING'),
        ('MSFT', '2025-07-30', None),
    ]

    print("="*80)
    print("Testing Signal-Type-Specific Prompts")
    print("="*80)

    for ticker, date, signal_type in test_cases:
        print(f"\n{'='*80}")
        print(f"Ticker: {ticker}")
        print(f"Date: {date}")
        print(f"Signal Type: {signal_type}")
        print("-"*80)

        # Test Korean prompt
        is_korean = ticker.endswith('.KS') or ticker.endswith('.KQ')
        prompt = analyzer._build_prompt(ticker, is_korean, date, signal_type)

        print("Generated Prompt:")
        print(prompt)
        print("="*80)

    print("\n✅ All prompts generated successfully!")
    print("\nVerify that:")
    print("- BUY asks: '왜 주가가 올랐나요?' (Why did it rise?)")
    print("- SELL asks: '왜 주가가 떨어졌나요?' (Why did it fall?)")
    print("- STRONG BUY asks: '왜 주가가 반등할 가능성이 있나요?' (Why might it rebound?)")
    print("- WARNING asks: '왜 주가가 하락할 위험이 있나요?' (Why might it fall?)")
    print("- None asks: '주가에 어떤 영향을 미쳤나요?' (How did this affect?)")

if __name__ == "__main__":
    test_prompts()
