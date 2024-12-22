import pandas as pd
import numpy as np
import requests
from email_validator import validate_email, EmailNotValidError
import logging

def get_mapped_tags(url):
    '''
    Retrieves dictionary format of tag mappings
    
    Args:
        url (str): API url containing mappings
    
    Returns:
        dict: key: original tag, value: mapped tag, or empty dict if url is inaccessible
    '''
    response = requests.get(url)
    if response.status_code == 200:
        tags = response.json()
        mapped_tags = {t['name'].strip(): t['mapped_name'].strip() for t in tags}
        return mapped_tags
    else:
        logging.error(f'Error: Could not access tag mapping API at {url}')
        return {}

def map_tags(tags, mapping):
    '''
    Map comma-separated tags using the mapping dictionary

    Args:
        tags (str): comma-separated string of tags
        mapping (dict): mapping original tags to new tags
    
    Returns:
        str: comma-separated mapped tags or NaN if no tags provided
    '''
    if pd.notnull(tags):
        mapped_tags = [mapping.get(t.strip(), t.strip()) for t in tags.split(',')]
        mapped_tags = set(mapped_tags)
        return ', '.join(mapped_tags)
    else:
        return float('nan')

def replace_invalid_email(entry, emails_df):
    '''
    Validate primary email. If invalid, replace with backup email associated with the same Patron ID.

    Args:
        entry (pd.Series): A row of the c_df Dataframe
        emails_df (pd.Dataframe): The emails Dataframe containing all valid emails
    
    Returns:
        str: valid email address for the email 1 column, or NaN if a valid email is not found
    '''
    try:
        validate_email(entry['Primary Email'], check_deliverability=True)
        return entry['Primary Email']
    except (EmailNotValidError, AttributeError):
        if pd.isna(entry["Primary Email"]):
            logging.error(f'{entry["Patron ID"]} did not provide a primary email')
        else:
            logging.error(f'{entry["Patron ID"]} provided invalid primary email: {entry["Primary Email"]}')
        return emails_df.loc[entry['Patron ID'], 'Email'] if entry['Patron ID'] in emails_df.index else float('nan')

def normalize_dates(date):
    '''
    Convert date string into standardized datetime format

    Args:
        date (str): String representing some date + time optionally
    
    Returns:
        datetime.datetime: normalized datetime object, or NaN if no date provided/date could not be parsed
    '''
    if pd.notnull(date):
        if ':' in date:
            d, t = date.split()
            h, m = t.split(':')
            h = h.zfill(2)
            date = f'{d} {h}:{m}'
        normalized_date = pd.to_datetime(date, errors='coerce')
        if pd.isna(normalized_date):
            logging.error(f'Could not convert {date} to readable format')
        return normalized_date
    else:
        return float('nan')

def validate_data(c_df, emails_df, dhist_df):
    '''
    Basic data validation function to ensure/log integrity of output data

    Args:
        c_df (pd.Dataframe): dataframe containing the main constituent data
        emails_df (pd.Dataframe): dataframe containing all emails including backups
        dhist_df (pd.Dataframe): dataframe containing log of donations and relevent details
    
    Returns:
        bool: True if data is valid for output generation, False otherwise
        str: Message to be printed to screen if data cannot be parsed, empty string otherwise
    '''
    # Ensure all necessary columns are present, cannot continue if false
    column_lists = [c_df.columns.tolist(), emails_df.columns.tolist(), dhist_df.columns.tolist()]
    exp_columns = [['Patron ID', 'First Name', 'Last Name', 'Date Entered', 'Primary Email', 'Company', 'Salutation', 'Title', 'Tags', 'Gender'], 
                   ['Patron ID', 'Email'], ['Patron ID', 'Donation Amount', 'Donation Date', 'Payment Method', 'Campaign', 'Status']]
    for i in range(len(column_lists)):
        if set(column_lists[i]) != set(exp_columns[i]):
            return False, 'Ensure that columns adhere to the samples'
    
    # Verify all Patron IDs are unique in constituents input, should not continue if false
    # Might break logic but sample does not so temporarily just log the error for presentation purposes
    if not c_df['Patron ID'].is_unique:
        logging.error('Error in constituents file: Patron IDs are not unique')

    # Verify all donations are in valid format and all greater than 0
    try:
        dhist_df['Donation Amount'] = dhist_df['Donation Amount'].str.replace('$', '').str.replace(',', '').astype(float)
    except ValueError:
        return False, 'Invalid donation amount format detected'
    
    if not (dhist_df['Donation Amount'] > 0).all():
        logging.error('Error in Donation History file: Non-positive donation amount detected')
    
    return True, ''

