import pandas as pd
import requests
from bs4 import BeautifulSoup


# Открываем HTML файл и читаем его содержимое
with open('test.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Создаем объект BeautifulSoup для парсинга HTML
soup = BeautifulSoup(html_content, 'lxml')

# Initialize arrays for questions and answers
questions = []
answers = []

# Find all elements of questions
question_divs = soup.find_all('div', class_='formulation clearfix')

for question_div in question_divs:
    # Extract question text
    question_text = question_div.find('div', class_='qtext').get_text(separator=' ', strip=True)  # Using separator to handle newlines
    questions.append(question_text)
    
    # Initialize a temporary list for answers to the current question
    current_answers = []
    for answer_div in question_div.find_all('div', class_='r0') + question_div.find_all('div', class_='r1'):
        # Extract text of each answer
        answer_text = answer_div.find('div').get_text(strip=True)
        current_answers.append(answer_text)
    
    answers.append(current_answers)

# Parsing the XLSX file
xlsx_file = 'questions_answers.xlsx'  # Replace with your actual file path
df = pd.read_excel(xlsx_file, header=None)

# Extracting questions, answer variants, and correct answers from the XLSX data
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
        # Compare the question text by extracting the main part from XLSX question (up to the first newline)
        xlsx_main_question = xlsx_question.split('\n', 1)[0].strip()
        if html_question.strip() == xlsx_main_question:  # Handling newlines by extracting the main question part
            # Find the correct answer letters and match them with the answer variants
            correct_letters_russian = list(correct_answers[i].strip())
            correct_answers_for_question = []
            
            for correct_letter_russian in correct_letters_russian:
                correct_letter_english = russian_to_english.get(correct_letter_russian.strip())
                
                # Check if the letter mapping exists
                if correct_letter_english is None:
                    continue
                
                try:
                    # Find the answer text corresponding to the correct letter from the XLSX file
                    xlsx_answer_texts = xlsx_question.split('\n')[1:]  # Split and get the answer texts
                    xlsx_answer_text = next((text.strip() for text in xlsx_answer_texts if text.strip().startswith(f"{correct_letter_russian})")), None)

                    if not xlsx_answer_text:
                        raise ValueError(f"Answer text not found for letter '{correct_letter_russian}' in question '{xlsx_question}'")

                    # Extract the answer text from the XLSX formatted correctly
                    answer_text_xlsx = xlsx_answer_text.split(' ', 1)[1].strip()
                    
                    # Find the index of this answer text in the HTML answers
                    html_answer_texts = [a.split('.', 1)[1].strip() for a in answers[questions.index(html_question)]]
                    answer_index = html_answer_texts.index(answer_text_xlsx)
                    
                    # Get the corresponding HTML letter
                    correct_letter_html = answers[questions.index(html_question)][answer_index].split('.')[0]
                    correct_answers_for_question.append(correct_letter_html)
                except Exception:
                    correct_answers_for_question.append("No answer")
            
            correct_answers_list.append(correct_answers_for_question)
            answer_found = True
            break
    
    if not answer_found:
        correct_answers_list.append(["No answer"])

# Output the correct answers in order
#print("\nCorrect Answers in Order:")
#for i, correct_answers in enumerate(correct_answers_list):
    #print(f"Question {i+1}: Correct Answers: {', '.join(correct_answers)}")

with open('answer_list.txt', 'w') as f:
    for i, correct_answers in enumerate(correct_answers_list):
        f.write(f"Question {i+1}: {', '.join(correct_answers)}\n")
