# global-dev-socio-eco-risk-seg

An analytics solution for strategically allocating financial aid and development resources based on socio-economic conditions of countries.

## Segmentation Rules

| Segment | Rule |
|---|---|
| High Risk Country | child_mort > 80 AND income < 5000 |
| Developed Nation | income > 30000 AND life_expec > 78 |
| Emerging Economy | income between 8000 and 30000 |
| High Inflation Risk | inflation > 15 |
| Health Critical | health < 5 AND child_mort > 70 |
| Low GDP Trap | gdpp < 2000 |

## Business Questions Addressed

- High socio-economic risk countries (high mortality + low income + low life expectancy)
- Income vs Life Expectancy relationship
- Health expenditure impact on child mortality
- Inflation risk with low GDP per capita
- Fertility rate vs economic development
- Country segmentation into Developed, Emerging, and High-Risk categories
- Aid allocation prioritization

## To access the streamlit app

https://global-dev-socio-eco-risk-seg.streamlit.app/