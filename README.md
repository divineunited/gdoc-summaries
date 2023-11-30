# gdoc-summaries
Request SignOffs Automatically with Google Doc Summaries

- This script looks for Google Docs that the service account has access to
- Within each Google Doc, it looks for a sign off table formatted in a certain way
- Each person who has not signed off that document will get an email
- The email will request sign-off with a link to the doc and an executive summary of that doc.
- This can be run on a daily Cron Job to remind folks within your org to sign off that doc.


## Usage:
If you want your Google Doc to automatically chase for sign-off, then:
- Grant access using the SHARE button within your GDoc to the service account that runs this script
- Create a header in the doc that states "Signoff"
- Create a table that is 3 columns using the @table method in GDocs. 
- The first column can be the 3 titles, we recommend "Name" | "Metadata" | "Date"
- The Name column must use the `@People` option to tag people within your Google org

Here is an example setup:

### Signoff
| Name | RACI | Date |  
| -------- | -------- | -------- |  
|  @DannyVu  |  R  |    |  
|  @MillieCat  |  A  |  2023-12-25  |  
|  @JohnDoe  |  C  |  Left comments  |  
|  @JaneDoe |  C |   |  
|  @RogerFederer |  I |   |  


Note: An empty column under the Date column means that the user has not signed off yet
- that person will get an email for 30 days until they sign off or fill in that column with something
- (in this case, Danny, Jane, and Roger will get emails)


## Executive Summary
- Optionally, define an Executive Summary section as follows:

#### Executive Summary
This is an executive summary that will get sent alongside the email that the 
receiver of the email can quickly read and make sure they're intereseted in the content
before going in and signing off.


## For Developers
- Create a python virtual env
- then: `pip install -r requirements.txt`
- to run tests: `pytest -k test_run`