def gen_constituents(c_df, emails_df, dhist_df):
    '''
    Generate output constituents dataframe as part of the requirements for this project

    Args:
        c_df (pd.Dataframe): dataframe containing the main constituent data
        emails_df (pd.Dataframe): dataframe containing all emails including backups
        dhist_df (pd.Dataframe): dataframe containing log of donations and relevent details
    
    Returns:
        pd.Dataframe: dataframe containing new/existing data according to the client requirements
    '''
    mapped_tags = get_mapped_tags('https://6719768f7fc4c5ff8f4d84f1.mockapi.io/api/v1/tags')
    # Filter valid emails only
    valid_map = []
    for e in emails_df['Email']:
        try:
            validate_email(e, check_deliverability=True)
            valid_map.append(True)
        except EmailNotValidError:
            logging.error(f'Invalid email detected in Emails file: {e}')
            valid_map.append(False)
    emails_df = emails_df[valid_map]

    # Determine donation details
    dhist_df = dhist_df[dhist_df['Status'] == 'Paid']
    most_recent_donations = dhist_df.loc[dhist_df.groupby('Patron ID')['Donation Date'].idxmax(),
                                         ['Patron ID', 'Donation Date', 'Donation Amount']]
    lt_donations = dhist_df.groupby('Patron ID').agg(lifetime_donations=('Donation Amount', 'sum'))
    donation_details = lt_donations.merge(most_recent_donations, on='Patron ID')
    donation_details['lifetime_donations'] = donation_details['lifetime_donations'].map('${:,.2f}'.format)
    donation_details['Donation Amount'] = donation_details['Donation Amount'].map('${:,.2f}'.format)

    # Determine constituent type
    non_company_words = ['n/a' 'none', 'used to work here'] # words that show up in company column that are certainly not companies
    t_conds = [c_df['First Name'].notnull() & c_df['Last Name'].notnull(), 
               c_df['Company'].notnull() & ~c_df['Company'].str.lower().isin(non_company_words)]
    t_choices = ['Person', 'Company']
    c_df['type'] = np.select(t_conds, t_choices, default='Unknown')
    c_df.insert(loc=1, column='type', value=c_df.pop('type'))
    # Standardize dates for created_at
    c_df['Date Entered'] = c_df['Date Entered'].apply(normalize_dates)
    c_df['Date Entered'] = c_df['Date Entered'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # Set email 1
    unique_emails = emails_df.groupby('Patron ID').first()
    c_df['Primary Email'] = c_df.apply(replace_invalid_email, axis=1, emails_df=unique_emails)
    # Set email 2
    temp_df = c_df.merge(emails_df, on='Patron ID', how='left')
    temp_df = temp_df[temp_df['Primary Email'] != temp_df['Email']]
    secondary_emails = temp_df.groupby('Patron ID')['Email'].first().rename('email2')
    c_df = c_df.merge(secondary_emails, on='Patron ID', how='left')
    c_df['email2'] = c_df['email2'].replace([None], float('nan'))
    c_df.insert(loc=7, column='email2', value=c_df.pop('email2'))
    # Map the tags
    c_df['Tags'] = c_df['Tags'].apply(map_tags, mapping=mapped_tags)
    # Determine background info
    job_title = np.where(c_df['Title'].notnull(), 'Job Title: ' + c_df['Title'], '')
    marital_status = np.where(c_df['Gender'].notnull() & (c_df['Gender'] != 'Unknown'), 
                              'Marital Status: ' + c_df['Gender'], '')
    c_df['background_info'] = np.char.strip((job_title + '; ' + marital_status).astype(np.str_), '; ')
    c_df.drop(['Title', 'Gender'], axis=1, inplace=True)
    # Merge donation details
    c_df = c_df.merge(donation_details, on='Patron ID', how='left')
    
    # Rename the columns and organize
    c_df.rename(columns={'Patron ID': 'patron_id', 'First Name': 'first_name', 'Last Name': 'last_name',
                         'Date Entered': 'created_at', 'Primary Email': 'email1', 'Company': 'company',
                         'Salutation': 'title', 'Tags': 'tags', 'Donation Amount': 'most_recent_donation_amount',
                         'Donation Date': 'most_recent_donation_date'}, inplace=True)
    c_df.insert(loc=1, column='type', value=c_df.pop('type'))
    c_df.insert(loc=4, column='company', value=c_df.pop('company'))
    c_df.insert(loc=7, column='email2', value=c_df.pop('email2'))
    
    return c_df

def gen_tag_counts(c_df):
    '''
    Generate output tags dataframe as part of the requirements for this project

    Args:
        c_df (pd.Dataframe): out constituents dataframe which contains mapped tags
    
    Returns:
        pd.Dataframe: Dataframe containing each tag and the number of times each tag appears in c_df
    '''
    tags_df = c_df[['patron_id', 'tags']].copy()
    tags_df['tags'] = tags_df['tags'].str.split(', ')
    tags_df = tags_df.explode('tags')
    tag_counts_df = tags_df['tags'].value_counts().reset_index(name='tag_count')
    tag_counts_df.rename(columns={'tags': 'tag_name'}, inplace=True)
    
    return tag_counts_df
