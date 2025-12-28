import os
import queue
import threading
import time
import speech_recognition as sr
import pygame
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, ToolMessage,SystemMessage
from langgraph.graph.message import add_messages
from mock_database_services import fetch_service_data
from slots_booked import fetch_slots_booked_data,log_slots_booked_data
from feedback_database import log_feedback
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

text_queue = queue.Queue()
audio_queue = queue.Queue()
stop_event = threading.Event()
interrupt_event = threading.Event()
current_messages = []
# pygame.mixer.init()

@tool
def shutdown_application():
    """
    shut down the voice assistance loop
    """
    print("shutdown_application tool")
    stop_event.set()
    return "Application shutting down."

tools = [shutdown_application,fetch_service_data,log_slots_booked_data,log_feedback]
llm_with_tools = ChatOpenAI(model="gpt-4o").bind_tools(tools)
openai_client = OpenAI()

def generate_tts(text: str, file_path: str) -> str:
    try:
        with openai_client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="alloy",
            input=text
        ) as response:
            response.stream_to_file(file_path)
        return file_path
    except Exception as e:
        print(f"TTS error: {e}")
        return None

def audio_player_thread():
    while not stop_event.is_set():
        try:
            file_path = audio_queue.get(timeout=1)
            
            if file_path is None:
                continue
            
            if not os.path.exists(file_path):
                print(f"Audio player error: file '{file_path}' does not exist.")
                continue

            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy() and not stop_event.is_set():
                time.sleep(0.1)
            
            pygame.mixer.music.unload()
            
            time.sleep(0.1) 
            
            try:
                os.remove(file_path)
            except PermissionError as e:
                print(f"Audio cleanup warning: could not delete '{file_path}'. file still locked or being accessed. {e}")
            except Exception as e:
                print(f"Audio cleanup error: {e}")

        except queue.Empty:
            continue
    print("Audio player thread shutting down")

def audio_callback(recognizer, audio_data):

    print("\nUser spoke")
    
    if pygame.mixer.music.get_busy():
        print("Interrupting AI playback")
        pygame.mixer.music.stop()

    while not audio_queue.empty():
        try:
            file_path = audio_queue.get_nowait()
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except queue.Empty:
            break
        except Exception as e:
            print(f"audio queue clear error: {e}]")
    
    print("interrupting LLM gen")
    interrupt_event.set()

    print("\ntranscribing")
    try:
        text = recognizer.recognize_openai(audio_data)
        if text.strip():
            text_queue.put(text)
    except sr.UnknownValueError:
        print("could not understand audio")
    except sr.RequestError as e:
        print(f"whisper API error: {e}")

def main_processing_loop(context:str=None):
    # global current_messages
    if context is not None:
        print("context available")
        current_messages.append(context)
    response = "did not book a slot"
    while not stop_event.is_set():
        try:
            if len(current_messages) != 1 and current_messages[-1].type != "tool":
                text = text_queue.get(timeout=1)
            
                interrupt_event.clear()
                
                print(f"User: {text}")
                current_messages.append(HumanMessage(content=text))
            
            stream = llm_with_tools.stream(current_messages)
            
            current_sentence = ""
            full_ai_response = None
            sentence_index = 0
            
            print("AI: ", end="", flush=True)

            for chunk in stream:
                if interrupt_event.is_set():
                    break

                if not full_ai_response:
                    full_ai_response = chunk
                else:
                    full_ai_response += chunk

                current_sentence += chunk.content
                print(chunk.content, end="", flush=True)
                
                if any(p in chunk.content for p in ['.', '?', '!', '\n']):
                    file_path = f"response_part_{sentence_index}.mp3"
                    audio_file = generate_tts(current_sentence, file_path)
                    
                    if audio_file:
                        audio_queue.put(audio_file)
                        sentence_index += 1
                        current_sentence = ""
            
            print()
            
            if current_sentence.strip() and not interrupt_event.is_set():
                file_path = f"response_part_{sentence_index}.mp3"
                audio_file = generate_tts(current_sentence, file_path)
                if audio_file:
                    audio_queue.put(audio_file)

            if full_ai_response:
                current_messages.append(full_ai_response)

            if full_ai_response and full_ai_response.tool_calls:
                print(f"tool call : {full_ai_response.tool_calls}")
                tool_results = []
                for tool_call in full_ai_response.tool_calls:
                    if tool_call['name'] == "log_slots_booked_data":
                        response = "booked a slot"
                        print(response)
                    tool_to_call = {t.name: t for t in tools}[tool_call['name']]
                    result = tool_to_call.invoke(tool_call['args'])
                    tool_results.append(
                        ToolMessage(content=str(result), tool_call_id=tool_call['id'])
                    )
                current_messages.extend(tool_results)
            
            interrupt_event.clear()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"main loop error: {e}")
            
    audio_queue.put(None)
    current_messages.clear()
    return response

if __name__ == "__main__":
    recognizer = sr.Recognizer()
    
    mic = sr.Microphone()
    with mic as source:
        print("calibrating for ambient noise")
        recognizer.adjust_for_ambient_noise(source, duration=2)
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = max(recognizer.energy_threshold, 1500)
    recognizer.pause_threshold = 0.9
    recognizer.non_speaking_duration = 0.2

    print("starting background listener. you can speak now")
    stop_listening = recognizer.listen_in_background(mic, audio_callback)
    
    player_thread = threading.Thread(target=audio_player_thread)
    player_thread.start()
    
    try:
        main_processing_loop("prompt here")
    except KeyboardInterrupt:
        print("\n shutting down")
        stop_event.set()
    
    
    if stop_listening:
        stop_listening(wait_for_stop=False)
    
    player_thread.join()
    
    pygame.mixer.quit()