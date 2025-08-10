#!/bin/bash

# Run tests with logging
echo "Running ReviewClassifier tests..."
echo "================================"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run test and capture output
docker compose exec app bash -c "cd /app && PYTHONPATH=/app/src python tests/test_review_classifier.py" 2>&1 | tee logs/test_review_classifier_$(date +%Y%m%d_%H%M%S).log

echo "Test completed. Log saved to logs/ directory"