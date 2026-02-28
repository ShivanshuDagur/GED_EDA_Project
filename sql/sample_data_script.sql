
--Create temp table with 5000 random candidates
SELECT TOP 5000 CANDIDATE_ID
INTO #RandomCandidates
FROM dbo.candidate
ORDER BY NEWID();

--Exported candidate data 
SELECT c.*
FROM dbo.candidate c
INNER JOIN #RandomCandidates rc ON c.CANDIDATE_ID = rc.CANDIDATE_ID
ORDER BY c.CANDIDATE_ID;

--Export test data for the same candidates
SELECT t.*
FROM dbo.TEST_DATA t
INNER JOIN #RandomCandidates rc ON t.CANDIDATE_ID = rc.CANDIDATE_ID
ORDER BY t.CANDIDATE_ID, t.EXAM_SUBJECT;

-- Cleanup
DROP TABLE #RandomCandidates