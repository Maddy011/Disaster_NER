# -*- coding: utf-8 -*-
"""ner_app.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XCt7GZESa83AuiI8UOnaS6TxUc1FHU9_
"""

import json
import requests
import configparser

import spacy
import spacy_transformers
from spacy import displacy
from spacy.tokens import Span
from transformers import pipeline
from spacy.matcher import PhraseMatcher

import csv
import numpy as np
import pandas as pd

import geopy
import gradio as gr
from geopy.geocoders import Nominatim

offset = None

def get_data(bot_token):
    global offset
    try:
        if offset == None:
            response = requests.get("https://api.telegram.org/bot{}/getUpdates".format(bot_token))
            response_json = json.loads(response.text)
            last_update_id = str(response_json['result'][-1]['update_id'])
            offset = last_update_id
        else:
            response = requests.get('https://api.telegram.org/bot{}/getUpdates?offset={}'.format(bot_token, offset))
            response_json = json.loads(response.text)
            last_update_id = str(response_json['result'][-1]['update_id'])
            offset = last_update_id
        text_list = [r['channel_post']['text'] for r in response_json['result']]
    except KeyError:
        print('KeyError occurred. Possibly empty request result list. Make sure your Telegram Bot Token is correct.')
        text_list = []
    except Exception as e:
        print('An error occurred:', e)
        text_list = []
  
    return text_list

def classify_message(bot_token):
  disaster_docs = []
  classifier = pipeline("sentiment-analysis", model="Madhana/disaster_msges_classifier_v1")
  results = []
  for data in get_data(bot_token):
    classification = classifier(data)
    label = classification[0]['label']
    results.append((data, label))
    if label == 'DISASTER':
      disaster_docs.append(data)
  return disaster_docs

@spacy.Language.component("disaster_ner")
def disaster_ner(doc):
    matcher = PhraseMatcher(doc.vocab)
    patterns = list(nlp.tokenizer.pipe(Tamil_words))
    matcher.add("Tamil_words", None, *patterns)
    matches = matcher(doc)
    spans = [Span(doc, start, end, label="YO!") for match_id, start, end in matches]
    doc.ents = spans
    return doc

Tamil_words = ['மதனா பாலா'] # umm, that's my name in Tamil, consider this as a easter egg in this app lol.

nlp = spacy.load("en_pipeline")
nlp.add_pipe("disaster_ner", name="disaster_ner", before='ner')

entity_types = ["NAME", "STREET", "NEIGHBORHOOD", "CITY", "PHONE NUMBER","YO!"]
df = pd.DataFrame(columns=["Text"] + entity_types)

def create_address(row):
    return f"{row['STREET']}, {row['NEIGHBORHOOD']}, {row['CITY']}"

geolocator = Nominatim(user_agent="disaster-ner-app")

def geocode_address(address):
    try:
        location = geolocator.geocode(address)
        return (location.latitude, location.longitude)
    except:
        return None

def get_ner(bot_token):
  data = classify_message(bot_token)

  for text in data:
    doc = nlp(text)
    row = [text]
    entities = {ent.label_: ent.text for ent in doc.ents}
    for entity_type in entity_types:
        row.append(entities.get(entity_type, ""))
    # html = displacy.render(doc, style="ent")
    # row.append(html)

    num_cols = len(df.columns)
    while len(row) < num_cols:
      row.append("")

    df.loc[len(df)] = row
  
  df['Address'] = df.apply(create_address, axis=1)
  df['Coordinates'] = df['Address'].apply(geocode_address)

  return df

'''
def process_data(your_bot_token):
    return get_ner(your_bot_token)


demo = gr.Blocks()

with demo:
    gr.Markdown("Telegram Disaster Recovery Assistant")
    with gr.Tabs():
        with gr.TabItem("Structured Telegram Messages"):
            with gr.Row():
                your_bot_token = gr.Textbox(type='password', label="Enter your Bot Token")
                ner_df = gr.Dataframe()
                
            ner_button = gr.Button("Get Output")
            clear = gr.Button("Clear")
        with gr.TabItem("User Guide"):
            with gr.Row(): 
              gr.Markdown("""This is an Telegram based Disaster Recovery Assist app that uses Named Entity Recognition to extract important entities from the unstructured text and stores it in an dataframe. 
              You need to provide your personal Telegram Bot API token (API token of the bot that is added to the channel as an administrator) to use this app.
              Steps to create a Telegram Bot: 
              1. Download the Telegram app on your device or use the web version. 
              2. Open the app and search for the "BotFather" bot. 
              3. Start a chat with the BotFather bot by clicking on the "START" button. 
              4. Type "/newbot" and follow the on-screen instructions to create a new bot. 
              5. Choose a name and username for your bot. \6. Once your bot is created, the BotFather will give you a unique API token.
              
              Steps to add your telegram bot to your channel as an administrator: 
              1. Create a new channel or choose an existing one that you want to use the bot in. 
              2. Add your bot to the channel as an administrator. To do this, go to the channel settings, click on "Administrators", and then click on "Add Administrator". Search for your bot and add it to the channel. 
              3. Now you can send commands to the bot in the channel by mentioning the bot using the "@" symbol followed by the bot's username. For example, "@my_bot help" will send the "help" command to the bot.""")
                        

    
    ner_button.click(process_data,inputs=your_bot_token, outputs=ner_df)
    clear.click(lambda: None, None, ner_df, queue=False)  

demo.launch(share=True, debug=True)
'''

import streamlit as st

def process_data(your_bot_token,df):
    df.drop(index=df.index, inplace=True)
    return get_ner(your_bot_token)

st.title("Telegram Disaster Recovery Assistant")

tabs = st.sidebar.tabs(["Structured Telegram Messages", "User Guide"])
if tabs == "Structured Telegram Messages":
    with st.form(key="ner_form"):
        your_bot_token = st.text_input("Enter your Bot Token", type='password')
        ner_df = pd.DataFrame()
        ner_button = st.form_submit_button("Get Output")
        clear = st.button("Clear")
        
    if clear:
        ner_df.drop(index=ner_df.index, inplace=True)
    
    if ner_button:
        ner_df = process_data(your_bot_token, ner_df)
        st.write(ner_df)
        
if tabs == "User Guide":
    st.write("This is an Telegram based Disaster Recovery Assist app that uses Named Entity Recognition to extract important entities from the unstructured text and stores it in an dataframe. You need to provide your personal Telegram Bot API token (API token of the bot that is added to the channel as an administrator) to use this app.")
    st.write("Steps to create a Telegram Bot:")
    st.write("1. Download the Telegram app on your device or use the web version.")
    st.write("2. Open the app and search for the 'BotFather' bot.")
    st.write("3. Start a chat with the BotFather bot by clicking on the 'START' button.")
    st.write("4. Type '/newbot' and follow the on-screen instructions to create a new bot.")
    st.write("5. Choose a name and username for your bot.")
    st.write("6. Once your bot is created, the BotFather will give you a unique API token.")
    st.write("")
    st.write("Steps to add your telegram bot to your channel as an administrator:")
    st.write("1. Create a new channel or choose an existing one that you want to use the bot in.")
    st.write("2. Add your bot to the channel as an administrator. To do this, go to the channel settings, click on 'Administrators', and then click on 'Add Administrator'. Search for your bot and add it to the channel.")
    st.write("3. Now you can send commands to the bot in the channel by mentioning the bot using the '@' symbol followed by the bot's username. For example, '@my_bot help' will send the 'help' command to the bot.")

