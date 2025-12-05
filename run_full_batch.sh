#!/bin/bash
# 전체 종목 일괄 분석 실행 스크립트

echo "=================================================="
echo "🚀 전체 종목 AI 분석 일괄 조회 시작"
echo "=================================================="
echo ""
echo "⚠️  주의사항:"
echo "  - 약 80개 종목을 분석합니다"
echo "  - API 호출 간격 2초 기준 약 3-4분 소요됩니다"
echo "  - Perplexity API 사용량이 발생합니다"
echo ""
read -p "계속하시겠습니까? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "분석을 시작합니다..."
echo ""

python3 batch_analyze_all.py --delay 2

echo ""
echo "=================================================="
echo "✅ 완료!"
echo "=================================================="
echo ""
echo "캐시된 결과를 확인하려면 Streamlit 앱을 실행하세요:"
echo "  streamlit run app.py"
