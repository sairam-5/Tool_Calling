# import boto3
# import requests
# import json
# from botocore.exceptions import ClientError
# from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv() 

# import sys
# import os

# current_script_dir = os.path.dirname(os.path.abspath(__file__))

# package_root = os.path.abspath(os.path.join(current_script_dir, '..'))

# if package_root not in sys.path:
#     sys.path.insert(0, package_root)

# from Tools.weather import get_weather_forecast
# from prompt import SYSTEM_PROMPT



# # AWS and Model Configuration
# AWS_REGION = "us-east-1"
# MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

# FASTAPI_FLIGHT_API_URL = "http://127.0.0.1:8000" 

# class MultiToolAssistant:
#     """
#     Manages the core logic for a multi-tool AI assistant.
#     This class handles user input, communicates with the Bedrock LLM,
#     invokes external tools (Flight and Weather), and manages the single-turn
#     conversation flow. It pre-processes relative dates in user queries
#     before sending them to the LLM.
#     """
#     def __init__(self):
#         """
#         Initializes the Bedrock client and defines the tool configurations
#         for the LLM.
#         """
#         self.bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
#         self.tool_config = {
#             "tools": [
#                 {
#                     "toolSpec": {
#                         "name": "Weather_Tool",
#                         "description": "Gets the current weather or a multi-day forecast for a specified location.",
#                         "inputSchema": {
#                             "json": {
#                                 "type": "object",
#                                 "properties": {
#                                     "location": {"type": "string", "description": "The name of the city or location."},
#                                     "forecast_days": {"type": "integer", "description": "Number of days for the forecast (1-16). Defaults to 1.", "minimum": 1, "maximum": 16}
#                                 },
#                                 "required": ["location"],
#                             }
#                         },
#                     }
#                 },
#                 {
#                     "toolSpec": {
#                         "name": "Flight_Availability_Tool",
#                         "description": "Checks the mock availability of a flight between an origin and destination for a specific date (YYYY-MM-DD). This is a mock tool and does not provide real-time flight data.",
#                         "inputSchema": {
#                             "json": {
#                                 "type": "object",
#                                 "properties": {
#                                     "origin": {"type": "string", "description": "The departure city (e.g., Chennai, Bangalore)."},
#                                     "destination": {"type": "string", "description": "The arrival city (e.g., New York, Delhi)."},
#                                     "travel_date": {"type": "string", "description": "The date of travel in YYYY-MM-DD format (e.g., 2025-06-25)."}
#                                 },
#                                 "required": ["origin", "destination", "travel_date"],
#                             }
#                         },
#                     }
#                 }
#             ]
#         }

#     def _flight_availability_tool(self, origin: str, destination: str, travel_date: str):
#         """
#         Calls the local mock FastAPI service to check flight availability.
#         Handles network errors and returns a structured response.
#         """
#         try:
#             payload = {
#                 "origin": origin,
#                 "destination": destination,
#                 "travel_date": travel_date
#             }
#             headers = {"Content-Type": "application/json"}

#             api_url = f"{FASTAPI_FLIGHT_API_URL}/flights/check_availability"
#             response = requests.post(api_url, json=payload, headers=headers)
#             response.raise_for_status() # Raises an HTTPError for bad responses

#             return response.json()

#         except requests.exceptions.ConnectionError:
#             return {"error": True, "message": f"Flight tool: Connection error. Ensure mock flight API is running at {FASTAPI_FLIGHT_API_URL}."}
#         except requests.exceptions.RequestException as req_err:
#             return {"error": True, "message": f"Flight tool: Request error: {str(req_err)}."}
#         except Exception as e:
#             return {"error": True, "message": f"Flight tool: Processing error: {str(e)}."}

#     def _invoke_tool(self, tool_use_block: dict):
#         """
#         Executes the specified tool function based on the LLM's request.
#         This acts as a router for the tools defined in tool_config.
#         """
#         tool_name = tool_use_block["name"]
#         input_data = tool_use_block["input"]
#         tool_use_id = tool_use_block["toolUseId"]

#         tool_output = {"error": True, "message": "Tool execution failed or tool not recognized."}

#         # Indicate which tool is to be called 
#         print(f"Invoking tool: {tool_name} with input: {input_data}")

#         if tool_name == "Weather_Tool":
#             location = input_data.get("location")
#             forecast_days = input_data.get("forecast_days", 1)
#             tool_output = get_weather_forecast(location, forecast_days)
#         elif tool_name == "Flight_Availability_Tool":
#             origin = input_data.get("origin")
#             destination = input_data.get("destination")
#             travel_date = input_data.get("travel_date")
#             tool_output = self._flight_availability_tool(origin, destination, travel_date)
        
#         return {"toolResult": {"toolUseId": tool_use_id, "content": [{"json": tool_output}]}}

#     def _resolve_relative_date(self, text: str) -> tuple[str, str]:
#         """
#         Parses common relative date terms (e.g., "tomorrow", "coming Friday", "next Tuesday")
#         in the input text and converts them to a YYYY-MM-DD format.
        
#         Returns the updated text with the absolute date and the resolved date string
#         (or the original text and None if no relative date is found).
#         """
#         today = date.today()
        
#         lower_text = text.lower()

#         # Handle "tomorrow"
#         if "tomorrow" in lower_text:
#             resolved_date = today + timedelta(days=1)
#             resolved_date_str = resolved_date.isoformat()
#             text = text.replace("tomorrow", resolved_date_str, 1) 
#             return text, resolved_date_str
        
#         # Handle "coming [day of week]" or "next [day of week]"
#         days_of_week_map = {
#             "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
#             "friday": 4, "saturday": 5, "sunday": 6
#         }
        
#         for day_name, day_index in days_of_week_map.items():
#             trigger_phrases = [f"coming {day_name}", f"next {day_name}"]
#             for phrase in trigger_phrases:
#                 if phrase in lower_text:
#                     today_weekday = today.weekday() # Monday is 0, Sunday is 6
#                     target_weekday = day_index

#                     days_ahead = target_weekday - today_weekday
#                     if days_ahead <= 0: # If target day is today or in the past, get it for next week
#                         days_ahead += 7
                    
#                     resolved_date = today + timedelta(days=days_ahead)
#                     resolved_date_str = resolved_date.isoformat()
                    
#                     text = text.replace(phrase, resolved_date_str, 1) 
#                     return text, resolved_date_str

#         return text, None # Return None as resolved_date_str if no match

#     def chat(self, user_input: str):
#         """
#         Manages a single turn of conversation with the AI assistant.
#         This includes pre-processing user input, interacting with the Bedrock LLM,
#         invoking necessary tools, and printing the final response.
#         """
#         # Resolve any relative dates in the user's input
#         processed_input, _ = self._resolve_relative_date(user_input)
        
#         # Prepare the initial user message block for the LLM
#         user_message_block = {"role": "user", "content": [{"text": processed_input}]}
        
