#!/bin/bash
# Run this manually after market close to update cache
# Or set up as a cron job

cd "$(dirname "$0")"

echo "Starting daily update..."
python3 daily_update.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Update successful! Committing changes..."
    git add stock_data.db
    git commit -m "Auto-update cache: $(date +'%Y-%m-%d %H:%M')"
    git push
    echo "Done! Streamlit Cloud will auto-deploy the updated cache."
else
    echo "Update failed. Check the logs above."
    exit 1
fi
