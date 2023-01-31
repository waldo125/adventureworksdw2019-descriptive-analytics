-- =============================================================================
-- Author:		    waldo125
-- Create date:		01.29.2023
-- Description: 	year over year revenue comparison AdventureWorksDW2019
-- Execution time:	100 ms
-- =============================================================================

-- where condition for new period
DECLARE @new_period AS NVARCHAR(6)
SET @new_period = (
SELECT CONCAT(2013,RIGHT('00'+CAST(MONTH(GETDATE()) AS VARCHAR(2)),2))
)

-- where condition for old period
DECLARE @old_period AS NVARCHAR(6)
SET @old_period = (
SELECT CONCAT(2012,RIGHT('00'+CAST(MONTH(GETDATE()) AS VARCHAR(2)),2))
)

-- current date used for new period
DECLARE @current_date AS DATE
SET @current_date = (
SELECT CAST(CONCAT(MONTH(GETDATE()),'/',DAY(GETDATE()),'/','2013') AS DATE)
)

;WITH revenue_by_year_month AS (
SELECT
CONCAT(c.CalendarYear,RIGHT('00'+CAST(c.MonthNumberOfYear AS VARCHAR(2)),2)) AS year_month,
SUM(a.SalesAmount) AS year_month_revenue
FROM [AdventureWorksDW2019].[dbo].[FactInternetSales] AS a
INNER JOIN [AdventureWorksDW2019].[dbo].[DimDate] AS c ON a.ShipDateKey = c.DateKey
WHERE CONCAT(c.CalendarYear,RIGHT('00'+CAST(MonthNumberOfYear AS VARCHAR(2)),2)) IN (@new_period,@old_period)
GROUP BY
c.CalendarYear,
c.MonthNumberOfYear
)

, revenue_by_year_month_day AS (
SELECT
CONCAT(c.CalendarYear,RIGHT('00'+CAST(c.MonthNumberOfYear AS VARCHAR(2)),2)) AS year_month,
CAST(a.ShipDate AS DATE) AS year_month_day,
SUM(a.SalesAmount) AS year_month_day_revenue
FROM [AdventureWorksDW2019].[dbo].[FactInternetSales] AS a
INNER JOIN [AdventureWorksDW2019].[dbo].[DimDate] AS c ON a.ShipDateKey = c.DateKey
WHERE CONCAT(c.CalendarYear,RIGHT('00'+CAST(MonthNumberOfYear AS VARCHAR(2)),2)) IN (@new_period,@old_period)
GROUP BY
c.CalendarYear,
c.MonthNumberOfYear,
a.ShipDate
)

-- old period in YoY revenue comparison
SELECT
ROW_NUMBER() OVER (ORDER BY revenue_by_year_month_day.year_month_day ASC) AS selling_day,
revenue_by_year_month.year_month,
revenue_by_year_month_day.year_month_day,
ROUND((revenue_by_year_month_day.year_month_day_revenue / revenue_by_year_month.year_month_revenue),4) AS decimal_year_month_day_revenue,
revenue_by_year_month_day.year_month_day_revenue,
SUM(revenue_by_year_month_day.year_month_day_revenue) OVER (ORDER BY revenue_by_year_month_day.year_month_day ASC) AS cumulative_year_month_day_revenue
FROM revenue_by_year_month
INNER JOIN revenue_by_year_month_day ON revenue_by_year_month.year_month = revenue_by_year_month_day.year_month
WHERE revenue_by_year_month.year_month IN (@old_period)

UNION ALL

-- new period in YoY revenue comparison
SELECT
ROW_NUMBER() OVER (ORDER BY revenue_by_year_month_day.year_month_day ASC) AS selling_day,
revenue_by_year_month.year_month,
revenue_by_year_month_day.year_month_day,
ROUND((revenue_by_year_month_day.year_month_day_revenue / revenue_by_year_month.year_month_revenue),4) AS decimal_year_month_day_revenue,
revenue_by_year_month_day.year_month_day_revenue,
SUM(revenue_by_year_month_day.year_month_day_revenue) OVER (ORDER BY revenue_by_year_month_day.year_month_day ASC) AS cumulative_year_month_day_revenue
FROM revenue_by_year_month
INNER JOIN revenue_by_year_month_day ON revenue_by_year_month.year_month = revenue_by_year_month_day.year_month
WHERE revenue_by_year_month.year_month IN (@new_period) AND revenue_by_year_month_day.year_month_day <= @current_date