#         try:
#             # First call to Bedrock - Model either responds directly or requests tool use
#             # Pass only the current user message
#             response = self.bedrock_client.converse(
#                 modelId=MODEL_ID,
#                 messages=[user_message_block], # Only the user's current query
#                 system=[{"text": SYSTEM_PROMPT}],
#                 toolConfig=self.tool_config,
#             )

#             assistant_response_message = response["output"]["message"]

#             # If the LLM requested tool(s), invoke them and send results back
#             if response["stopReason"] == "tool_use":
#                 tool_results_to_llm = [] 
#                 for content_item in assistant_response_message["content"]:
#                     if "toolUse" in content_item:
#                         tool_result = self._invoke_tool(content_item["toolUse"])
#                         tool_results_to_llm.append(tool_result) 

#                 tool_result_message_block = {"role": "user", "content": tool_results_to_llm}

#                 #  Make a second call to Bedrock for the final response.
#                 # This call includes the original user message, the assistant's tool-use request,
#                 # and the results from the tool execution.
#                 second_response = self.bedrock_client.converse(
#                     modelId=MODEL_ID,
#                     messages=[user_message_block, assistant_response_message, tool_result_message_block], 
#                     system=[{"text": SYSTEM_PROMPT}],
#                     toolConfig=self.tool_config,
#                 )
                
#                 final_assistant_message = second_response["output"]["message"]
                
#                 #  Print the final text response from the assistant
#                 for content_item in final_assistant_message["content"]:
#                     if "text" in content_item:
#                         print(f"Assistant: {content_item['text']}")
#                         return 

#             #  Handle direct text response (no tool use was needed)
#             elif response["stopReason"] == "end_turn":
#                 for content_item in assistant_response_message["content"]:
#                     if "text" in content_item:
#                         print(f"Assistant: {content_item['text']}")
#                         return 

#             # Handle unexpected stop reasons
#             else:
#                 print(f"Assistant: An unexpected response occurred. Reason: {response['stopReason']}. Please try again.")

#         except ClientError as e:
#             error_message = e.response.get("Error", {}).get("Message", "An unknown AWS service error occurred.")
#             print(f"Assistant: Error during Bedrock interaction: {error_message}. Please check AWS configuration/permissions.")
#         except Exception as e:
#             print(f"Assistant: An unexpected internal error occurred: {str(e)}.")

# # Main execution block for running the assistant 
# if __name__ == "__main__":
#     assistant = MultiToolAssistant()
    
#     user_query = input("\nYou: ").strip()
    
#     if user_query.lower() == "exit":
#         print("--- Exiting Assistant. ---")
#     elif not user_query:
#         print("No input provided. Please enter your query.")
#     else:
#         assistant.chat(user_query)


# client = boto3.client("bedrock-runtime", region_name="us-east-1")
# model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
# propt = "hey i am in chenai i have a plan to go to bengalore through flight do you know the cost of the flight?" 

# conversation = [
#     {
#         "role": "user",
#         "content": [{"text":propt}]

#     }
# ] 

# response = client.converse(
#     modelId=model_id,
#     messages=conversation,
#     inferenceConfig={"maxTokens": 1000, "temperature": 0.5}
# )

# output = response["output"]["message"]["content"][0]["text"]
# print(output)






# claude_agent.py

# This script integrates Amazon Bedrock's Claude model with several custom tools:
# Weather (local function call), Flight, Train, and Hotel (FastAPI services).
# It orchestrates the conversation flow based on a detailed system prompt.

# import boto3
# import requests
# import json
# import datetime # For date handling, if needed for complex date conversions

# import sys
# import os

# current_script_dir = os.path.dirname(os.path.abspath(__file__))

# package_root = os.path.abspath(os.path.join(current_script_dir, '..'))

# if package_root not in sys.path:
#     sys.path.insert(0, package_root)


# # Import the system prompt from the separate prompt.py file.
# from prompt import SYSTEM_PROMPT

# # Import the local weather function.
# # Ensure your weather.py file contains the get_weather_forecast function as previously defined.
# from Tools.weather  import get_weather_forecast

# # --- Configuration Constants ---
# # AWS Region where your Bedrock model is available.
# AWS_REGION = "us-east-1" # Or your preferred AWS region, e.g., "us-west-2"

# # Model ID for Claude. Adjust as needed based on availability and preference.
# # For a full list of supported models, refer to AWS Bedrock documentation.
# MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0" # A good balance of capability and cost

# # Base URLs for our locally running FastAPI services.
# # Ensure these services are running on their respective ports before running this agent.
# FLIGHT_SERVICE_URL = "http://127.0.0.1:8001"
# TRAIN_SERVICE_URL = "http://127.0.0.1:8002"
# HOTEL_SERVICE_URL = "http://127.0.0.1:8003"

# # The maximum number of recursive calls allowed in the tool_use_demo function.
# # This helps prevent infinite loops during complex tool interactions.
# MAX_RECURSIONS = 5

# class ClaudeAgent:
#     """
#     Manages the conversation with Claude on Amazon Bedrock, integrating various tools
#     for travel planning.
#     """

#     def __init__(self):
#         """
#         Initializes the Bedrock Runtime client and sets up the tool configurations.
#         """
#         # Prepare the system prompt as a list of text content.
#         self.system_prompt = [{"text": SYSTEM_PROMPT}]

#         # Prepare the tool configuration by getting specifications for all tools.
#         self.tool_config = {"tools": self._get_tool_specs()}

#         # Create a Bedrock Runtime client in the specified AWS Region.
#         self.bedrock_runtime_client = boto3.client(
#             "bedrock-runtime", region_name=AWS_REGION
#         )

#     def run(self):
#         """
#         Starts the conversation with the user and handles the interaction with Bedrock.
#         """
#         print("\n--- Claude AI Travel Planner ---")
#         print("Hello! I'm your AI Travel Planner. How can I assist you today?")
#         print("Type 'x' to exit at any time.")

#         conversation = [] # Stores the history of messages for the conversation.

#         user_input = self._get_user_input("Your travel request")

#         while user_input is not None:
#             # Create a new user message and append it to the conversation history.
#             message = {"role": "user", "content": [{"text": user_input}]}
#             conversation.append(message)

#             # Send the entire conversation history to Amazon Bedrock.
#             bedrock_response = self._send_conversation_to_bedrock(conversation)

#             # Recursively process the model's response until it reaches an 'end_turn'
#             # or the recursion limit is hit.
#             self._process_model_response(
#                 bedrock_response, conversation, max_recursion=MAX_RECURSIONS
#             )

#             # Prompt for next user input to continue the conversation.
#             user_input = self._get_user_input("Your next request")

#         print("\n--- Thank you for using the Claude AI Travel Planner! ---")

#     def _send_conversation_to_bedrock(self, conversation):
#         """
#         Sends the current conversation, system prompt, and tool specifications to Bedrock
#         and returns the model's response.
#         """
#         print("\n[Calling Bedrock for response...]\n")
#         # Use the converse API for tool use functionality.
#         return self.bedrock_runtime_client.converse(
#             modelId=MODEL_ID,
#             messages=conversation,
#             system=self.system_prompt,
#             toolConfig=self.tool_config,
#         )

