import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# File paths
html_file_path = 'test.html'
xlsx_file_path = 'questions_answers.xlsx'
output_file_path = 'answer_list.txt'

# Step 1: Parse the HTML file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'lxml')

# Initialize arrays for questions and answers
questions = []
answers = []

# Find all elements of questions
question_divs = soup.find_all('div', class_='formulation clearfix')

for question_div in question_divs:
    # Extract question text
    question_text = question_div.find('div', class_='qtext').get_text(separator=' ', strip=True)
    questions.append(question_text)
    
    # Initialize a temporary list for answers to the current question
    current_answers = []
    for answer_div in question_div.find_all('div', class_='r0') + question_div.find_all('div', class_='r1'):
        # Extract text of each answer
        answer_text = answer_div.find('div').get_text(strip=True)
        current_answers.append(answer_text)
    
    answers.append(current_answers)

# Step 2: Parse the XLSX file and map answers
df = pd.read_excel(xlsx_file_path, header=None)
xlsx_questions = df[1].tolist()
correct_answers = df[2].tolist()

# Mapping Russian letters to English letters
russian_to_english = {
    'а': 'a',
    'б': 'b',
    'в': 'c',
    'г': 'd',
    'д': 'e'
}

# Initialize a list to store the correct answers in order
correct_answers_list = []

# Comparing and finding correct answers
for html_question in questions:
    answer_found = False
    for i, xlsx_question in enumerate(xlsx_questions):
        # Compare the question text
        xlsx_main_question = xlsx_question.split('\n', 1)[0].strip()
        if html_question.strip() == xlsx_main_question:
            correct_letters_russian = list(correct_answers[i].strip())
            correct_answers_for_question = []
            
            for correct_letter_russian in correct_letters_russian:
                correct_letter_english = russian_to_english.get(correct_letter_russian.strip())
                
                if correct_letter_english is None:
                    continue
                
                try:
                    # Extract answer text corresponding to the correct letter from XLSX
                    xlsx_answer_texts = xlsx_question.split('\n')[1:]
                    xlsx_answer_text = next((text.strip() for text in xlsx_answer_texts if text.strip().startswith(f"{correct_letter_russian})")), None)
                    
                    if not xlsx_answer_text:
                        raise ValueError(f"Answer text not found for letter '{correct_letter_russian}' in question '{xlsx_question}'")

                    answer_text_xlsx = xlsx_answer_text.split(' ', 1)[1].strip()
                    
                    # Find the index of this answer text in the HTML answers
                    html_answer_texts = [a.split('.', 1)[1].strip() for a in answers[questions.index(html_question)]]
                    answer_index = html_answer_texts.index(answer_text_xlsx)
                    
                    correct_letter_html = answers[questions.index(html_question)][answer_index].split('.')[0]
                    correct_answers_for_question.append(correct_letter_html)
                except Exception:
                    correct_answers_for_question.append("No answer")
            
            correct_answers_list.append(correct_answers_for_question)
            answer_found = True
            break
    
    if not answer_found:
        correct_answers_list.append(["No answer"])

# Save the correct answers to a file
with open(output_file_path, 'w') as f:
    for i, correct_answers in enumerate(correct_answers_list):
        f.write(f"Question {i+1}: {', '.join(correct_answers)}\n")

# Step 3: Automate the form filling using Selenium

# Chrome options for window maximization
chrome_options = Options()

chrome_options.add_argument(r'--user-data-dir=C:\Users\mate_\AppData\Local\Google\Chrome\User Data')
chrome_options.add_argument(r'--profile-directory=Profile 1')

# Path to ChromeDriver
chromedriver_bin = r'C:\Users\mate_\Downloads\chromedriver-win64\chromedriver.exe'
service = ChromeService(executable_path=chromedriver_bin)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Maximize the browser window
driver.maximize_window()

time.sleep(30)
# Open the test page
#driver.get('https://dl.sechenov.ru/mod/quiz/attempt.php?attempt=4459728&cmid=39505')
# Get the list of all open windows/tabs
windows = driver.window_handles

# Switch to the window you manually opened (usually the last one)
driver.switch_to.window(windows[-1])

# Iterate through each question
for question_number, answer_list in enumerate(correct_answers_list, start=1):
    if "No answer" in answer_list:
        continue  # Skip questions without answers

    try:
        # Locate the entire question block based on the question number
        question_block = driver.find_element(By.XPATH, f"//h3[@class='no']/span[@class='qno' and text()='{question_number}']/ancestor::div[@class='que multichoice deferredfeedback notyetanswered']")

        # Find the 'answer' div within the question block
        answer_div = question_block.find_element(By.XPATH, ".//div[@class='answer']")
        
        # Iterate through each possible answer within the 'answer' div
        possible_answer_divs = answer_div.find_elements(By.XPATH, "./div")
        
        for ans in answer_list:
            for answer_option in possible_answer_divs:
                answernumber_span = answer_option.find_element(By.XPATH, ".//span[@class='answernumber']")
                answernumber_text = answernumber_span.text.strip().replace('.', '')

                # Check if the answernumber matches the correct answer
                if answernumber_text == ans:
                    input_element = answer_option.find_element(By.XPATH, ".//input[@type='checkbox' or @type='radio']")
                    if not input_element.is_selected():
                        input_element.click()
                    break
        
        # Delay between each question (2 seconds)
        #time.sleep(2)

    except Exception as e:
        print(f"Error processing Question {question_number}: {e}")

# Keep the browser open after execution
input("Press Enter to exit and close the browser...")

