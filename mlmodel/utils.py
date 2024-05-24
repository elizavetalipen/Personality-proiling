import PyPDF2
import requests
import asyncio
import pickle
from playwright.sync_api import sync_playwright
from docx import Document
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import pandas as pd
import numpy as np
import re
from joblib import load
import time
from datetime import datetime
from django.conf import settings
import spacy
import textacy
from textacy import text_stats as ts
from textacy import preprocessing as prep
from emoji import demojize
import contractions
from transformers import pipeline


quotes_dict = {
    'intj': '''"Some people would rather die than think. In fact, they do." - Bertrand Russell''',
    'intp': '''"My passion is for scientific truth. I don’t much care about good and evil. I care about what’s true." - Richard Dawkins''',
    'entj': '''"The best way to predict the future is to create it." - Peter Drucker''',
    'entp': '''"I have not failed. I've just found 10,000 ways that won't work." - Thomas A. Edison''',
    'infj': '''"The purpose of life is not to be happy. It is to be useful, 
    to be honorable, to be compassionate, to have it make some difference that you have lived and lived well." - Ralph Waldo Emerson''',
    'infp': '''"All that is gold does not glitter; not all those who wander are lost; 
    the old that is strong does not wither;
    deep roots are not reached by the frost." - J.R.R. Tolkien''',
    'enfj': '''"You have not lived today until you have done something for someone who can never repay you." - John Bunyan''',
    'enfp': '''"The future belongs to those who believe in the beauty of their dreams." - Eleanor Roosevelt''',
    'istj': '''"Success is not the key to happiness. Happiness is the key to success. 
    If you love what you are doing, you will be successful." - Albert Schweitzer''',
    'isfj': '''"You must not lose faith in humanity. Humanity is like an ocean; if a few drops of the ocean are dirty, the ocean does not become dirty." - Mahatma Gandhi''',
    'estj': '''"The only limit to our realization of tomorrow will be our doubts of today." - Franklin D. Roosevelt''',
    'esfj': '''"The purpose of our lives is to be happy." - Dalai Lama''',
    'istp': '''"The way to get started is to quit talking and begin doing." - Walt Disney''',
    'isfp': '''"In the end, it's not the years in your life that count. It's the life in your years." - Abraham Lincoln''',
    'estp': '''"I can't change the direction of the wind, but I can adjust my sails to always reach my destination." - Jimmy Dean''',
    'esfp': '''"The only thing necessary for the triumph of evil is for good men to do nothing." - Edmund Burke'''}