#     def _process_model_response(
#         self, model_response, conversation, max_recursion=MAX_RECURSIONS
#     ):
#         """
#         Processes the response from Bedrock. It handles text output, tool use requests,
#         and manages the conversation flow recursively until a final answer is achieved.
#         """
#         if max_recursion <= 0:
#             print("[Warning: Maximum recursion depth reached. Ending conversation.]")
#             return

#         # Append the model's message to the conversation history.
#         message = model_response["output"]["message"]
#         conversation.append(message)

#         # Check the stop reason to determine the next action.
#         if model_response["stopReason"] == "tool_use":
#             # If the model wants to use a tool, hand it over to the tool handler.
#             self._handle_tool_use(message, conversation, max_recursion)

#         elif model_response["stopReason"] == "end_turn":
#             # If the model has finished its turn, print its final text response.
#             for content_block in message["content"]:
#                 if "text" in content_block:
#                     print(f"\n[AI]: {content_block['text']}")
#             return # End of this processing path.

#         else:
#             # Handle other stop reasons or unexpected scenarios.
#             print(f"[AI]: Model stopped with reason: {model_response['stopReason']}")
#             for content_block in message["content"]:
#                 if "text" in content_block:
#                     print(f"[AI]: {content_block['text']}")
#             return

#     def _handle_tool_use(
#         self, model_message, conversation, max_recursion=MAX_RECURSIONS
#     ):
#         """
#         Executes the tool calls requested by the model and sends the results back to Bedrock.
#         """
#         tool_results = [] # List to store results from all tool calls.

#         # A model response might contain multiple tool use requests. Process them all.
#         for content_block in model_message["content"]:
#             if "text" in content_block:
#                 # If there's explanatory text from the model, print it.
#                 print(f"\n[AI (Thinking)]: {content_block['text']}")

#             if "toolUse" in content_block:
#                 # Extract tool details from the model's request.
#                 tool_use = content_block["toolUse"]
#                 tool_name = tool_use["name"]
#                 tool_input = tool_use["input"]
#                 tool_use_id = tool_use["toolUseId"]

#                 print(f"\n[Tool Call]: Calling {tool_name} with input: {tool_input}")

#                 # Invoke the specific tool.
#                 tool_output = self._invoke_tool(tool_name, tool_input)

#                 print(f"[Tool Output]: {tool_name} returned: {tool_output}")

#                 # Format the tool result to be sent back to Bedrock.
#                 tool_results.append(
#                     {
#                         "toolResult": {
#                             "toolUseId": tool_use_id,
#                             "content": [{"json": tool_output}], # Tool results are sent as JSON.
#                         }
#                     }
#                 )

#         # Create a new user message containing the tool results.
#         # This message tells the model what happened when its tools were called.
#         message_with_tool_results = {"role": "user", "content": tool_results}
#         conversation.append(message_with_tool_results)

#         # Send the conversation (now including tool results) back to Bedrock
#         # for the model to continue its reasoning or generate a final response.
#         response = self._send_conversation_to_bedrock(conversation)

#         # Continue processing the model's new response.
#         self._process_model_response(response, conversation, max_recursion - 1)


#     def _invoke_tool(self, tool_name: str, input_data: dict) -> dict:
#         """
#         Dispatches the tool call to the appropriate function or external API.
#         This method acts as a router for all defined tools.
#         """
#         try:
#             if tool_name == "get_weather_forecast":
#                 # For the weather tool, directly call the imported Python function.
#                 location = input_data.get("location")
#                 forecast_days = input_data.get("forecast_days", 1) # Default to 1 day
#                 if not location:
#                     return {"error": True, "message": "Location is required for weather forecast."}
#                 return get_weather_forecast(location, forecast_days)

#             elif tool_name == "search_flights":
#                 # For flights, make an HTTP GET request to the FastAPI service.
#                 params = {
#                     "origin_region": input_data.get("origin_region"),
#                     "destination_region": input_data.get("destination_region"),
#                     "date": input_data.get("date"),
#                 }
#                 response = requests.get(f"{FLIGHT_SERVICE_URL}/flights/search", params=params)
#                 response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
#                 return response.json()

#             elif tool_name == "search_trains":
#                 # For trains, make an HTTP GET request to the FastAPI service.
#                 params = {
#                     "origin_region": input_data.get("origin_region"),
#                     "destination_region": input_data.get("destination_region"),
#                     "date": input_data.get("date"),
#                 }
#                 response = requests.get(f"{TRAIN_SERVICE_URL}/trains/search", params=params)
#                 response.raise_for_status()
#                 return response.json()

#             elif tool_name == "search_hotels": # Corrected name from "Google Hotels"
#                 # For hotels, make an HTTP GET request to the FastAPI service.
#                 params = {
#                     "region": input_data.get("region"),
#                     "check_in_date": input_data.get("check_in_date"),
#                     "check_out_date": input_data.get("check_out_date"),
#                 }
#                 response = requests.get(f"{HOTEL_SERVICE_URL}/hotels/search", params=params)
#                 response.raise_for_status()
#                 return response.json()

#             else:
#                 # If an unrecognized tool name is provided by the model.
#                 return {"error": True, "message": f"Unknown tool: {tool_name}"}

#         except requests.exceptions.RequestException as e:
#             # Catch network or HTTP errors from FastAPI calls.
#             return {"error": True, "message": f"API call failed for {tool_name}: {str(e)}"}
#         except Exception as e:
#             # Catch any other unexpected errors during tool invocation.
#             return {"error": True, "message": f"Error invoking tool {tool_name}: {str(e)}"}

#     def _get_tool_specs(self) -> list:
#         """
#         Defines the OpenAPI specifications for all tools, enabling Bedrock to understand
#         how to call them and what parameters they require.
#         """
#         # --- Weather Tool Specification ---
#         # This tool is a direct Python function call. Its spec defines how Claude should use it.
#         weather_tool_spec = {
#             "name": "get_weather_forecast",
#             "description": "Get the current weather forecast for a specific location for up to 16 days.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "location": {
#                             "type": "string",
#                             "description": "The city or location name (e.g., 'London', 'Chennai')."
#                         },
#                         "forecast_days": {
#                             "type": "integer",
#                             "description": "Number of days for the forecast (1-16). Defaults to 1.",
#                             "default": 1
#                         }
#                     },
#                     "required": ["location"]
#                 }
#             }
#         }

#         # --- Flight Search Tool Specification ---
#         # This tool makes an HTTP GET request to our FastAPI service.
#         flight_tool_spec = {
#             "name": "search_flights",
#             "description": "Search for available flights between broad geographical regions on a specific date.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "origin_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of departure (e.g., 'North India', 'South India')."
#                         },
#                         "destination_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of arrival (e.g., 'North India', 'South India')."
#                         },
#                         "date": {
#                             "type": "string",
#                             "description": "The desired travel date in (%Y-%m-%d) format (e.g., '2025-06-28')."
#                         }
#                     },
#                     "required": ["origin_region", "destination_region", "date"]
#                 }
#             }
#         }

