import pandas as pd
import numpy as np
import requests
from email_validator import validate_email, EmailNotValidError

def get_mapped_tags(url):
    response = requests.get(url)
    if response.status_code == 200:
        tags = response.json()
        mapped_tags = {t['name'].strip(): t['mapped_name'].strip() for t in tags}
        return mapped_tags
    else:
        print('Could not open url')
        exit(1)

def map_tags(tags, mapping):
    if pd.notnull(tags):
        mapped_tags = [mapping.get(t.strip(), t.strip()) for t in tags.split(',')]
        mapped_tags = set(mapped_tags)
        return ', '.join(mapped_tags)
    else:
        return float('nan')

def replace_invalid_email(entry, emails_df):
    try:
        validate_email(entry['Primary Email'], check_deliverability=True)
        return entry['Primary Email']
    except (EmailNotValidError, AttributeError):
        return emails_df.loc[entry['Patron ID'], 'Email'] if entry['Patron ID'] in emails_df.index else float('nan')

def normalize_dates(date):
    try:
        if pd.notnull(date):
            if ':' in date:
                d, t = date.split()
                h, m = t.split(':')
                h = h.zfill(2)
                date = f'{d} {h}:{m}'
            return pd.to_datetime(date, errors='coerce')
    except ValueError:
        return float('nan')

def gen_constituents():
    fp1 = 'sample_data/constituents.csv'
    fp2 = 'sample_data/emails.csv'
    fp3 = 'sample_data/donation_history.csv'
    mapped_tags = get_mapped_tags('https://6719768f7fc4c5ff8f4d84f1.mockapi.io/api/v1/tags')

    c_df = pd.read_csv(fp1)
    # Filter valid emails only
    emails_df = pd.read_csv(fp2)
    valid_map = []
    for e in emails_df['Email']:
        try:
            validate_email(e, check_deliverability=True)
            valid_map.append(True)
        except EmailNotValidError:
            valid_map.append(False)
    emails_df = emails_df[valid_map]
    # Determine donation details
    dhist_df = pd.read_csv(fp3)
    dhist_df = dhist_df[dhist_df['Status'] == 'Paid']
    dhist_df['Donation Amount'] = dhist_df['Donation Amount'].str.replace('$', '').str.replace(',', '').astype(float)
    most_recent_donations = dhist_df.loc[dhist_df.groupby('Patron ID')['Donation Date'].idxmax(),
                                         ['Patron ID', 'Donation Date', 'Donation Amount']]
    lt_donations = dhist_df.groupby('Patron ID').agg(lifetime_donations=('Donation Amount', 'sum'))
    donation_details = lt_donations.merge(most_recent_donations, on='Patron ID')
    donation_details['lifetime_donations'] = donation_details['lifetime_donations'].map('${:,.2f}'.format)
    donation_details['Donation Amount'] = donation_details['Donation Amount'].map('${:,.2f}'.format)

    # Determine constituent type
    t_conds = [c_df['First Name'].notnull() & c_df['Last Name'].notnull(), c_df['Company'].notnull()]
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
                         'Salutation': 'title', 'Tags': 'tags', 'Donation Amount': 'donation_amount',
                         'Donation Date': 'donation_date'}, inplace=True)
    c_df.insert(loc=1, column='type', value=c_df.pop('type'))
    c_df.insert(loc=4, column='company', value=c_df.pop('company'))
    c_df.insert(loc=7, column='email2', value=c_df.pop('email2'))
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    print(c_df)
    return c_df

def gen_tag_counts(c_df):
    tags_df = c_df[['patron_id', 'tags']].copy()
    tags_df['tags'] = tags_df['tags'].str.split(', ')
    tags_df = tags_df.explode('tags')
    tag_counts_df = tags_df['tags'].value_counts().reset_index(name='tag_count')
    tag_counts_df.rename(columns={'tags': 'tag_name'}, inplace=True)
    return
        

c_df = gen_constituents()
gen_tag_counts(c_df)