descriptions_dict = {
    'intj': '''INTJs are strategic and analytical thinkers who prefer a logical approach.
    They enjoy solving complex problems and are often seen as independent and innovative. 
    In interactions, they can be direct and concise. Ideal careers include science, engineering, 
    research, and strategic management. 
    They are often focused on long-term goals and value competence and intellectual rigor. 
    Their natural inclination toward strategic thinking and planning makes them excellent 
    at envisioning future possibilities and finding efficient paths to achieve them.''',
    
    'intp': '''INTPs are imaginative and curious individuals who enjoy 
    exploring complex theories and ideas. They prefer to work independently 
    and can be introspective and thoughtful. Possible careers include science, 
    technology, philosophy, and writing. They have a strong desire to 
    understand the underlying principles of the world and excel at abstract thinking. 
    Their deep curiosity often leads them to investigate unusual or theoretical topics, 
    seeking new insights and possibilities.''',
    
    'entj': '''ENTJs are assertive and decisive leaders who excel at strategic 
    planning and problem-solving. They are direct in communication and 
    enjoy challenging others to achieve goals. Suitable careers include 
    business management, law, consulting, and leadership roles. 
    They are often visionary and can quickly assess situations and 
    devise plans for improvement. ENTJs are highly goal-oriented and 
    can be relentless in their pursuit of success, making them natural leaders.''',
    
    'entp': '''ENTPs are energetic and innovative individuals who enjoy 
    debating ideas and seeking out challenges. They are sociable and thrive 
    in dynamic environments. Potential careers include entrepreneurship, 
    law, sales, and creative fields. Their inventive and curious nature 
    leads them to explore a wide range of interests, often pushing 
    boundaries and questioning conventional wisdom. 
    ENTPs enjoy intellectual stimulation and can quickly adapt to changing situations.''',
    
    'infj': '''INFJs are empathetic and insightful individuals who seek 
    meaning in their work and relationships. They prefer deep conversations 
    and strive to help others. Careers in counseling, psychology, teaching, 
    and the arts suit them well. They are highly intuitive and perceptive,
    often understanding others' emotions and needs with ease. 
    INFJs are driven by a desire to make the world a better place 
    and can be deeply compassionate and nurturing.''',
    
    'infp': '''INFPs are imaginative and compassionate individuals 
    who value personal growth and authenticity. 
    They excel in creative thinking and deep connections with others. 
    Ideal careers include writing, counseling, social work, and the arts. 
    They are guided by their personal values and ideals, 
    often striving to find meaning and purpose in their lives. 
    INFPs are sensitive and empathetic, which makes them excellent 
    at understanding and supporting others.''',
    
    'enfj': '''ENFJs are warm and inspiring leaders who excel at connecting 
    with others and helping them achieve their potential. They are skilled 
    communicators and motivators. Careers in teaching, counseling, human resources, 
    and social work suit them. ENFJs possess a natural charisma and can 
    easily build strong relationships with others. They are motivated by 
    the desire to help others grow and thrive, often acting as supportive 
    mentors or guides.''',
    
    'enfp': '''ENFPs are enthusiastic and imaginative individuals who enjoy 
    exploring new ideas and connecting with others. They are expressive 
    and adaptable. Suitable careers include writing, counseling, 
    social work, and the arts. ENFPs have a vibrant and optimistic 
    outlook on life, often inspiring others with their creativity and passion. 
    They are open-minded and value freedom and individuality, 
    seeking opportunities to express themselves and explore new possibilities.''',
    
    'istj': '''ISTJs are organized and responsible individuals who value 
    structure and tradition. They excel at following through on tasks and 
    ensuring accuracy. Potential careers include accounting, law, engineering, 
    and administration. They are known for their reliability and thoroughness,
    often preferring established methods and protocols. ISTJs are conscientious 
    and dependable, making them valuable team members who take their duties seriously.''',
    
    'isfj': '''ISFJs are caring and reliable individuals who value stability 
    and harmony. They are excellent at supporting others and maintaining order. 
    Possible careers include nursing, teaching, social work, and 
    administrative roles. ISFJs are highly attentive to the needs of others 
    and often put others' welfare ahead of their own. They are practical 
    and detail-oriented, making them well-suited for nurturing and supportive roles.''',
    
    'estj': '''ESTJs are assertive and organized individuals who thrive 
    in structured environments. They are efficient and excel at managing 
    projects and people. Ideal careers include business management, 
    law enforcement, and public administration. ESTJs are strong-willed 
    and value tradition and authority. They are known for their decisive 
    and pragmatic approach, making them effective leaders and managers.''',
    
    'esfj': '''ESFJs are sociable and empathetic individuals who enjoy helping 
    others and creating harmonious environments. They excel in supportive roles. 
    Careers in healthcare, teaching, and customer service suit them well. 
    They are warm and nurturing, often going out of their way to care for others. 
    They value community and tradition and thrive in environments where they 
    can contribute to the well-being of those around them.''',
    
    'istp': '''ISTPs are practical and adaptable individuals who enjoy 
    hands-on problem-solving and working independently. They thrive in dynamic 
    environments. Possible careers include engineering, mechanics, 
    and skilled trades. ISTPs have a calm and composed demeanor, 
    often remaining level-headed in high-pressure situations. They enjoy 
    tackling challenges and are resourceful in finding efficient solutions.''',
    
    'isfp': '''ISFPs are artistic and sensitive individuals who value personal 
    expression and creativity. They prefer flexibility and independence. 
    Suitable careers include design, art, music, and healthcare. 
    They are deeply attuned to their surroundings and often express themselves 
    through aesthetics and personal style. They are free-spirited and adaptable, 
    often preferring to take life as it comes.''',
    
    'estp': '''ESTPs are energetic and action-oriented individuals who enjoy 
    taking risks and living in the moment. They thrive in fast-paced environments. 
    Potential careers include sales, entrepreneurship, sports, and emergency services. 
    ESTPs are thrill-seekers who embrace adventure and spontaneity. 
    They are quick thinkers and excel at adapting to new situations, 
    making them effective in high-pressure environments.''',
    
    'esfp': '''ESFPs are lively and outgoing individuals who enjoy 
    entertaining and connecting with others. They thrive in social 
    settings and are natural performers. Ideal careers include acting, 
    hospitality, sales, and event planning. ESFPs have a natural charm 
    and enjoy being at the center of attention. They are spontaneous and 
    enthusiastic, often bringing joy and excitement to those around them.'''
}

def load_models():
    modelnames = ["IE", "NS", "FT", "JP"]
    models = []
    
    for m in modelnames:
        #filename = f"{settings.MEDIA_URL}models/trained_{m}.sav"
        filename = f"C:/Users/lizal/mysite/media/models/trained_{m}.sav"
        with open(filename, "rb") as file:
            loaded_model = pickle.load(file)
            models.append(loaded_model)
        
    return models

