-- Curated compatibility seeds for the demo / case-study brief.
-- The scraped dataset has no model-level compatibility data (only equivalent
-- part numbers), so these rows are hand-verified same-brand + same-appliance
-- pairs used by the example questions. Safe to re-run (idempotent).

INSERT INTO compatibility (part_number, model_number, brand, compatible, confidence_score, source, notes, verified_at)
VALUES
  ('PS11759673', 'WDT780SAEM1', 'Whirlpool', TRUE, 0.97, 'partselect', 'Whirlpool dishwasher filter listed for this model series.', NOW()),
  ('PS11755592', 'WDT780SAEM1', 'Whirlpool', TRUE, 0.95, 'partselect', 'Whirlpool dishwasher lower spray arm for this model series.', NOW()),
  ('PS11755664', 'WDT780SAEM1', 'Whirlpool', TRUE, 0.95, 'partselect', 'Whirlpool dishwasher middle spray arm for this model series.', NOW())
ON CONFLICT (part_number, model_number) DO UPDATE
  SET compatible = EXCLUDED.compatible,
      confidence_score = EXCLUDED.confidence_score,
      source = EXCLUDED.source,
      notes = EXCLUDED.notes,
      verified_at = EXCLUDED.verified_at;
