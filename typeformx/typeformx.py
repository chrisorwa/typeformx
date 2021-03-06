import csv
import json
import pandas as pd
import re
import requests
from textblob import TextBlob
from textract import process

def get_form(api_key, typeform_id, complete=False):
    typeform_base_url = 'https://api.typeform.com/v1/form/'
    base_url = typeform_base_url +typeform_id + '?key=' +api_key
    
    if complete:
        base_url += '&completed=true'

    return requests.get(base_url).json()
    
def get_typeform_answers(api_key, typeform_id, complete):
    typeform_responses = get_form(api_key, typeform_id, complete)['responses']
    typeform_answers = [response['answers'] for response in typeform_responses]
        
    return typeform_answers
        
def write_to_csv(arr, csv_filename):
    try:
        with open(csv_filename, 'ab') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(arr)
    except IOError:
        print "Error! Could not write to file!"
        
def download_file(url):
    file_extensions = ['csv', 'doc', 'docx', 'eml', 'epub', 'gif', 'htm', 'html', 'jpeg', 'jpg', 'json', 'log', 'mp3', 'msg', 'odt', 'ogg', 'pdf', 'png', 'pptx', 'ps', 'psv', 'rtf', 'tff', 'tif', 'tiff', 'tsv', 'txt', 'wav', 'xls', 'xlsx']
    if url is not None:
        filename = url.split('/')[-1]
        filename = filename.split('?')[0]
        extension = filename.split('.')[-1]
        
        if extension not in file_extensions:
            return None
            
        # NOTE the stream=True parameter
        r = requests.get(url, stream=True)
        try:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk: # filter out keep-alive new chunks
                        f.write(chunk)
        except IOError:
            print "Error! Download failed! Could not write to file!"
            
        return filename
        
    return None

def extract_text(filename):
    if filename is not None:
        return process(filename)
        
    return None
    
class TypeformX:
    def __init__(self, api_key, complete=False):
        self.api_key = api_key
        self.complete = complete
        
    def get_all_forms(self):
        base_url = 'https://api.typeform.com/v1/forms?key='
        base_url += self.api_key
        
        api_response = requests.get(base_url).json()
        cols = ['id', 'name']
        api_response_length = len(api_response)
        
        typeform_frame = pd.DataFrame(columns=cols, index=range(api_response_length))
        
        for i in range(api_response_length):
            typeform_frame.id[i] = api_response[i]['id']
            typeform_frame.name[i] = api_response[i]['name']
            
        return typeform_frame
        
    def get_form_answers(self, typeform_id):
        return get_typeform_answers(self.api_key, typeform_id, self.complete)
        
    def get_form_fields(self, typeform_id):
        typeform_questions = get_form(self.api_key, typeform_id)['questions']
        typeform_fields = set()
        
        for question in typeform_questions:
            if question['id'].lower().startswith('list'):
                question['question'] += '_multiple_choice'
            
            typeform_fields.add(question['question'])
            
        return list(typeform_fields)
        
    def get_form_emails(self, typeform_id):
        emails = []
        for answers in get_typeform_answers(self.api_key, typeform_id, self.complete):
            for answer in answers.values():
                x = re.search('\w+[.|\w]\w+@\w+[.]\w+[.|\w+]\w+', answer)
                if x:
                    emails.append(x.group())
                    
        return emails
        
    def get_file_upload_urls(self, typeform_id):
        file_upload_links = []
        answers = get_typeform_answers(self.api_key, typeform_id, self.complete)
        
        for answer in answers:
            for key in answer.keys():
                if key.startswith('fileupload'):
                    file_upload_links.append(answer[key])
                    
        return file_upload_links

    def extract_cv_text(self, typeform_id):
        extracted_data = []
        
        for obj in get_typeform_answers(self.api_key, typeform_id, self.complete):
            for key in obj.keys():
                x = re.search('\w+[.|\w]\w+@\w+[.]\w+[.|\w+]\w+', obj[key])
                if x:
                    email = x.group()
                    
                if key.startswith('fileupload'):
                    cv_link = obj[key]
                
            try:
                extracted_text = ' '.join(TextBlob(extract_text(download_file(cv_link)).decode('unicode-escape').encode('ascii', 'ignore')).words)
                extracted_data.append([email, cv_link, extracted_text])
            except AttributeError:
                print "No file upload url found... Encountered NoneType"
            except UnicodeDecodeError:
                print "Could not decode text from file"
            except UnboundLocalError:
                print "No fileupload field found"
                
                
        return extracted_data
        
def main():
    api_key = raw_input('Enter API_KEY: ')
    typeform = TypeformX(api_key)
    typeform_df = typeform.get_all_forms()
    print '\n'
    print typeform_df
    
    operation = int(raw_input('\nEnter Operation\n0. Exit\n1. Get Form Fields\n2. Get Form Answers\n\nOperation: '))
    if operation == 0:
        exit()
    
    form_id = int(raw_input('\nEnter typeform id number from above list: '))
    
    if operation == 1:
        fields = typeform.get_form_fields(typeform_df['id'][form_id])
        print '\n'
        print fields
    elif operation == 2:
        answers = typeform.get_form_answers(typeform_df['id'][form_id])
        print '\n'
        print answers

if __name__ == '__main__':
    main()