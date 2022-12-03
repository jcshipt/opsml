WITH NEW_PREDICTIONS AS (
SELECT
  BUNDLE_ID                             TIME_BUNDLE_ID,
  TO_NUMBER(SUM(A.CHECKOUT_TIME),10,4)  PRED_CHECKOUT_TIME,
  TO_NUMBER(SUM(A.DELIVERY_TIME),10,4)  PRED_DELIVERY_MIN,
  TO_NUMBER(SUM(A.PICK_TIME),10,4)      PRED_PICK_TIME,
  TO_NUMBER(SUM(A.DROP_TIME),10,4)      PRED_DROP_TIME,
  TO_NUMBER(SUM(A.DRIVE_TIME),10,4)     PRED_DRIVE_TIME,
  TO_NUMBER(SUM(A.WAIT_TIME),10,4)      PRED_WAIT_TIME
FROM DATA_SCIENCE.{prediction_table} AS A
GROUP BY BUNDLE_ID
),


ACTUAL_DATA AS (
  
SELECT
A.METRO,  
-- CURRENT PREDS -- FILL IN IF MISSING
PRED_CHECKOUT_TIME,
PRED_DELIVERY_MIN,
PRED_PICK_TIME,
PRED_DROP_TIME,
PRED_DRIVE_TIME,
PRED_WAIT_TIME,
  
-- CURRENT FP PREDS
A.PRE_CLAIM_EST_CHECKOUT_MINS_UN_ADJ  AS FP_CHECKOUT_TIME,
A.PRE_CLAIM_EST_SHOP_MINS_UN_ADJ      AS FP_PICK_TIME,
A.PRE_CLAIM_EST_DELIVERY_MINS_UN_ADJ  AS FP_DELIVERY_TIME,
A.PRE_CLAIM_EST_WAIT_MINS_UN_ADJ      AS FP_WAIT_TIME,
A.PRE_CLAIM_EST_DROP_OFF_MINS_UN_ADJ  AS FP_DROP_TIME,
A.PRE_CLAIM_EST_SERVICE_MINS_UN_ADJ   AS FP_SERVICE_TIME, 
A.PRE_CLAIM_EST_OVERALL_MINS_UN_ADJ   AS FP_OVERALL_TIME, 

-- ACTUALS
BUNDLE_PICK_TIME/60            AS ACTUAL_PICK_TIME,
BUNDLE_CHECKOUT_TIME/60        AS ACTUAL_CHECKOUT_TIME,
BUNDLE_DELIVERY_WAIT_TIME/60   AS ACTUAL_WAIT_TIME,
BUNDLE_DELIVERY_TIME/60        AS ACTUAL_DELIVERY_TIME,
DROP_OFF_TIME/60               AS ACTUAL_DROP_OFF_TIME,
ACTUAL_DROP_OFF_TIME + COALESCE(ACTUAL_WAIT_TIME,0) AS ACTUAL_SERVICE_TIME,
COALESCE(ACTUAL_PICK_TIME, 0) + COALESCE(ACTUAL_CHECKOUT_TIME, 0) + ACTUAL_DELIVERY_TIME AS ACTUAL_OVERALL_TIME,
 
  
-- SHOP TIME
COALESCE(PRED_CHECKOUT_TIME, FP_CHECKOUT_TIME) + COALESCE(PRED_PICK_TIME,FP_PICK_TIME) AS PRED_SHOP_TIME,
  
-- SERVICE TIME
COALESCE(PRED_WAIT_TIME, FP_WAIT_TIME) + COALESCE(PRED_DROP_TIME, FP_DROP_TIME) AS PRED_SERVICE_TIME,

-- FP_DRIVE TIME
FP_DELIVERY_TIME - FP_SERVICE_TIME AS FP_DRIVE_TIME,
CASE WHEN BUNDLE_TYPE IN ('TLMD', 'TARP') THEN
  COALESCE(PRED_DRIVE_TIME,FP_DRIVE_TIME) + COALESCE(PRED_WAIT_TIME,FP_WAIT_TIME) + COALESCE(PRED_DROP_TIME, FP_DROP_TIME) 
  ELSE COALESCE(PRED_DELIVERY_MIN, FP_DELIVERY_TIME) END AS PRED_DELIVERY_TIME,
  
-- OVERALL TIME
PRED_SHOP_TIME + PRED_DELIVERY_TIME AS PRED_OVERALL_TIME
              

FROM DATA_SCIENCE.OPSML_FP_BUNDLES_TIME_ACTUALS AS A
INNER JOIN NEW_PREDICTIONS AS B
   ON A.TIME_BUNDLE_ID = B.TIME_BUNDLE_ID
WHERE 1=1
   AND (A.SHOPPER_EXPERIENCE = 'shop_deliver' AND A.PRE_CLAIM_EST_PICK_MINS IS NOT NULL)
   OR (A.SHOPPER_EXPERIENCE = 'delivery' AND A.PRE_CLAIM_EST_DELIVERY_MINS IS NOT NULL)
),

