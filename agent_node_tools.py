from class_model import model_inference
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI,OpenAI
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate,MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage
from langchain.tools import tool
from doc_gen import doc_specific_gen
from mock_database import fetch_data_RCA_CAPA

from dotenv import load_dotenv
import threading
import speech_recognition as sr
import pygame
import requests

from schema import automotive_state,VoiceAppState
from mock_database import fetch_data,log_currnet_data
from conv2 import audio_player_thread,audio_callback,main_processing_loop,stop_event

load_dotenv()

def Data_Agent_init(state:automotive_state) -> automotive_state:
    prompt = PromptTemplate(template="""
    you are a mechanic working for a company, based on given vehicle parameters and maintenance history to detect early warning signs and forecast
    likely maintenance needs or service demand\n
    parameters:{parameters}\n
    after fetching the maintenence history stop tool calling and detect early warning signs and forecast
    likely maintenance needs or service demand.
    """,input_variables=["parameters"])
    res = prompt.format(parameters=state["data"],)
    return {"messages":[SystemMessage(content=res)],"vehicle_id":state["data"]["ID"],"vehicle_model":state["data"]["model"],"customer_name":state["data"]["customer_name"]}

def llm_agent_init(tools):
    def llm_Agent(state:automotive_state) -> automotive_state:
        model = ChatOpenAI(temperature=0)
        model = model.bind_tools(tools)
        res = model.invoke(state["messages"])
        return {"messages":[res]}
    return llm_Agent

def Diagnosis_Agent_init(state:automotive_state) -> automotive_state:
    prompt = PromptTemplate(template="""
    Run a predictive models to assess probable component failures
    and assign priority level based on the given parameters and data analysis result\n
    parameters:{parameters},\n
    data analysis result:{data_analysis}\n
    after all is done log the problem back into the data base given the detials of the customer which are also provided in parameters, and dont get trapped in a infinite loop just log the data once.
    """,input_variables=["parameters","data_analysis"])
    res = prompt.format(parameters=state["data"],data_analysis=state["Data_agent"])
    return {"messages":[SystemMessage(content=res)]}

def tts_conv_init(state:automotive_state):
    prompt = PromptTemplate(template="""
    you are a customer care agent who calls the customer, youre goal is to convencie them to book a slot in your compony's mechanic garage at any cost, make sure to keep it concise and to the point rather than haveing a long and lengthy conversations.end the converstaion when it seems neccessary dont prolong the conversation unecessarly.first address the coustmer by there name and state why you contected them and make sure you keed your introduction and the whole conversation short and consise after that tell them All the available slots for servicing,convence the coustomer to book a slot at all cost.\n
    the diagnosis of the costumer's vehicle: {vehicle_diagnosis}\n
    the data analysis of the costumer's vehicle: {vehicle_data_analysis}\n
    name of the customer: {name}
    """,input_variables=["vehicle_diagnosis","vehicle_data_analysis","name"])
    res = prompt.format(vehicle_diagnosis=state["Diagnosis_agent"],vehicle_data_analysis=state["Data_agent"],name=state["customer_name"])
    return {"tts_prompt":SystemMessage(content=res)}

def feedback_init(state:automotive_state):
    feedback_data = requests.get(state["feedback_url"]).json()
    prompt = PromptTemplate(template="""
    you are a call centre agent and need to take feedback of the customer regarding there experience of there vehicle service within the mechanic garage of your company.\n
    ask the customer to rate the overall experience from 1 to 5 and to sepecify any troubles encountered if any
    customer name: {name}\n
    customer vehicle model: {model}.
    """,input_variables=["name","model"])
    res = prompt.format(name=feedback_data["name"],model=feedback_data["model"])
    return {"feedback_prompt":SystemMessage(content=res)}

def comunication_init(prompt):
    def customer_comunication(state:automotive_state):
        recognizer = sr.Recognizer()
        mic = sr.Microphone(device_index=0)
        stop_event.clear()
        pygame.mixer.init()
        with mic as source:
            print("[Calibrating for ambient noise...]")
            recognizer.adjust_for_ambient_noise(source, duration=2)
        recognizer.dynamic_energy_threshold = False
        recognizer.energy_threshold = max(recognizer.energy_threshold, 500)
        recognizer.pause_threshold = 0.9
        recognizer.non_speaking_duration = 0.2

        print("[Starting background listener... Speak now.]")
        stop_listening = recognizer.listen_in_background(mic, audio_callback)
        
        player_thread = threading.Thread(target=audio_player_thread)
        player_thread.start()
        
        try:
            result = main_processing_loop(state[prompt])
        except KeyboardInterrupt:
            print("\n[KeyboardInterrupt detected, shutting down...]")
            stop_event.set()
        
        print("\n[Shutting down...]")
        
        if stop_listening:
            stop_listening(wait_for_stop=False)
        
        player_thread.join()
        
        pygame.mixer.quit()
        print("[Application closed.]")

        return {"conv_result":result}
    return customer_comunication

def parser_node_init(schema,agent):
    def parser_node(state:automotive_state) -> automotive_state:
        parser = JsonOutputParser(pydantic_object=schema)
        print(state["messages"])
        prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert data extraction assistant.
        Look at the chat history. Find the last 'ToolMessage' that contains
        the output from the 'model_inference' tool.
        
        Extract the anomaly data from that tool message and format it
        perfectly according to the following JSON schema.
        
        {format_instructions} 
        """),
        MessagesPlaceholder(variable_name="messages")
        ])
        model = ChatOpenAI()
        chain = prompt | model | parser
        parsed = chain.invoke({
            "messages": state["messages"],
            "format_instructions": parser.get_format_instructions()
        })
        return {agent: parsed}
    return parser_node

def condition_def(state:automotive_state):
    print(state["conv_result"])
    if state["conv_result"] == "booked a slot":
        print("the condition output is true")
        return "true"
    else:
        print("the condition output is false")
        return "false"

def RCA_CAPA_init(state:automotive_state):
    prompt = PromptTemplate(template="""
    you are a RCA/CAPA specialist and infer problems from databases it is in the format of (vehical model,problem) these are the reported problems\n
    {problems}\n
    based on these problems produce a RCA/CAPA report about these problems to the automotive manufacturing company make sure it follows the format of a RCA/CAPA report,make sure the RCA/CAPA report is as detailed as possible even if it is 5 or 10 pages long make sure it is detailed and goes over every problem and its RCA/CAPA points this is very important,then draft the RCA/CAPA report into a docx file using the doc_specific_gen tool this is mandatory.
    """,input_variables=['problems'])

    res = prompt.format(problems=fetch_data_RCA_CAPA())

    return {"messages":[SystemMessage(content=res)]}