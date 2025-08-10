-- Langfuse Models Migration
-- Generated on: 2025-07-26 21:27:42 UTC
-- 
-- This migration adds LLM models from llm.yaml to the Langfuse models table.
-- Models are added as global models (project_id = NULL) with per-token pricing.

BEGIN;

-- openai: gpt-4.1
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273a9742f0f76a491',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gpt-4.1-2025-04-14',
    '(?i)^(gpt-4.1-2025-04-14)$',
    NULL,
    '0.000002000000000000000000000000',
    '0.000008000000000000000000000000',
    NULL,
    'TOKENS',
    '{"tokensPerName": 1, "tokenizerModel": "gpt-4.1-2025-04-14", "tokensPerMessage": 3}'::jsonb,
    'openai'
);

-- openai: gpt-4.1-mini
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273a9914d43dbfdf4',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gpt-4.1-mini-2025-04-14',
    '(?i)^(gpt-4.1-mini-2025-04-14)$',
    NULL,
    '0.000000400000000000000000000000',
    '0.000001600000000000000000000000',
    NULL,
    'TOKENS',
    '{"tokensPerName": 1, "tokenizerModel": "gpt-4.1-mini-2025-04-14", "tokensPerMessage": 3}'::jsonb,
    'openai'
);

-- openai: gpt-4.1-nano
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273a94873de573aa9',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gpt-4.1-nano-2025-04-14',
    '(?i)^(gpt-4.1-nano-2025-04-14)$',
    NULL,
    '0.000000100000000000000000000000',
    '0.000000400000000000000000000000',
    NULL,
    'TOKENS',
    '{"tokensPerName": 1, "tokenizerModel": "gpt-4.1-nano-2025-04-14", "tokensPerMessage": 3}'::jsonb,
    'openai'
);

-- openai: gpt-4o-mini
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273a9c7e69b6ec055',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gpt-4o-mini-2024-07-18',
    '(?i)^(gpt-4o-mini-2024-07-18)$',
    NULL,
    '0.000000150000000000000000000000',
    '0.000000600000000000000000000000',
    NULL,
    'TOKENS',
    '{"tokensPerName": 1, "tokenizerModel": "gpt-4o-mini-2024-07-18", "tokensPerMessage": 3}'::jsonb,
    'openai'
);

-- anthropic: claude-sonnet-4
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273a93addf86a24ac',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'claude-sonnet-4-20250514',
    '(?i)^(claude-sonnet-4-20250514)$',
    NULL,
    '0.000003000000000000000000000000',
    '0.000015000000000000000000000000',
    NULL,
    'TOKENS',
    NULL::jsonb,
    'claude'
);

-- anthropic: claude-3-7-sonnet
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273aa24c380bc6b69',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'claude-3-7-sonnet-20250219',
    '(?i)^(claude-3-7-sonnet-20250219)$',
    NULL,
    '0.000003000000000000000000000000',
    '0.000015000000000000000000000000',
    NULL,
    'TOKENS',
    NULL::jsonb,
    'claude'
);

-- anthropic: claude-3-5-haiku
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273aa67f53e4cfa64',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'claude-3-5-haiku-20241022',
    '(?i)^(claude-3-5-haiku-20241022)$',
    NULL,
    '0.000000800000000000000000000000',
    '0.000004000000000000000000000000',
    NULL,
    'TOKENS',
    NULL::jsonb,
    'claude'
);

-- google: gemini-2.5-pro
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273aa34c1c048a8c0',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gemini-2.5-pro',
    '(?i)^(gemini-2.5-pro)$',
    NULL,
    '0.000001250000000000000000000000',
    '0.000010000000000000000000000000',
    NULL,
    'TOKENS',
    NULL::jsonb,
    'google'
);

-- google: gemini-2.5-flash
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273aa5717c286af03',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gemini-2.5-flash',
    '(?i)^(gemini-2.5-flash)$',
    NULL,
    '0.000000300000000000000000000000',
    '0.000002500000000000000000000000',
    NULL,
    'TOKENS',
    NULL::jsonb,
    'google'
);

-- google: gemini-2.5-flash-lite
INSERT INTO models (
    id,
    created_at,
    updated_at,
    project_id,
    model_name,
    match_pattern,
    start_date,
    input_price,
    output_price,
    total_price,
    unit,
    tokenizer_config,
    tokenizer_id
) VALUES (
    'c19848a273aa49910a75ea87',
    '2025-07-26 21:27:42.000',
    '2025-07-26 21:27:42.000',
    NULL,
    'gemini-2.5-flash-lite-preview-06-17',
    '(?i)^(gemini-2.5-flash-lite-preview-06-17)$',
    NULL,
    '0.000000100000000000000000000000',
    '0.000000400000000000000000000000',
    NULL,
    'TOKENS',
    NULL::jsonb,
    'google'
);


COMMIT;

-- Summary: 10 models added
