from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import logging
import tiktoken
import openai
from pydantic import BaseModel, Field
from llm import LLM, LLMConfig, load_api_keys
import subprocess
from datetime import datetime
import typer

app = FastAPI()
cli = typer.Typer()

# test

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Message(BaseModel):
    content: str
    isUser: bool

class ChatHistory(BaseModel):
    messages: List[Message] = Field(default_factory=list)

class UserMessage(BaseModel):
    message: str

class LLMResponse(BaseModel):
    response: str

class SaveResponse(BaseModel):
    message: str

class SonicPiController:
    def __init__(self):
        self.session_folder = None
        self.code_counter = 0
        self.message_history = []
        self.llm = self.initialize_llm()
        self.encoding = tiktoken.encoding_for_model('gpt-4')
        self.current_code = ""
        self.max_retries = 3
        self.save_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved")
        os.makedirs(self.save_folder, exist_ok=True)
        self.create_session_folder()
        self.example_code = self.load_example_code()
        self.system_message = self.create_system_message()

    def load_example_code(self):
        example_file_path = os.path.join(os.path.dirname(__file__), "examples", "all_example_code.txt")
        try:
            with open(example_file_path, 'r') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Warning: Example code file not found at {example_file_path}")
            return ""

    def initialize_llm(self):
        load_api_keys()
        config = LLMConfig(
            model="gpt-4",
            api_type="azure",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version="2023-05-15"
        )
        return LLM(config)

    def create_system_message(self):
        # Load example code and create the system message
        example_code = self.load_example_code()
        return f"""
        You are an expert live coder like Sam Aaron, specializing in creating music with Sonic Pi. 
        Be fun, entertaining, and creative with the music, but adhere to user requests as much as possible. 
        You can perform the following actions:
        1. Generate Sonic Pi code: {{'action': 'generate_code', 'code': 'your code here'}}
        2. Stop the music: {{'action': 'stop'}}
        3. Start a new song: {{'action': 'new_song'}}
        4. Undo the last change: {{'action': 'undo'}}
        5. Respond to user inquiry: {{'action': 'user_inquiry', 'response': 'your text response here'}}

        Important: 
        - If you want to start a completely new song, use the 'new_song' action before 'generate_code'.
        - If you don't use 'new_song', any new code you generate will be added to the currently running music.
        - If the user asks to "start over" or similar, interpret this as a request to stop the current music and prepare for a new song. Don't generate new code immediately unless specifically requested.
        - If the user asks a general question about music or Sonic Pi that doesn't require code generation or music changes, use the 'user_inquiry' action to provide a text response.

        Here is a library of canonical Sonic Pi example code:

        {example_code}

        Always respond with a list of JSON objects in the format specified above, even if there's only one action.
        If you need to include code, put it in the 'code' field of the JSON response.
        Ensure your response is valid JSON. Do not include any explanation text outside of the JSON structure.
        """

    def create_session_folder(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"session_{timestamp}")
        os.makedirs(self.session_folder, exist_ok=True)
        self.code_counter = 0  # Reset code counter for new session

    def execute_sonic_pi_code(self, code):
        try:
            logging.debug(f"Executing Sonic Pi code: {code}")
            process = subprocess.Popen(['sonic_pi4'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=code)
            if process.returncode != 0:
                logging.error(f"Error executing Sonic Pi code: {stderr}")
                return f"Error: {stderr}"
            logging.debug(f"Sonic Pi code executed successfully. Output: {stdout}")
            return None
        except Exception as e:
            logging.exception("Exception occurred while executing Sonic Pi code")
            return f"Error: {str(e)}"

    def stop_sonic_pi(self):
        try:
            logging.debug("Stopping Sonic Pi")
            stop_code = "stop"
            process = subprocess.Popen(['sonic_pi4'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=stop_code)
            if process.returncode != 0:
                logging.error(f"Error stopping Sonic Pi: {stderr}")
                return f"Error stopping music: {stderr}"
            logging.debug("Sonic Pi stopped successfully")
            return None
        except Exception as e:
            logging.exception("Exception occurred while stopping Sonic Pi")
            return f"Error stopping music: {str(e)}"

    def save_code(self, code):
        self.code_counter += 1
        code_file = os.path.join(self.session_folder, f"code_{self.code_counter:03d}.pi")
        with open(code_file, 'w') as f:
            f.write(code)
        return code_file

    def remove_last_code(self):
        if self.code_counter > 0:
            last_code_file = os.path.join(self.session_folder, f"code_{self.code_counter:03d}.pi")
            os.remove(last_code_file)
            self.code_counter -= 1

    def run_previous_code(self):
        for i in range(1, self.code_counter + 1):
            code_file = os.path.join(self.session_folder, f"code_{i:03d}.pi")
            with open(code_file, 'r') as f:
                code = f.read()
            self.execute_sonic_pi_code(code)


    def get_llm_response(self, user_message: str):
        messages = [{"role": "system", "content": self.system_message}] + self.message_history
        messages.append({"role": "user", "content": user_message})
        
        response = self.llm.generate(messages)
        
        self.message_history.append({"role": "user", "content": user_message})
        self.message_history.append({"role": "assistant", "content": response})
        
        return response


    def get_llm_response_with_retry(self, user_input, system_message):
        for attempt in range(self.max_retries):
            try:
                response = self.get_llm_response(user_input, system_message)
                json.loads(response)  # Try to parse the response
                return response
            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    error_message = f"Your last response was not valid JSON. Please fix and respond again. Error: {str(e)}"
                    user_input = f"{user_input}\n\nError in previous response: {error_message}"
                else:
                    logging.error(f"Failed to get valid JSON after {self.max_retries} attempts.")
                    return '{"action": "error", "message": "Failed to generate valid response after multiple attempts."}'
        
    def process_llm_response(self, response: str) -> str:
        try:
            actions = json.loads(response)
            if not isinstance(actions, list):
                actions = [actions]
            
            all_code = []
            other_actions = []
            
            for action in actions:
                if isinstance(action, dict) and 'action' in action:
                    if action['action'] == 'generate_code':
                        all_code.append(action['code'])
                    else:
                        other_actions.append(action)
            
            results = []
            
            # Handle non-code actions
            for action in other_actions:
                if action['action'] == 'stop':
                    result = self.stop_sonic_pi()
                    results.append("Music stopped." if result is None else result)
                elif action['action'] == 'new_song':
                    self.stop_sonic_pi()
                    self.create_session_folder()
                    self.current_code = ""
                    results.append("Ready for a new song.")
                elif action['action'] == 'undo':
                    results.append("Undo functionality not implemented yet.")
                elif action['action'] == 'user_inquiry':
                    results.append(f"Information: {action['response']}")
                else:
                    results.append(f"Unknown action: {action['action']}")
            
            # Combine and execute all code
            if all_code:
                combined_code = "\n\n".join(all_code)
                self.current_code = combined_code
                execution_result = self.handle_code_generation(combined_code)
                results.append(execution_result)
            
            return "\n".join(results)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            logging.debug(f"Raw LLM response: {response}")
            return "Invalid response format from LLM. Failed to parse JSON."
        except Exception as e:
            logging.exception("Error processing LLM response")
            return f"Error processing LLM response: {str(e)}"

    def get_chat_history(self):
        return [
            {"content": msg["content"], "isUser": msg["role"] == "user"}
            for msg in self.message_history
        ]

    def new_chat(self):
        self.message_history = []

    def handle_code_generation(self, code):
        self.save_code(code)
        error = self.execute_sonic_pi_code(code)
        if error:
            logging.error(f"Error executing code: {error}")
            return f"Error executing code: {error}"
        logging.info("Code executed successfully")
        return f"Code executed successfully:\n```\n{code}\n```"

    def save_current_code(self):
        if not self.current_code:
            # If current_code is empty, ask LLM for the running code
            llm_response = self.get_llm_response("Output as text all the code for the current running sound", self.system_message)
            try:
                actions = json.loads(llm_response)
                if isinstance(actions, list) and len(actions) > 0 and actions[0]['action'] == 'user_inquiry':
                    self.current_code = actions[0]['response']
                else:
                    return "Failed to retrieve current running code"
            except json.JSONDecodeError:
                return "Failed to parse LLM response for current running code"

        # Find the next available file name
        i = 1
        while os.path.exists(os.path.join(self.save_folder, f"{i}.pi")):
            i += 1
        file_path = os.path.join(self.save_folder, f"{i}.pi")

        # Save the code
        with open(file_path, 'w') as f:
            f.write(self.current_code)

        return f"Code saved to {file_path}"
 
  
controller = SonicPiController()

@app.get("/api/chat-history", response_model=ChatHistory)
def get_chat_history(self):
    return [
        {"content": msg["content"], "isUser": msg["role"] == "user"}
        for msg in self.message_history
    ]



@app.post("/api/send-message", response_model=LLMResponse)
async def send_message(user_message: UserMessage):
    llm_response = controller.get_llm_response(user_message.message)
    result = controller.process_llm_response(llm_response)
    return LLMResponse(response=result)

@app.post("/api/new-chat")
async def new_chat():
    controller.new_chat()
    return {"message": "New chat started"}

@app.post("/api/stop-music")
async def stop_music():
    result = controller.stop_sonic_pi()
    return {"message": "Music stopped" if result is None else result}


@app.post("/api/save-code", response_model=SaveResponse)
async def save_code():
    result = controller.save_current_code()
    return SaveResponse(message=result)

@cli.command()
def chat():
    """Run the Sonic Pi Controller in CLI mode."""
    print("Welcome to the Sonic Pi Controller!")
    while True:
        user_input = input("User: ")
        if user_input.lower() == 'quit':
            break
        
        llm_response = controller.get_llm_response(user_input)
        print("LLM:", llm_response)
        
        result = controller.process_llm_response(llm_response)
        print("Result:", result)

if __name__ == "__main__":
    typer.run(chat)