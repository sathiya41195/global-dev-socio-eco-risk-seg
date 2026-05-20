-- Active: 1775773908470@@mysql-a60948b-sathya41195-1055.d.aivencloud.com@13687@guvi_projects
#Average income per segment.
SELECT segment, AVG(income) AS average_income
FROM country_data
GROUP BY segment;

#Top 10 high-risk countries.
SELECT Country AS High_Risk_Country FROM country_data 
WHERE Segment ='High Risk Country'
order by income asc ,child_mort desc LIMIT 10;

#Countries with highest inflation.
SELECT Country, inflation from country_data
ORDER BY inflation DESC
LIMIT 10;

#Countries with lowest GDP per capita.

SELECT Country, gdpp from country_data
ORDER BY gdpp ASC
LIMIT 10;

#Average life expectancy by segment.


SELECT segment, AVG(life_expec) AS average_life_expectancy
FROM country_data
Group BY Segment;

#Fertility rate comparison across segments.


SELECT segment, AVG(total_fer) AS average_fertility_rate
FROM country_data   
GROUP BY Segment;

#Segmentation of countries in SQL
SELECT Country, CASE WHEN
child_mort > 80 and income < 5000 THEN 'High Risk Country'
WHEN (income > 30000) AND (life_expec > 78) THEN 'Developed Nation'
WHEN (income > 8000) AND (income < 30000) THEN 'Emerging Economy'
WHEN (inflation > 15) THEN 'High Inflation Risk' 
WHEN (health < 5) AND (child_mort > 70) THEN 'Health Critical'
WHEN (gdpp < 2000) THEN 'Low GDP Trap'
ELSE 'Other Country' END AS Segment
FROM country_data;
                