# PM Agent Data Directory

This directory contains data files used by the PM Agent system for processing user reviews.

## Structure

- `reviews/` - User review data files
  - `sample_reviews.csv` - Sample user reviews for testing and development

## Files

### sample_reviews.csv
Contains sample user reviews with the following columns:
- `id` - Unique review identifier
- `text` - Review text content
- `rating` - User rating (1-5 stars)
- `source` - Review source (app_store, play_store, web)
- `date` - Review date (YYYY-MM-DD format)

This data is used for testing the review classification and processing pipeline.