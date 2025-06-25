import boto3
import requests
import json
from botocore.exceptions import ClientError
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv() 

import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))

package_root = os.path.abspath(os.path.join(current_script_dir, '..'))

if package_root not in sys.path:
    sys.path.insert(0, package_root)

from Tools.weather import get_weather_forecast
from prompt import SYSTEM_PROMPT



# AWS and Model Configuration
AWS_REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

FASTAPI_FLIGHT_API_URL = "http://127.0.0.1:8000" 

class MultiToolAssistant:
    """
    Manages the core logic for a multi-tool AI assistant.
    This class handles user input, communicates with the Bedrock LLM,
    invokes external tools (Flight and Weather), and manages the single-turn
    conversation flow. It pre-processes relative dates in user queries
    before sending them to the LLM.
    """
    def __init__(self):
        """
        Initializes the Bedrock client and defines the tool configurations
        for the LLM.
        """
        self.bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        self.tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "Weather_Tool",
                        "description": "Gets the current weather or a multi-day forecast for a specified location.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string", "description": "The name of the city or location."},
                                    "forecast_days": {"type": "integer", "description": "Number of days for the forecast (1-16). Defaults to 1.", "minimum": 1, "maximum": 16}
                                },
                                "required": ["location"],
                            }
                        },
                    }
                },
                {
                    "toolSpec": {
                        "name": "Flight_Availability_Tool",
                        "description": "Checks the mock availability of a flight between an origin and destination for a specific date (YYYY-MM-DD). This is a mock tool and does not provide real-time flight data.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "origin": {"type": "string", "description": "The departure city (e.g., Chennai, Bangalore)."},
                                    "destination": {"type": "string", "description": "The arrival city (e.g., New York, Delhi)."},
                                    "travel_date": {"type": "string", "description": "The date of travel in YYYY-MM-DD format (e.g., 2025-06-25)."}
                                },
                                "required": ["origin", "destination", "travel_date"],
                            }
                        },
                    }
                }
            ]
        }

    def _flight_availability_tool(self, origin: str, destination: str, travel_date: str):
        """
        Calls the local mock FastAPI service to check flight availability.
        Handles network errors and returns a structured response.
        """
        try:
            payload = {
                "origin": origin,
                "destination": destination,
                "travel_date": travel_date
            }
            headers = {"Content-Type": "application/json"}

            api_url = f"{FASTAPI_FLIGHT_API_URL}/flights/check_availability"
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status() # Raises an HTTPError for bad responses

            return response.json()

        except requests.exceptions.ConnectionError:
            return {"error": True, "message": f"Flight tool: Connection error. Ensure mock flight API is running at {FASTAPI_FLIGHT_API_URL}."}
        except requests.exceptions.RequestException as req_err:
            return {"error": True, "message": f"Flight tool: Request error: {str(req_err)}."}
        except Exception as e:
            return {"error": True, "message": f"Flight tool: Processing error: {str(e)}."}

    def _invoke_tool(self, tool_use_block: dict) -> dict:
        """
        Executes the specified tool function based on the LLM's request.
        This acts as a router for the tools defined in tool_config.
        """
        tool_name = tool_use_block["name"]
        input_data = tool_use_block["input"]
        tool_use_id = tool_use_block["toolUseId"]

        tool_output = {"error": True, "message": "Tool execution failed or tool not recognized."}

        # Indicate which tool is to be called 
        print(f"Invoking tool: {tool_name} with input: {input_data}")

        if tool_name == "Weather_Tool":
            location = input_data.get("location")
            forecast_days = input_data.get("forecast_days", 1)
            tool_output = get_weather_forecast(location, forecast_days)
        elif tool_name == "Flight_Availability_Tool":
            origin = input_data.get("origin")
            destination = input_data.get("destination")
            travel_date = input_data.get("travel_date")
            tool_output = self._flight_availability_tool(origin, destination, travel_date)
        
        return {"toolResult": {"toolUseId": tool_use_id, "content": [{"json": tool_output}]}}

    def _resolve_relative_date(self, text: str) -> tuple[str, str]:
        """
        Parses common relative date terms (e.g., "tomorrow", "coming Friday", "next Tuesday")
        in the input text and converts them to a YYYY-MM-DD format.
        
        Returns the updated text with the absolute date and the resolved date string
        (or the original text and None if no relative date is found).
        """
        today = date.today()
        
        lower_text = text.lower()

        # Handle "tomorrow"
        if "tomorrow" in lower_text:
            resolved_date = today + timedelta(days=1)
            resolved_date_str = resolved_date.isoformat()
            text = text.replace("tomorrow", resolved_date_str, 1) 
            return text, resolved_date_str
        
        # Handle "coming [day of week]" or "next [day of week]"
        days_of_week_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        for day_name, day_index in days_of_week_map.items():
            trigger_phrases = [f"coming {day_name}", f"next {day_name}"]
            for phrase in trigger_phrases:
                if phrase in lower_text:
                    today_weekday = today.weekday() # Monday is 0, Sunday is 6
                    target_weekday = day_index

                    days_ahead = target_weekday - today_weekday
                    if days_ahead <= 0: # If target day is today or in the past, get it for next week
                        days_ahead += 7
                    
                    resolved_date = today + timedelta(days=days_ahead)
                    resolved_date_str = resolved_date.isoformat()
                    
                    text = text.replace(phrase, resolved_date_str, 1) 
                    return text, resolved_date_str

        return text, None # Return None as resolved_date_str if no match

    def chat(self, user_input: str):
        """
        Manages a single turn of conversation with the AI assistant.
        This includes pre-processing user input, interacting with the Bedrock LLM,
        invoking necessary tools, and printing the final response.
        """
        # Resolve any relative dates in the user's input
        processed_input, _ = self._resolve_relative_date(user_input)
        
        # Prepare the initial user message block for the LLM
        user_message_block = {"role": "user", "content": [{"text": processed_input}]}
        
        try:
            # First call to Bedrock - Model either responds directly or requests tool use
            # Pass only the current user message
            response = self.bedrock_client.converse(
                modelId=MODEL_ID,
                messages=[user_message_block], # Only the user's current query
                system=[{"text": SYSTEM_PROMPT}],
                toolConfig=self.tool_config,
            )

            assistant_response_message = response["output"]["message"]

            # If the LLM requested tool(s), invoke them and send results back
            if response["stopReason"] == "tool_use":
                tool_results_to_llm = [] 
                for content_item in assistant_response_message["content"]:
                    if "toolUse" in content_item:
                        tool_result = self._invoke_tool(content_item["toolUse"])
                        tool_results_to_llm.append(tool_result) 

                tool_result_message_block = {"role": "user", "content": tool_results_to_llm}

                #  Make a second call to Bedrock for the final response.
                # This call includes the original user message, the assistant's tool-use request,
                # and the results from the tool execution.
                second_response = self.bedrock_client.converse(
                    modelId=MODEL_ID,
                    messages=[user_message_block, assistant_response_message, tool_result_message_block], 
                    system=[{"text": SYSTEM_PROMPT}],
                    toolConfig=self.tool_config,
                )
                
                final_assistant_message = second_response["output"]["message"]
                
                #  Print the final text response from the assistant
                for content_item in final_assistant_message["content"]:
                    if "text" in content_item:
                        print(f"Assistant: {content_item['text']}")
                        return 

            #  Handle direct text response (no tool use was needed)
            elif response["stopReason"] == "end_turn":
                for content_item in assistant_response_message["content"]:
                    if "text" in content_item:
                        print(f"Assistant: {content_item['text']}")
                        return 

            # Handle unexpected stop reasons
            else:
                print(f"Assistant: An unexpected response occurred. Reason: {response['stopReason']}. Please try again.")

        except ClientError as e:
            error_message = e.response.get("Error", {}).get("Message", "An unknown AWS service error occurred.")
            print(f"Assistant: Error during Bedrock interaction: {error_message}. Please check AWS configuration/permissions.")
        except Exception as e:
            print(f"Assistant: An unexpected internal error occurred: {str(e)}.")

# Main execution block for running the assistant 
if __name__ == "__main__":
    assistant = MultiToolAssistant()
    
    user_query = input("\nYou: ").strip()
    
    if user_query.lower() == "exit":
        print("--- Exiting Assistant. ---")
    elif not user_query:
        print("No input provided. Please enter your query.")
    else:
        assistant.chat(user_query)