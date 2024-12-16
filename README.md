# Cuebox-take-home

## Assumptions

- Input file format is CSV because it is convenient for use in a Dataframe and is easily exportable from Google Sheets.
- Input files will not be so large as to exceed memory on my computer. I may be wrong, but I don't anticipate that the datasets will be that massive.
- A refunded donation should not count as part of a patron's lifetime donations nor their most recent donation since they did not actually make the donation in the end.
- There is a space at the end of Camp 2016 in the API which seems like a mistake because none of the other tags have spaces at the end of them. 
- There should not be duplicate tags in the output since they are redundant.
- There are no other date formats other than the ones specified in the samples since I cannot predict what other formats there are. 

## Decisions
- If a constituent has a first name, last name, and company, the constituent type is 'Person' because they are probably an individual who works at the given company, which does not mean the company itself is a constituent. 
- If first name, last name, and company are empty, the constituent type is Unknown. A first and last name is required to classify a patron as 'Person'. A company name is required to classify a patron as 'Company'. In absence of all of these fields, it did not make sense to use either type.
- By convention, column names generally do not use spaces due to consistency issues, so I took the liberty of adhering to the snake case naming convention.
- The created_at column will follow this format: Year-Month-Day Hour:Minute:Seconds. I chose this because it is a standard format for a timestamp.
- If a tag is not mapped in the API, then it remains as is. Even though the tag is not mapped, it could still be important in the future and worth counting. 

## Questions
- Is there a possibility that my code will need to handle very large datasets?
- Some of the tags map to the same tag in the API- should the data only include these mapped tags once or are duplicate tags fine?
- Should tags which are not mapped in the API be counted?