#         # --- Train Search Tool Specification ---
#         # This tool makes an HTTP GET request to our FastAPI service.
#         train_tool_spec = {
#             "name": "search_trains",
#             "description": "Search for available trains between broad geographical regions on a specific date.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "origin_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of departure (e.g., 'North India', 'South India')."
#                         },
#                         "destination_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of arrival (e.g., 'North India', 'South India')."
#                         },
#                         "date": {
#                             "type": "string",
#                             "description": "The desired travel date in (%Y-%m-%d) format (e.g., '2025-06-28')."
#                         }
#                     },
#                     "required": ["origin_region", "destination_region", "date"]
#                 }
#             }
#         }

#         # --- Hotel Search Tool Specification ---
#         # This tool makes an HTTP GET request to our FastAPI service.
#         hotel_tool_spec = {
#             "name": "search_hotels",
#             "description": "Search for available hotels in a specific broad geographical region for given check-in and check-out dates.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "region": {
#                             "type": "string",
#                             "description": "The broad geographical region where the user wants to find hotels (e.g., 'South India', 'North India')."
#                         },
#                         "check_in_date": {
#                             "type": "string",
#                             "description": "The desired check-in date in (%Y-%m-%d) format (e.g., '2025-08-01')."
#                         },
#                         "check_out_date": {
#                             "type": "string",
#                             "description": "The desired check-out date in (%Y-%m-%d) format (e.g., '2025-08-05')."
#                         }
#                     },
#                     "required": ["region", "check_in_date", "check_out_date"]
#                 }
#             }
#         }

#         # Each tool specification must be wrapped in a 'toolSpec' key as required by Bedrock API.
#         return [
#             {"toolSpec": weather_tool_spec},
#             {"toolSpec": flight_tool_spec},
#             {"toolSpec": train_tool_spec},
#             {"toolSpec": hotel_tool_spec}
#         ]

#     @staticmethod
#     def _get_user_input(prompt_text="Enter your request"):
#         """
#         Prompts the user for input and handles the 'x' command to exit.
#         """
#         print("\n" + "-"*50) # Separator for clarity
#         user_input = input(f"{prompt_text} (type 'x' to exit): ")
#         if user_input.lower() == 'x':
#             return None
#         return user_input.strip()

# if __name__ == "__main__":
#     # --- IMPORTANT: Before running this script ---
#     # 1. Ensure you have AWS credentials configured (e.g., via AWS CLI 'aws configure').
#     # 2. Ensure your Bedrock API access is enabled for the chosen MODEL_ID in AWS_REGION.
#     # 3. Ensure your weather.py file exists and contains the get_weather_forecast function.
#     # 4. Ensure your prompt.py file exists with the SYSTEM_PROMPT.
#     # 5. Make sure your FastAPI services (flight_service.py, train_service.py, hotel_service.py)
#     #    are running in separate terminals on their respective ports (8001, 8002, 8003).

#     # Example of how to run the FastAPI services:
#     # Terminal 1: uvicorn flight_service:app --reload --port 8001
#     # Terminal 2: uvicorn train_service:app --reload --port 8002
#     # Terminal 3: uvicorn hotel_service:app --reload --port 8003
#     # Terminal 4: python claude_agent.py (Run this main agent script)

#     # Instantiate and run the Claude agent.
#     agent = ClaudeAgent()
#     agent.run()






# claude_agent.py

# This script integrates Amazon Bedrock's Claude model with several custom tools:
# Weather (local function call), Flight, Train, and Hotel (FastAPI services).
# It orchestrates the conversation flow based on a detailed system prompt.


# claude_agent.py

# This script integrates Amazon Bedrock's Claude model with several custom tools:
# Weather (local function call), Flight, Train, and Hotel (FastAPI services).
# It orchestrates the conversation flow based on a detailed system prompt.

# import boto3
# import requests
# import json
# from datetime import date, timedelta # Imported for dynamic date calculation

# import sys
# import os

# current_script_dir = os.path.dirname(os.path.abspath(__file__))

# package_root = os.path.abspath(os.path.join(current_script_dir, '..'))

# if package_root not in sys.path:
#     sys.path.insert(0, package_root)


# # Import the system prompt from the separate prompt.py file.
# from prompt import SYSTEM_PROMPT

# # Import the local weather function.
# # Ensure your weather.py file contains the get_weather_forecast function as previously defined.
# from  Tools.weather   import get_weather_forecast

# # --- Configuration Constants ---
# # AWS Region where your Bedrock model is available.
# AWS_REGION = "us-east-1" # Or your preferred AWS region, e.g., "us-west-2"

# # Model ID for Claude. Adjust as needed based on availability and preference.
# # For a full list of supported models, refer to AWS Bedrock documentation.
# MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0" # A good balance of capability and cost

# # Base URLs for our locally running FastAPI services.
# # Ensure these services are running on their respective ports before running this agent.
# FLIGHT_SERVICE_URL = "http://127.0.0.1:8001"
# TRAIN_SERVICE_URL = "http://127.0.0.1:8002"
# HOTEL_SERVICE_URL = "http://127.0.0.1:8003"

# # The maximum number of recursive calls allowed in the tool_use_demo function.
# # This helps prevent infinite loops during complex tool interactions.
# MAX_RECURSIONS = 5

# class ClaudeAgent:
#     """
#     Manages the conversation with Claude on Amazon Bedrock, integrating various tools
#     for travel planning.
#     """

#     def __init__(self):
#         """
#         Initializes the Bedrock Runtime client and sets up the tool configurations.
#         """
#         # The system prompt is loaded directly from prompt.py.
#         # It's already a string, so we wrap it in a list with a "text" content block.
#         self.system_prompt = [{"text": SYSTEM_PROMPT}] # Ensure this exact format

#         # Prepare the tool configuration by getting specifications for all tools.
#         self.tool_config = {"tools": self._get_tool_specs()}

#         # Create a Bedrock Runtime client in the specified AWS Region.
#         self.bedrock_runtime_client = boto3.client(
#             "bedrock-runtime", region_name=AWS_REGION
#         )

#     def run(self):
#         """
#         Starts the conversation with the user and handles the interaction with Bedrock.
#         Pre-processes user input to resolve relative dates.
#         """
#         print("\n--- Claude AI Travel Planner ---")
#         print("Hello! I'm your AI Travel Planner. How can I assist you today?")
#         print("Type 'x' to exit at any time.")

#         conversation = [] # Stores the history of messages for the conversation.

#         user_input = self._get_user_input("Your travel request")

#         while user_input is not None:
#             # Resolve any relative dates in the user's input before sending to Bedrock.
#             # The LLM will receive the absolute date in Walpole-MM-DD format.
#             processed_user_input, _ = self._resolve_relative_date(user_input)

