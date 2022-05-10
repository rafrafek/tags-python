**Answers**

> 1. What did you find most challenging?

Verifying whether the algorithms I had in my head during development are correct. I've created tests after making implementation. I think TDD approach would be beneficial in this case.

> 2. What is the big-O runtime of your solution?

Based on my calculations it is `O(a*b)` where `a` is the number of assets (input file rows), and `b` is the number of average `expected_life` value.

> 3. What compilers, tools, or runtimes are required to build and run your solution code, and what are the instructions for doing that?

See below.

**Requirements**

- Python - version 3.9 or later

No additional modules required.

**How to run**

Open directory containing this solution in terminal and run command:
```shell
python depreciation_calculator.py assets.csv
```

where `assets.csv` is the name of your input CSV file.

You can also specify output file by using `-o` argument. Default output file is `line_items.csv`.

**How to run included tests**

Run in your terminal:
```shell
python -m unittest depreciation_calculator_test.py
```