----SERVICE TIME
SERVICE_ERROR AS (
SELECT 
--METRO,
{metro}
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_SERVICE_TIME     AS ACTUAL,
    PRED_SERVICE_TIME       AS PREDICTION,
    FP_SERVICE_TIME         AS FP_PREDICTION,
    (PREDICTION - ACTUAL) AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL) AS FP_DIFF
    FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
 ),
  
DROP_OFF_ERROR AS (
SELECT 
--METRO,
{metro}
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_DROP_OFF_TIME     AS ACTUAL,
    PRED_DROP_TIME           AS PREDICTION,
    FP_DROP_TIME             AS FP_PREDICTION,
    (PREDICTION - ACTUAL)    AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL) AS FP_DIFF
   FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
),


WAIT_ERROR AS (
SELECT 
--METRO,
{metro}
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_WAIT_TIME         AS ACTUAL,
    PRED_WAIT_TIME           AS PREDICTION,
    FP_WAIT_TIME             AS FP_PREDICTION,
    (PREDICTION - ACTUAL)    AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL) AS FP_DIFF
   FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
),

PICK_ERROR AS (
SELECT 
--METRO,
{metro}
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_PICK_TIME         AS ACTUAL,
    PRED_PICK_TIME           AS PREDICTION,
    FP_PICK_TIME             AS FP_PREDICTION,
    (PREDICTION - ACTUAL)    AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL) AS FP_DIFF
   FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
),

CHECKOUT_ERROR AS (
SELECT 
--METRO,
{metro}
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_CHECKOUT_TIME         AS ACTUAL,
    PRED_CHECKOUT_TIME           AS PREDICTION,
    FP_CHECKOUT_TIME             AS FP_PREDICTION,
    (PREDICTION - ACTUAL)        AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL)     AS FP_DIFF
   FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
),

DELIVERY_ERROR AS (
SELECT 
--METRO,
{metro}
  
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_DELIVERY_TIME         AS ACTUAL,
    PRED_DELIVERY_TIME           AS PREDICTION,
    FP_DELIVERY_TIME             AS FP_PREDICTION,
    (PREDICTION - ACTUAL)        AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL)     AS FP_DIFF
   FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
),


OVERALL_ERROR AS (
SELECT 
--METRO,
{metro}
  
    -- NEW PREDICTIONS
ROUND(DIV0(SUM(ABS(NEW_DIFF)),SUM(ABS(ACTUAL))),3) AS NEW_MAPE,
ROUND(DIV0(SUM(ABS(FP_DIFF)),SUM(ABS(ACTUAL))),3) AS FP_MAPE,
ROUND(DIV0(SUM(NEW_DIFF),SUM(ACTUAL)),3) AS NEW_WMPE,
ROUND(DIV0(SUM(FP_DIFF),SUM(ACTUAL)),3) AS FP_WMPE,
ROUND(SQRT(AVG(SQUARE(NEW_DIFF))),2) NEW_RMSE,
ROUND(SQRT(AVG(SQUARE(FP_DIFF))),2) FP_RMSE,
COUNT(1) TOTAL_RECORDS
  
FROM (
  SELECT
    METRO,
    ACTUAL_OVERALL_TIME          AS ACTUAL,
    PRED_OVERALL_TIME            AS PREDICTION,
    FP_OVERALL_TIME             AS FP_PREDICTION,
    (PREDICTION - ACTUAL)        AS NEW_DIFF,
    (FP_PREDICTION - ACTUAL)     AS FP_DIFF
   FROM ACTUAL_DATA
    )
{metro_group}
--GROUP BY METRO
)


SELECT 
  'OVERALL' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM OVERALL_ERROR
UNION ALL 
SELECT 
  'PICK' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM PICK_ERROR
UNION ALL 
SELECT 
  'CHECKOUT' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM CHECKOUT_ERROR
UNION ALL 
SELECT 
  'DELIVERY' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM DELIVERY_ERROR
UNION ALL 
SELECT 
  'WAIT' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM WAIT_ERROR
UNION ALL 
SELECT 
  'SERVICE' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM SERVICE_ERROR 
UNION ALL 
SELECT 
  'DROP_OFF' AS IND,
  {metro}
  TOTAL_RECORDS,
  FP_MAPE,
  NEW_MAPE,
 DIV0((NEW_MAPE - FP_MAPE),FP_MAPE) MAPE_PERC_DIFF,

  FP_WMPE,
  NEW_WMPE,
 DIV0((NEW_WMPE - FP_WMPE),FP_WMPE) WMPE_PERC_DIFF,

  NEW_RMSE,
  FP_RMSE,
  DIV0((NEW_RMSE - FP_RMSE),FP_RMSE) RMSE_PERC_DIFF
FROM DROP_OFF_ERROR