nlp = spacy.load("en_core_web_lg")
models = load_models()
classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)

# функция очищает текст и возвращает вектор
def preprocess_text(sample_text:str):
    
    sample_text = clean_text(sample_text)
    data = pd.DataFrame({'cleaned_text': [sample_text]})
    nlp = spacy.load("en_core_web_lg")
    data['vector'] = data['cleaned_text'].apply(lambda text: nlp(text).vector)
    vector_2d = np.array([vec for vec in data['vector']])
    return vector_2d


def make_prediction(sample_text:str):
    
    X_data = preprocess_text(sample_text)
    
    predIE = models[0].predict(X_data)
    predNS = models[1].predict(X_data)
    predFT = models[2].predict(X_data)
    predJP = models[3].predict(X_data)

    predIE = "I" if predIE[0] == 1 else "E"
    predNS = "N" if predNS[0] == 1 else "S"
    predFT = "F" if predFT[0] == 1 else "T"
    predJP = "J" if predJP[0] == 1 else "P"
    mbti_type = predIE + predNS + predFT + predJP

    return mbti_type.lower()


def sentiment_analysis(sample_text:str):
    sentences = [sample_text]
    model_outputs = classifier(sentences)
    res = model_outputs[0]
    emotion_analysis = [(item["label"], item["score"]) for item in res[0:5]]
    return emotion_analysis


def ling_analysis(sample_text:str):
    doc = nlp(sample_text)
    treadability = ts.readability.flesch_kincaid_grade_level(doc)
    diversity = ts.diversity.mtld(doc)
    ling = [("Lexical Diversity", diversity),("Readability", treadability)]
    return ling


def read_text_from_file(file):
    if file.content_type == 'text/plain':
        # Handle plain text files
        return file.read().decode('utf-8')
    elif file.content_type == 'application/pdf':
        # Handle PDF files using PyPDF2
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif file.content_type in ('application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
        # Handle MS Word files using python-docx
        document = Document(file)
        text = ""
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
        return text
    else:
        return ""
    
##############################################
#########################   
# доп. функции по очистке текста
def replace_mbti(text):
    mbti_types = [
    'INTJ', 'INTP', 'ENTJ', 'ENTP',
    'INFJ', 'INFP', 'ENFJ', 'ENFP',
    'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
    'ISTP', 'ISFP', 'ESTP', 'ESFP',
    'INTJS', 'INTPS', 'ENTJS', 'ENTPS',
    'INFJS', 'INFPS', 'ENFJS', 'ENFPS',
    'ISTJS', 'ISFJS', 'ESTJS', 'ESFJS',
    'ISTPS', 'ISFPS', 'ESTPS', 'ESFPS']
    mbti_pattern = '|'.join(mbti_types)
    pattern = re.compile(r'\b(' + mbti_pattern + r')\b', re.IGNORECASE)
    replaced_text = pattern.sub('MBTI', text)
    return replaced_text

def replace_emojis_with_words(text):
    text = demojize(text, delimiters=(" ", " "))
    text = text.replace(":", "").replace("_", " ")
    return text

def create_preprocessing_pipeline():
    preprocessing_functions = [
        prep.normalize.unicode,
        prep.normalize.bullet_points,
        prep.normalize.hyphenated_words,
        prep.normalize.quotation_marks,
        prep.normalize.whitespace,
        prep.remove.accents,
        prep.remove.brackets,
        prep.remove.html_tags,
        prep.replace.urls,
        prep.replace.user_handles,
        prep.remove.punctuation,
        prep.replace.currency_symbols,
        prep.replace.emails,
        prep.replace.hashtags,
        prep.replace.numbers,
        prep.replace.phone_numbers,
        replace_mbti,
        replace_emojis_with_words,]

    preprocessing_pipeline = prep.pipeline.make_pipeline(*preprocessing_functions)
    return preprocessing_pipeline


def clean_text(input_text):
  cleaned_tokens = []
  try:
    input_text = re.sub(r'\|', '', input_text)
    input_text = contractions.fix(input_text)
    pipeline = create_preprocessing_pipeline()
    input_text = pipeline(input_text).lower()
    input_text = re.sub(r'\W+', ' ', input_text)

    doc = nlp(input_text)

    for token in doc:
          # тут очищаем ещё  от стоп-слов и для вектора используем cleaned_tokens
          if not (token.is_punct or token.is_space or token.is_stop or token.is_digit):
              cleaned_tokens.append(token.lemma_)
  except Exception as e:
    print(input_text)
    print(e)
  return ' '.join(cleaned_tokens)






  


  