#             # Create a new user message with the processed input and append it to the conversation history.
#             message = {"role": "user", "content": [{"text": processed_user_input}]}
#             conversation.append(message)

#             # Send the entire conversation history to Amazon Bedrock.
#             bedrock_response = self._send_conversation_to_bedrock(conversation)

#             # Recursively process the model's response until it reaches an 'end_turn'
#             # or the recursion limit is hit.
#             self._process_model_response(
#                 bedrock_response, conversation, max_recursion=MAX_RECURSIONS
#             )

#             # Prompt for next user input to continue the conversation.
#             user_input = self._get_user_input("Your next request")

#         print("\n--- Thank you for using the Claude AI Travel Planner! ---")

#     def _send_conversation_to_bedrock(self, conversation):
#         """
#         Sends the current conversation, system prompt, and tool specifications to Bedrock
#         and returns the model's response.
#         """
#         print("\n[Calling Bedrock for response...]\n")
#         # Ensure system prompt is passed as a list of content blocks, as expected by converse API.
#         return self.bedrock_runtime_client.converse(
#             modelId=MODEL_ID,
#             messages=conversation,
#             system=self.system_prompt, # Already correctly formatted as [{"text": SYSTEM_PROMPT}]
#             toolConfig=self.tool_config,
#         )

#     def _process_model_response(
#         self, model_response, conversation, max_recursion=MAX_RECURSIONS
#     ):
#         """
#         Processes the response from Bedrock. It handles text output, tool use requests,
#         and manages the conversation flow recursively until a final answer is achieved.
#         """
#         if max_recursion <= 0:
#             print("[Warning: Maximum recursion depth reached. Ending conversation.]")
#             return

#         # Append the model's message to the conversation history.
#         message = model_response["output"]["message"]
#         conversation.append(message)

#         # Check the stop reason to determine the next action.
#         if model_response["stopReason"] == "tool_use":
#             # If the model wants to use a tool, hand it over to the tool handler.
#             self._handle_tool_use(message, conversation, max_recursion)

#         elif model_response["stopReason"] == "end_turn":
#             # If the model has finished its turn, print its final text response.
#             for content_block in message["content"]:
#                 if "text" in content_block:
#                     print(f"\n[AI]: {content_block['text']}")
#             return # End of this processing path.

#         else:
#             # Handle other stop reasons or unexpected scenarios.
#             print(f"[AI]: Model stopped with reason: {model_response['stopReason']}")
#             for content_block in message["content"]:
#                 if "text" in content_block:
#                     print(f"[AI]: {content_block['text']}")
#             return

#     def _handle_tool_use(
#         self, model_message, conversation, max_recursion=MAX_RECURSIONS
#     ):
#         """
#         Executes the tool calls requested by the model and sends the results back to Bedrock.
#         """
#         tool_results = [] # List to store results from all tool calls.

#         # A model response might contain multiple tool use requests. Process them all.
#         for content_block in model_message["content"]:
#             if "text" in content_block:
#                 # If there's explanatory text from the model, print it.
#                 print(f"\n[AI (Thinking)]: {content_block['text']}")

#             if "toolUse" in content_block:
#                 # Extract tool details from the model's request.
#                 tool_use = content_block["toolUse"]
#                 tool_name = tool_use["name"]
#                 tool_input = tool_use["input"]
#                 tool_use_id = tool_use["toolUseId"]

#                 print(f"\n[Tool Call]: Calling {tool_name} with input: {tool_input}")

#                 # Invoke the specific tool.
#                 tool_output = self._invoke_tool(tool_name, tool_input)

#                 print(f"[Tool Output]: {tool_name} returned: {tool_output}")

#                 # Format the tool result to be sent back to Bedrock.
#                 tool_results.append(
#                     {
#                         "toolResult": {
#                             "toolUseId": tool_use_id,
#                             "content": [{"json": tool_output}], # Tool results are sent as JSON.
#                         }
#                     }
#                 )

#         # Create a new user message containing the tool results.
#         # This message tells the model what happened when its tools were called.
#         message_with_tool_results = {"role": "user", "content": tool_results}
#         conversation.append(message_with_tool_results)

#         # Send the conversation (now including tool results) back to Bedrock
#         # for the model to continue its reasoning or generate a final response.
#         response = self._send_conversation_to_bedrock(conversation)

#         # Continue processing the model's new response.
#         self._process_model_response(response, conversation, max_recursion - 1)


#     def _invoke_tool(self, tool_name: str, input_data: dict) -> dict:
#         """
#         Dispatches the tool call to the appropriate function or external API.
#         This method acts as a router for all defined tools.
#         """
#         try:
#             if tool_name == "get_weather_forecast":
#                 # For the weather tool, directly call the imported Python function.
#                 location = input_data.get("location")
#                 forecast_days = input_data.get("forecast_days", 1) # Default to 1 day
#                 if not location:
#                     return {"error": True, "message": "Location is required for weather forecast."}
#                 return get_weather_forecast(location, forecast_days)

#             elif tool_name == "search_flights":
#                 # For flights, make an HTTP GET request to the FastAPI service.
#                 params = {
#                     "origin_region": input_data.get("origin_region"),
#                     "destination_region": input_data.get("destination_region"),
#                     "date": input_data.get("date"),
#                 }
#                 response = requests.get(f"{FLIGHT_SERVICE_URL}/flights/search", params=params)
#                 response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
#                 return response.json()

#             elif tool_name == "search_trains":
#                 # For trains, make an HTTP GET request to the FastAPI service.
#                 params = {
#                     "origin_region": input_data.get("origin_region"),
#                     "destination_region": input_data.get("destination_region"),
#                     "date": input_data.get("date"),
#                 }
#                 response = requests.get(f"{TRAIN_SERVICE_URL}/trains/search", params=params)
#                 response.raise_for_status()
#                 return response.json()

#             elif tool_name == "search_hotels":
#                 # For hotels, make an HTTP GET request to the FastAPI service.
#                 params = {
#                     "region": input_data.get("region"),
#                     "check_in_date": input_data.get("check_in_date"),
#                     "check_out_date": input_data.get("check_out_date"),
#                 }
#                 response = requests.get(f"{HOTEL_SERVICE_URL}/hotels/search", params=params)
#                 response.raise_for_status()
#                 return response.json()

#             else:
#                 # If an unrecognized tool name is provided by the model.
#                 return {"error": True, "message": f"Unknown tool: {tool_name}"}

#         except requests.exceptions.RequestException as e:
#             # Catch network or HTTP errors from FastAPI calls.
#             return {"error": True, "message": f"API call failed for {tool_name}: {str(e)}"}
#         except Exception as e:
#             # Catch any other unexpected errors during tool invocation.
#             return {"error": True, "message": f"Error invoking tool {tool_name}: {str(e)}"}

#     def _resolve_relative_date(self, text: str) -> tuple[str, str]:
#         """
#         Parses common relative date terms (e.g., "tomorrow", "coming Friday", "next Tuesday")
#         in the input text and converts them to a YYYY-MM-DD format.

