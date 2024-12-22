# Cuebox-take-home

## How to run
Navigate to the root directory of this project in your terminal and create a virtual environment (pipenv shell). Then, install the dependencies via pipenv install, and run the app via python web_app/app.py. The app can be accessed from your browser at http://127.0.0.1:5000. 

## Assumptions

- Input file format is CSV because it is convenient for use in a Dataframe and is easily exportable from Google Sheets.
- Input files will not be so large as to exceed memory on my computer. I may be wrong, but I don't anticipate that the datasets will be that massive.
- A refunded donation should not count as part of a patron's lifetime donations nor their most recent donation since they did not actually make the donation in the end.
- There is a space at the end of Camp 2016 in the API which seems like a mistake because none of the other tags have spaces at the end of them. 
- There should not be duplicate tags in the output constituents file since they are redundant.
- There are no other date formats other than the ones specified in the samples since I cannot predict what other formats there are. 

## Decisions
- If a constituent has a first name, last name, and company, the constituent type is 'Person' because they are probably an individual who works at the given company, which does not mean the company itself is a constituent. 
- If a constituent does not have a first and last name, and their company entry is something like None or N/A, then the constituent is classified as Unknown. This is because patrons might enter these types of things in the Company field. Given the small scale, I am just using a list to store 'non-company' words, but with larger data, a more complex solution might be necessary.
- If first name, last name, and company are empty, the constituent type is Unknown. A first and last name is required to classify a patron as 'Person'. Acompany name is required to classify a patron as 'Company'. In absence of all of these fields, it did not make sense to use either type.
- By convention, column names generally do not use spaces due to consistency issues, so I took the liberty of adhering to the snake case naming convention.
- The created_at column will follow this format: Year-Month-Day Hour:Minute:Seconds. I chose this because it is a standard format for a timestamp.
- If a tag is not mapped in the API, then it remains as is. Even though the tag is not mapped, it could still be important in the future and worth counting. 
- Backup emails are selected by choosing the first available email associated with the given Patron ID since there does not appear to be any priority in regards to the emails input file.
- Invalid emails and duplicate Patron IDs are logged in the error log for manual review by the user if data does not appear to be correct.
- Non-positive donations indicate faulty/incorrect data in the donation history, so transformation should not continue until this is addressed and corrected.
- The outputs are returned as a Zipfile as I don't believe you are able to return to downloadable files in one Flask response.

## Questions
- Is there a possibility that my code will need to handle very large datasets?
- Some of the tags map to the same tag in the API- should the data only include these mapped tags once or are duplicate tags fine?
- Should tags which are not mapped in the API be counted?
- What should we do with duplicate Patron IDs in the constituents input file? Keeping them in could potentially affect the integrity of the data.

## Possible enhancements
- Unit testing
- Continuous integration 

## Resource Use
I mainly used ChatGPT, the Pandas documentation, and past projects as my aids throughout this project. I haven't used Pandas in about a year and my experience is limited with it, so I firstly needed some help reminding myself of the relevant functions for my use cases, and secondly I sometimes felt like the way I was doing something was not exactly the most optimal way. One specific instance is my use of certain vectorized operations from the Numpy library, which I have not previously used before. Upon doing some research with ChatGPT, I found that some of these Numpy functions were more efficient and intuitive than using the generic apply function. I also used ChatGPT and my past work to help me with writing the HTML/CSS and Javascript code since my experience with these languages is limited as well.
