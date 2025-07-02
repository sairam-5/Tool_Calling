import boto3
import requests
import json
from datetime import date, timedelta # Used for dynamic date calculations
from dotenv import load_dotenv
load_dotenv()
import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))

package_root = os.path.abspath(os.path.join(current_script_dir, '..'))

if package_root not in sys.path:
    sys.path.insert(0, package_root)

from prompt import SYSTEM_PROMPT

from Tools.weather import get_weather_forecast

AWS_REGION = "us-east-1" 
MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0" 

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
        self.bedrock_runtime_client = boto3.client("bedrock-runtime", region_name="us-east-1")

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
            print("[Warning: Maximum recursion depth reached. " \
            "Ending conversation.]")
            return

        # Add the AI's message to the conversation history.
        message = model_response["output"]["message"]
        conversation.append(message)

        if model_response["stopReason"] == "tool_use":
            self._handle_tool_use(message, conversation, max_recursion)

        elif model_response["stopReason"] == "end_turn":
            for content_block in message["content"]:
                if "text" in content_block:
                    print(f"\n[AI]: {content_block['text']}")
            return

        else:
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
        message_with_tool_results = {"role": "user", "content": tool_results}
        conversation.append(message_with_tool_results)

        # Sending the updated conversation back to Bedrock for the AI to continue its reasoning.
        response = self._send_conversation_to_bedrock(conversation)

        # Recursively process the AI's new response.
        self._process_model_response(response, conversation, max_recursion - 1)

    def _invoke_tool(self, tool_name: str, input_data: dict):
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
                week_offset = phrase_tuple[1] 
            else:
                phrase = phrase_tuple
                week_offset = 0 

            if phrase in lower_text:
                day_name_extracted = phrase.split()[-1]
                day_index = days_of_week_map[day_name_extracted]
                
                today_weekday = today.weekday() 
                
                # Calculate days until the next occurrence of the target weekday.
                days_ahead = (day_index - today_weekday + 7) % 7 

                # Adjust for "next" keyword or if the calculated day is today/in the past week.
                if week_offset == 7: 
                    if days_ahead == 0: 
                        days_ahead = 7
                elif days_ahead == 0 and phrase_tuple == today.strftime("%A").lower():
                    days_ahead = 0
                elif days_ahead == 0: 
                    days_ahead = 7
                
                resolved_date = today + timedelta(days=days_ahead)
                resolved_date_str = resolved_date.isoformat()
                
                # Replace only the first occurrence of the phrase to avoid issues.
                text = text.replace(phrase, resolved_date_str, 1)
                return text, resolved_date_str

        return text, None # No relative date found in the text.


    def _get_tool_specs(self):
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

        # Define spec for the Flight Search Tool (FastAPI ).
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

        # Define spec for the Train Search Tool (FastAPI ).
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

        # Define spec for the Hotel Search Tool (FastAPI ).
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

if __name__ == "__main__":
    agent = ClaudeAgent()
    agent.run()