#         Returns the updated text with the absolute date and the resolved date string
#         (or the original text and None if no relative date is found).
#         """
#         today = date.today()

#         lower_text = text.lower()

#         # Handle "tomorrow"
#         if "tomorrow" in lower_text:
#             resolved_date = today + timedelta(days=1)
#             resolved_date_str = resolved_date.isoformat()
#             text = text.replace("tomorrow", resolved_date_str, 1)
#             return text, resolved_date_str
        
#         # Handle "today"
#         if "today" in lower_text:
#             resolved_date = today
#             resolved_date_str = resolved_date.isoformat()
#             text = text.replace("today", resolved_date_str, 1)
#             return text, resolved_date_str


#         # Handle "coming [day of week]" or "next [day of week]"
#         days_of_week_map = {
#             "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
#             "friday": 4, "saturday": 5, "sunday": 6
#         }
        
#         # Prioritize "next [day]" over "coming [day]" or just "[day]"
#         # This order matters to replace "next Friday" before just "Friday" if that were a case
#         day_phrases = [(f"next {day_name}", 7) for day_name in days_of_week_map.keys()] + \
#                       [(f"coming {day_name}", 0) for day_name in days_of_week_map.keys()] + \
#                       [day_name for day_name in days_of_week_map.keys()] # Simple day name

#         for phrase_tuple in day_phrases:
#             if isinstance(phrase_tuple, tuple):
#                 phrase = phrase_tuple[0]
#                 week_offset = phrase_tuple[1] # 7 for "next", 0 for "coming"
#             else:
#                 phrase = phrase_tuple
#                 week_offset = 0 # Default to current week for simple day name (unless it's today)

#             if phrase in lower_text:
#                 day_name_extracted = phrase.split()[-1] # e.g., "monday" from "next monday"
#                 day_index = days_of_week_map[day_name_extracted]
                
#                 today_weekday = today.weekday() # Monday is 0, Sunday is 6
                
#                 # Calculate days until the next occurrence of that weekday
#                 days_ahead = (day_index - today_weekday + 7) % 7 

#                 # Special handling for "next [day]" vs. "coming [day]" or just "[day]"
#                 if week_offset == 7: # If "next [day]" was explicitly used
#                     if days_ahead == 0: # If today is that day, "next X" means 7 days from now
#                         days_ahead = 7
#                     # Otherwise, days_ahead is already correct for next week's occurrence
#                 elif days_ahead == 0 and phrase_tuple == today.strftime("%A").lower():
#                     # If "today" is "Wednesday" and user says "Wednesday", it means today.
#                     days_ahead = 0
#                 elif days_ahead == 0: # If calculated days_ahead is 0 but it's not today (means it's a day in the past week), then it must be next week
#                      days_ahead = 7
                
#                 resolved_date = today + timedelta(days=days_ahead)
#                 resolved_date_str = resolved_date.isoformat()
                
#                 # Replace only the first occurrence to avoid issues with multiple same day names
#                 text = text.replace(phrase, resolved_date_str, 1)
#                 return text, resolved_date_str

#         return text, None # Return None as resolved_date_str if no match


#     def _get_tool_specs(self) -> list:
#         """
#         Defines the OpenAPI specifications for all tools, enabling Bedrock to understand
#         how to call them and what parameters they require.
#         """
#         # --- Weather Tool Specification ---
#         # This tool is a direct Python function call. Its spec defines how Claude should use it.
#         weather_tool_spec = {
#             "name": "get_weather_forecast",
#             "description": "Get the current weather forecast for a specific location for up to 16 days.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "location": {
#                             "type": "string",
#                             "description": "The city or location name (e.g., 'London', 'Chennai')."
#                         },
#                         "forecast_days": {
#                             "type": "integer",
#                             "description": "Number of days for the forecast (1-16). Defaults to 1.",
#                             "default": 1
#                         }
#                     },
#                     "required": ["location"]
#                 }
#             }
#         }

#         # --- Flight Search Tool Specification ---
#         # This tool makes an HTTP GET request to our FastAPI service.
#         flight_tool_spec = {
#             "name": "search_flights",
#             "description": "Search for available flights between broad geographical regions on a specific date.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "origin_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of departure (e.g., 'North India', 'South India')."
#                         },
#                         "destination_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of arrival (e.g., 'North India', 'South India')."
#                         },
#                         "date": {
#                             "type": "string",
#                             "description": "The desired travel date in YYYY-MM-DD format (e.g., '2025-06-28')."
#                         }
#                     },
#                     "required": ["origin_region", "destination_region", "date"]
#                 }
#             }
#         }

#         # --- Train Search Tool Specification ---
#         # This tool makes an HTTP GET request to our FastAPI service.
#         train_tool_spec = {
#             "name": "search_trains",
#             "description": "Search for available trains between broad geographical regions on a specific date.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "origin_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of departure (e.g., 'North India', 'South India')."
#                         },
#                         "destination_region": {
#                             "type": "string",
#                             "description": "The broad geographical region of arrival (e.g., 'North India', 'South India')."
#                         },
#                         "date": {
#                             "type": "string",
#                             "description": "The desired travel date in YYYY-MM-DD format (e.g., '2025-06-28')."
#                         }
#                     },
#                     "required": ["origin_region", "destination_region", "date"]
#                 }
#             }
#         }

#         # --- Hotel Search Tool Specification ---
#         # This tool makes an HTTP GET request to our FastAPI service.
#         hotel_tool_spec = {
#             "name": "search_hotels",
#             "description": "Search for available hotels in a specific broad geographical region for given check-in and check-out dates.",
#             "inputSchema": {
#                 "json": {
#                     "type": "object",
#                     "properties": {
#                         "region": {
#                             "type": "string",
#                             "description": "The broad geographical region where the user wants to find hotels (e.g., 'South India', 'North India')."
#                         },
#                         "check_in_date": {
#                             "type": "string",
#                             "description": "The desired check-in date in YYYY-MM-DD format (e.g., '2025-08-01')."
#                         },
#                         "check_out_date": {
#                             "type": "string",
#                             "description": "The desired check-out date in YYYY-MM-DD format (e.g., '2025-08-05')."
#                         }
#                     },
#                     "required": ["region", "check_in_date", "check_out_date"]
#                 }
#             }
#         }

#         # Each tool specification must be wrapped in a 'toolSpec' key as required by Bedrock API.
#         return [
#             {"toolSpec": weather_tool_spec},
#             {"toolSpec": flight_tool_spec},
#             {"toolSpec": train_tool_spec},
#             {"toolSpec": hotel_tool_spec}
#         ]

#     @staticmethod
#     def _get_user_input(prompt_text="Enter your request"):
#         """
#         Prompts the user for input and handles the 'x' command to exit.
#         """
#         print("\n" + "-"*50) # Separator for clarity
#         user_input = input(f"{prompt_text} (type 'x' to exit): ")
#         if user_input.lower() == 'x':
#             return None
#         return user_input.strip()

