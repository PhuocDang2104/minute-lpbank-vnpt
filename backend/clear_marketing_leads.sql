-- Deletes all data from the marketing_leads table
TRUNCATE TABLE marketing_leads RESTART IDENTITY;

-- Alternative if TRUNCATE permission is an issue (but TRUNCATE is preferred for clearing):
-- DELETE FROM marketing_leads;
