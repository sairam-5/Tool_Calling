import streamlit as st
import json
import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))
package_root = os.path.abspath(os.path.join(current_script_dir, '..'))
if package_root not in sys.path:
    sys.path.insert(0, package_root)

from main import ClaudeAgent, FLIGHT_SERVICE_URL, TRAIN_SERVICE_URL, HOTEL_SERVICE_URL, MAX_RECURSIONS
from prompt import SYSTEM_PROMPT

st.set_page_config(page_title="AI Travel Planner", layout="centered")
st.title("AI Travel Planner")

# Initialize AI agent and conversation history, persisting across app reruns.
if 'agent' not in st.session_state:
    st.session_state.agent = ClaudeAgent()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'bedrock_conversation' not in st.session_state:
    st.session_state.bedrock_conversation = []

# Render past messages in the chat interface.
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "ai_text":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# Get user input from the chat box.
user_query = st.chat_input("How can I assist you with your travel plans today?")

if user_query:
    # Add user query to display history.
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # Resolve relative dates in the user's query.
    processed_user_input, _ = st.session_state.agent._resolve_relative_date(user_query)
    
    # Add processed user input to the Bedrock conversation history.
    st.session_state.bedrock_conversation.append({"role": "user", "content": [{"text": processed_user_input}]})

    with st.spinner("AI is planning your trip..."):
        current_recursion_depth = MAX_RECURSIONS
        response_finalized = False

        # Manages multi-turn AI reasoning and tool interactions.
        while current_recursion_depth > 0 and not response_finalized:
            try:
                # Send conversation to Bedrock and get AI's response.
                model_response = st.session_state.agent._send_conversation_to_bedrock(st.session_state.bedrock_conversation)
                
                message_from_bedrock = model_response["output"]["message"]
                stop_reason = model_response["stopReason"]
                
                # Append AI's raw message to conversation history for context.
                st.session_state.bedrock_conversation.append(message_from_bedrock)

                if stop_reason == "tool_use":
                    tool_results_for_bedrock = []

                    # Process tool calls requested by the AI.
                    for content_block in message_from_bedrock["content"]:
                        if "toolUse" in content_block:
                            tool_use = content_block["toolUse"]
                            tool_name = tool_use["name"]
                            tool_input = tool_use["input"]
                            tool_use_id = tool_use["toolUseId"]

                            tool_output = st.session_state.agent._invoke_tool(tool_name, tool_input)

                            # Format tool result for Bedrock.
                            tool_results_for_bedrock.append(
                                {
                                    "toolResult": {
                                        "toolUseId": tool_use_id,
                                        "content": [{"json": tool_output}],
                                    }
                                }
                            )
                    
                    # Add tool results to conversation for AI's next turn.
                    st.session_state.bedrock_conversation.append({"role": "user", "content": tool_results_for_bedrock})

                elif stop_reason == "end_turn":
                    # Display AI's final text response.
                    for content_block in message_from_bedrock["content"]:
                        if "text" in content_block:
                            st.session_state.messages.append({"role": "ai_text", "content": content_block["text"]})
                            with st.chat_message("assistant"):
                                st.write(content_block["text"])
                    response_finalized = True

                else:
                    # Handle unexpected AI stop reasons.
                    error_message = f"AI stopped with unexpected reason: {stop_reason}."
                    for content_block in message_from_bedrock["content"]:
                        if "text" in content_block:
                            error_message += f" AI response: {content_block['text']}"
                    st.session_state.messages.append({"role": "ai_text", "content": error_message})
                    with st.chat_message("assistant"):
                        st.error(error_message)
                    response_finalized = True

            except Exception as e:
                error_message = f"An error occurred during AI processing: {e}"
                st.session_state.messages.append({"role": "ai_text", "content": error_message})
                with st.chat_message("assistant"):
                    st.error(error_message)
                response_finalized = True

            current_recursion_depth -= 1

        # Fallback message if AI doesn't finalize response.
        if not response_finalized:
            st.session_state.messages.append({"role": "ai_text", "content": "Maximum processing depth reached without a final AI response. Please try rephrasing your request."})
            with st.chat_message("assistant"):
                st.warning("Maximum processing depth reached without a final AI response. Please try rephrasing your request.")

    st.rerun()