# if __name__ == "__main__":
#     # --- IMPORTANT: Before running this script ---
#     # 1. Ensure you have AWS credentials configured (e.g., via AWS CLI 'aws configure').
#     # 2. Ensure your Bedrock API access is enabled for the chosen MODEL_ID in AWS_REGION.
#     # 3. Ensure your weather.py file exists and contains the get_weather_forecast function.
#     # 4. Ensure your prompt.py file exists with the SYSTEM_PROMPT.
#     # 5. Make sure your FastAPI services (flight_service.py, train_service.py, hotel_service.py)
#     #    are running in separate terminals on their respective ports (8001, 8002, 8003).

#     # Example of how to run the FastAPI services:
#     # Terminal 1: uvicorn flight_service:app --reload --port 8001
#     # Terminal 2: uvicorn train_service:app --reload --port 8002
#     # Terminal 3: uvicorn hotel_service:app --reload --port 8003
#     # Terminal 4: python claude_agent.py (Run this main agent script)

#     # Instantiate and run the Claude agent.
#     agent = ClaudeAgent()
#     agent.run()






import boto3
import requests
import json
from datetime import date, timedelta # Used for dynamic date calculations

import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))

package_root = os.path.abspath(os.path.join(current_script_dir, '..'))

if package_root not in sys.path:
    sys.path.insert(0, package_root)



# Import the main system prompt for the AI's behavior.
from prompt import SYSTEM_PROMPT

# Import the function that fetches weather data.
from Tools.weather  import get_weather_forecast

# configuration for AWS and FastAPI Services 
AWS_REGION = "us-east-1" # AWS region where Bedrock service is accessed
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0" # The specific Claude model to use

# Base URLs for the FastAPI services. .
FLIGHT_SERVICE_URL = "http://127.0.0.1:8001"
TRAIN_SERVICE_URL = "http://127.0.0.1:8002"
HOTEL_SERVICE_URL = "http://127.0.0.1:8003"

# Limits recursive calls to prevent infinite loops in conversational turns
MAX_RECURSIONS = 5

