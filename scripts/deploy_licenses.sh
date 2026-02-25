#!/bin/bash

# Script to deploy LICENSE files to all services missing them
echo "🚀 Deploying LICENSE files to all services..."

# List of services that need LICENSE files
services=(
    "backtest-ui"
    "batch-audit-ui"
    "client-reporting-ui"
    "features-calendar-service"
    "features-delta-one-service"
    "features-onchain-service"
    "features-volatility-service"
    "instruments-service"
    "logs-dashboard-ui"
    "market-data-processing-service"
    "matching-engine-library"
    "ml-deployment-ui"
    "ml-inference-service"
    "ml-training-service"
    "onboarding-ui"
    "pnl-attribution-service"
    "settlement-ui"
    "strategy-service"
    "trading-analytics-ui"
    "unified-defi-execution-interface"
    "unified-market-interface"
)

# Copy LICENSE to each service
for service in "${services[@]}"; do
    if [ -d "$service" ]; then
        echo "✅ Adding LICENSE to $service"
        cp LICENSE_TEMPLATE "$service/LICENSE"
    else
        echo "⚠️ Directory $service not found, skipping..."
    fi
done

echo "📄 LICENSE files deployment complete!"
echo "Total services updated: ${#services[@]}"