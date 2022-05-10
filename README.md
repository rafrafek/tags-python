# Fixed Asset Depreciation

This is a coding challenge.

For answers and solution see **README_solution.md**.

## Problem description

**The Problem**
Our company has a number of assets which have been purchased over the years which depreciate (lose value) over time. For the company's monthly financial statements the accounting team needs to reduce the values of those assets, accounting for the reduction by recording a depreciation expense. Your task is to build a system that performs this calculation.


**An Example**
Suppose the company purchases a laptop for an employee on 1/1/2021. The laptop is valued at $1,500 and has an expected life of 3 years (ending 12/31/2023), after which it can be sold for parts for $300. So it will lose $1,200 over 36 months, $33.33 in each month. Despite months having different numbers of days, the same amount should still be depreciated each month (with two exceptions, to be discussed next).


**Rounding**
In that example we had to round each month's depreciation to the cent, and always in the same direction. The result would be that after 36 months of recognizing $33.33, we'd have a total depreciation of $1,199.88 - 12 cents shy. Your solution must recognize properly rounded whole cents for each asset each month, but also sum up to the proper total over the full expected life. You can solve this a number of ways, including jamming the complete rounding error in the final recognition, or spreading it out over the expected life.


**Partial Months**
The first and last month of the asset's expected life may be partial months. In these cases you must pro-rate the months according to the percentage of the month that is included. As an example suppose the laptop from the earlier example was purchased instead of 1/13/2021, so that it's expected life ends 1/12/2024. In January 2021, 19 out of 31 days were included, so that first month's amortization will be `round(33.333333 * 19 / 31)` or $20.43. In the final month there were 12 out of 31 days, so that month's amortization is `round(33.3333333 * 12 / 31)` or $12.90.

While there might be partial months at the beginning and end, the total useful life will always be expressed as a number of whole months.


**Input**
Your code will need to read a CSV file of fixed assets with all their attributes. An example input file is included at `assets.csv`.

| column | type | description |
| -- | -- | -- |
| asset_id | string | unique identifier for the asset |
| purchase_date | date (YYYY-MM-DD) | date of the start of the depreciation schedule |
| expected_life | integer | expected lifetime in whole months |
| original_value | decimal | starting value of the asset |
| salvage_value | decimal | residual value of the asset after all depreciation |


**Output**
The solution must output a CSV file (`line_items.csv`) of every individual asset's monthly depreciations.

| column | type | description |
| -- | -- | -- |
| asset_id | string | the same asset_id from `assets.csv` |
| month | string (YYYY-MM) | the month of the depreciation |
| amount | decimal | the amount of that month's depreciation |


**Write-up**
In addition to source code solving the above problem, you should include a README file answering the following questions:

1. What did you find most challenging?
2. What is the big-O runtime of your solution?
3. What compilers, tools, or runtimes are required to build and run your solution code, and what are the instructions for doing that?


**Packaging**
Your solution package should include:
- Source code
- A README with answers to the above questions
- the provided `assets.csv` file
- the corresponding solution `line_items.csv` file