class ClaudeAgent:
    """
    Manages the conversation flow with the user, interacts with Amazon Bedrock,
    and dispatches calls to various travel-related tools.
    """

    def __init__(self):
        """
        Initializes the Bedrock client and sets up the tool definitions for the LLM.
        """
        self.system_prompt = [{"text": SYSTEM_PROMPT}]
        self.tool_config = {"tools": self._get_tool_specs()}
        self.bedrock_runtime_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    def run(self):
        """
        Starts the conversational loop with the user. It takes user input,
        pre-processes it sends it to Bedrock,
        and then processes Bedrock's responses.
        """
        print("\n--- Claude AI Travel Planner ---")
        print("Hello! I'm your AI Travel Planner. How can I assist you today?")
        print("Type 'x' to exit at any time.")

        conversation = [] # Stores the ongoing chat history with the LLM.

        user_input = self._get_user_input("Your travel request")

        while user_input is not None:
            # Convert any relative dates in the user's query
            processed_user_input, _ = self._resolve_relative_date(user_input)

            # Add the user's processed message to the conversation history.
            message = {"role": "user", "content": [{"text": processed_user_input}]}
            conversation.append(message)

            # Send the complete conversation history to the Bedrock model.
            bedrock_response = self._send_conversation_to_bedrock(conversation)

            # Process the AI's response, which might involve tool calls.
            self._process_model_response(
                bedrock_response, conversation, max_recursion=MAX_RECURSIONS
            )

            # Prompt for the next user input to continue the conversation.
            user_input = self._get_user_input("Your next request")

        print("\n--- Thank you for using the Claude AI Travel Planner! ---")

    def _send_conversation_to_bedrock(self, conversation):
        """
        Communicates with the Bedrock API to get a response from the Claude model.
        """
        return self.bedrock_runtime_client.converse(
            modelId=MODEL_ID,
            messages=conversation,
            system=self.system_prompt,
            toolConfig=self.tool_config,
        )

    def _process_model_response(
        self, model_response, conversation, max_recursion=MAX_RECURSIONS
    ):
        """
        Analyzes the AI's response to decide the next action: print text,
        call tools, or continue the conversation.
        """
        if max_recursion <= 0:
            print("[Warning: Maximum recursion depth reached. Ending conversation.]")
            return

        # Add the AI's message to the conversation history.
        message = model_response["output"]["message"]
        conversation.append(message)

        if model_response["stopReason"] == "tool_use":
            # If the AI requests to use a tool, handle that request.
            self._handle_tool_use(message, conversation, max_recursion)

        elif model_response["stopReason"] == "end_turn":
            # If the AI has finished its turn, display its text response to the user.
            for content_block in message["content"]:
                if "text" in content_block:
                    print(f"\n[AI]: {content_block['text']}")
            return

        else:
            # Handle any unexpected ways the AI might stop.
            for content_block in message["content"]:
                if "text" in content_block:
                    print(f"[AI]: {content_block['text']}")
            return

    def _handle_tool_use(
        self, model_message, conversation, max_recursion=MAX_RECURSIONS
    ):
        """
        Executes the tools requested by the AI and sends the results back to Bedrock.
        """
        tool_results = [] # Collects outputs from all tool calls in this turn.

        # Iterate through all content blocks in the AI's message.
        for content_block in model_message["content"]:
            if "text" in content_block:
                # If the AI provides internal thinking text, display it.
                print(f"\n[AI (Thinking)]: {content_block['text']}")

            if "toolUse" in content_block:
                # Extract details for the tool call.
                tool_use = content_block["toolUse"]
                tool_name = tool_use["name"]
                tool_input = tool_use["input"]
                tool_use_id = tool_use["toolUseId"]

                # Indicate the tool being called and its input.
                print(f"\n[Tool Call]: Calling {tool_name} with input: {tool_input}")

                # Execute the tool and get its output.
                tool_output = self._invoke_tool(tool_name, tool_input)

                # Display the tool's response.
                print(f"[Tool Output]: {tool_name} returned: {tool_output}")

                # Format the tool result to be sent back to Bedrock.
                tool_results.append(
                    {
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"json": tool_output}],
                        }
                    }
                )

        # Create a new user message containing all tool results and add to conversation.
        # This tells the AI the outcome of its tool requests.
        message_with_tool_results = {"role": "user", "content": tool_results}
        conversation.append(message_with_tool_results)

        # Sending the updated conversation back to Bedrock for the AI to continue its reasoning.
        response = self._send_conversation_to_bedrock(conversation)

        # Recursively process the AI's new response.
        self._process_model_response(response, conversation, max_recursion - 1)

    def _invoke_tool(self, tool_name: str, input_data: dict) -> dict:
        """
        Routes the tool call to the appropriate function or external API.
        Handles errors during tool execution.
        """
        try:
            if tool_name == "get_weather_forecast":
                # calls function for weather.
                location = input_data.get("location")
                forecast_days = input_data.get("forecast_days", 1)
                if not location:
                    return {"error": True, "message": "Location is required for weather forecast."}
                return get_weather_forecast(location, forecast_days)

            elif tool_name == "search_flights":
                # Calls the Flight FastAPI service.
                params = {
                    "origin_region": input_data.get("origin_region"),
                    "destination_region": input_data.get("destination_region"),
                    "date": input_data.get("date"),
                }
                response = requests.get(f"{FLIGHT_SERVICE_URL}/flights/search", params=params)
                response.raise_for_status() # Check for HTTP errors
                return response.json()

            elif tool_name == "search_trains":
                # Calls the Train FastAPI service.
                params = {
                    "origin_region": input_data.get("origin_region"),
                    "destination_region": input_data.get("destination_region"),
                    "date": input_data.get("date"),
                }
                response = requests.get(f"{TRAIN_SERVICE_URL}/trains/search", params=params)
                response.raise_for_status()
                return response.json()

            elif tool_name == "search_hotels":
                # Calls the Hotel FastAPI service.
                params = {
                    "region": input_data.get("region"),
                    "check_in_date": input_data.get("check_in_date"),
                    "check_out_date": input_data.get("check_out_date"),
                }
                response = requests.get(f"{HOTEL_SERVICE_URL}/hotels/search", params=params)
                response.raise_for_status()
                return response.json()

            else:
                # Handles cases where the AI requests an unknown tool.
                return {"error": True, "message": f"Unknown tool: {tool_name}"}

        except requests.exceptions.RequestException as e:
            # Catches network or HTTP-related errors from API calls.
            return {"error": True, "message": f"API call failed for {tool_name}: {str(e)}"}
        except Exception as e:
            # Catches any other unexpected errors during tool execution.
            return {"error": True, "message": f"Error invoking tool {tool_name}: {str(e)}"}

    def _resolve_relative_date(self, text: str) -> tuple[str, str]:
        """
        Converts common relative date terms (e.g., "tomorrow", "next Friday")
        in a given text to absolute YYYY-MM-DD dates.

        Returns the modified text and the first resolved date string found,
        or the original text and None if no relative date is found.
        """
        today = date.today()
        lower_text = text.lower()

        # Handle "tomorrow"
        if "tomorrow" in lower_text:
            resolved_date = today + timedelta(days=1)
            resolved_date_str = resolved_date.isoformat()
            text = text.replace("tomorrow", resolved_date_str, 1)
            return text, resolved_date_str
        
        # Handle "today"
        if "today" in lower_text:
            resolved_date = today
            resolved_date_str = resolved_date.isoformat()
            text = text.replace("today", resolved_date_str, 1)
            return text, resolved_date_str

        # Define mapping for days of the week.
        days_of_week_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        # Define common phrases for relative days, prioritized for accuracy.
        day_phrases = [(f"next {day_name}", 7) for day_name in days_of_week_map.keys()] + \
                      [(f"coming {day_name}", 0) for day_name in days_of_week_map.keys()] + \
                      [day_name for day_name in days_of_week_map.keys()] # Handles "Friday"

        for phrase_tuple in day_phrases:
            if isinstance(phrase_tuple, tuple):
                phrase = phrase_tuple[0]
                week_offset = phrase_tuple[1] # 7 for "next", 0 for "coming" or current week
            else:
                phrase = phrase_tuple
                week_offset = 0 # Default for simple day name (e.g., "Wednesday")

            if phrase in lower_text:
                day_name_extracted = phrase.split()[-1]
                day_index = days_of_week_map[day_name_extracted]
                
                today_weekday = today.weekday() # 0 = Monday, ..., 6 = Sunday
                
                # Calculate days until the next occurrence of the target weekday.
                days_ahead = (day_index - today_weekday + 7) % 7 

                # Adjust for "next" keyword or if the calculated day is today/in the past week.
                if week_offset == 7: # If "next [day]" was explicitly used
                    if days_ahead == 0: # If today is that day, "next X" means 7 days from now.
                        days_ahead = 7
                elif days_ahead == 0 and phrase_tuple == today.strftime("%A").lower():
                    # If today is "Wednesday" and user says "Wednesday", it means today.
                    days_ahead = 0
                elif days_ahead == 0: # If it's a day in the past week, assume user means next occurrence.
                     days_ahead = 7
                
                resolved_date = today + timedelta(days=days_ahead)
                resolved_date_str = resolved_date.isoformat()
                
                # Replace only the first occurrence of the phrase to avoid issues.
                text = text.replace(phrase, resolved_date_str, 1)
                return text, resolved_date_str

        return text, None # No relative date found in the text.


    def _get_tool_specs(self) -> list:
        """
        Provides the OpenAPI specifications for all tools. Bedrock uses these
        specifications to understand how to call the tools.
        """
        # Define spec for the Weather Tool (local function call).
        weather_tool_spec = {
            "name": "get_weather_forecast",
            "description": "Get the current weather forecast for a specific location for up to 16 days.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "forecast_days": {"type": "integer", "default": 1}
                    },
                    "required": ["location"]
                }
            }
        }

        # Define spec for the Flight Search Tool (FastAPI service).
        flight_tool_spec = {
            "name": "search_flights",
            "description": "Search for available flights between broad geographical regions on a specific date.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "origin_region": {"type": "string"},
                        "destination_region": {"type": "string"},
                        "date": {"type": "string"}
                    },
                    "required": ["origin_region", "destination_region", "date"]
                }
            }
        }

        # Define spec for the Train Search Tool (FastAPI service).
        train_tool_spec = {
            "name": "search_trains",
            "description": "Search for available trains between broad geographical regions on a specific date.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "origin_region": {"type": "string"},
                        "destination_region": {"type": "string"},
                        "date": {"type": "string"}
                    },
                    "required": ["origin_region", "destination_region", "date"]
                }
            }
        }

        # Define spec for the Hotel Search Tool (FastAPI service).
        hotel_tool_spec = {
            "name": "search_hotels",
            "description": "Search for available hotels in a specific broad geographical region for given check-in and check-out dates.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "region": {"type": "string"},
                        "check_in_date": {"type": "string"},
                        "check_out_date": {"type": "string"}
                    },
                    "required": ["region", "check_in_date", "check_out_date"]
                }
            }
        }

        # Return all tool specifications, each wrapped under a toolSpec' key
        return [
            {"toolSpec": weather_tool_spec},
            {"toolSpec": flight_tool_spec},
            {"toolSpec": train_tool_spec},
            {"toolSpec": hotel_tool_spec}
        ]

    @staticmethod
    def _get_user_input(prompt_text="Enter your request"):
        """
        Prompts the user for input in the console. Handles 'x' command to exit.
        """
        print("\n" + "-"*50) # Visual separator
        user_input = input(f"{prompt_text} (type 'x' to exit): ")
        if user_input.lower() == 'x':
            return None
        return user_input.strip()

if __name__ == "__main__":
    agent = ClaudeAgent()
    agent.run()
