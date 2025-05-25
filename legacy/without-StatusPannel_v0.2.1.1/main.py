# Copyright (c) 2025 1f84@ELT Group
# Email: elt17604@outlook.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# Additional Terms:
# This software may not be used for commercial purposes.
# Any redistribution of this software must retain this notice.


import os
import json
from openai import OpenAI
import requests

DEEPSEEK_API_BASE_URL_V1 = "https://api.deepseek.com/v1"
DEEPSEEK_BALANCE_URL = "https://api.deepseek.com/user/balance"

def get_api_key():
    api_key = input("Enter your DeepSeek API Key: ").strip()
    while not api_key:
        print("API Key cannot be empty.")
        api_key = input("Enter your DeepSeek API Key: ").strip()
    return api_key

def initialize_client(api_key):
    try:
        return OpenAI(api_key=api_key, base_url=DEEPSEEK_API_BASE_URL_V1)
    except Exception as e:
        print(f"Client initialization failed: {e}")
        return None

def list_and_select_model(client):
    if not client:
        print("Client not initialized.")
        return None
    try:
        print("\nFetching available models...")
        models_response = client.models.list()
        available_models = [model.id for model in models_response.data if
                            "chat" in model.id.lower() or "coder" in model.id.lower() or len(models_response.data) < 10]
        if not available_models:
            available_models = [model.id for model in models_response.data]
        if not available_models:
            print("Failed to fetch model list. Check API key and connection.")
            manual_model = input("Enter model name (e.g., deepseek-chat): ")
            return manual_model if manual_model else None
        print("Available models:")
        for i, model_id in enumerate(available_models):
            print(f"{i + 1}. {model_id}")
        while True:
            try:
                choice_input = input(f"Select a model by number 1-{len(available_models)}: ")
                if not choice_input:
                    print("No model selected, using last selected or default.")
                    return None
                choice = int(choice_input)
                if 1 <= choice <= len(available_models):
                    selected_model = available_models[choice - 1]
                    print(f"Model selected: {selected_model}")
                    return selected_model
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a number.")
    except Exception as e:
        print(f"Failed to fetch model list: {e}")
        manual_model = input("Enter model name (leave blank to cancel): ")
        return manual_model if manual_model else None

def query_balance(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    try:
        print("\nQuerying account balance...")
        response = requests.get(DEEPSEEK_BALANCE_URL, headers=headers)
        response.raise_for_status()
        balance_data = response.json()
        print("Account Balance Information:")
        if balance_data.get("is_available", False):
            print("  Service Available: Yes")
            balance_infos_list = balance_data.get("balance_infos", [])
            if balance_infos_list:
                for idx, info in enumerate(balance_infos_list):
                    print(f"\n  Balance Info #{idx + 1}:")
                    print(f"    Currency: {info.get('currency', 'N/A')}")
                    print(f"    Total Balance: {info.get('total_balance', 'N/A')}")
                    print(f"    Granted Balance: {info.get('granted_balance', 'N/A')}")
                    print(f"    Topped-up Balance: {info.get('topped_up_balance', 'N/A')}")
            else:
                print("  Could not retrieve detailed balance entries.")
        else:
            print("  Service Available: No")
            if "message" in balance_data:
                print(f"  API Message: {balance_data['message']}")
            elif not balance_data.get("balance_infos") and not balance_data.get("is_available", True):
                print("  Possibly due to service unavailability or no balance info.")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while querying balance: {http_err}")
        if http_err.response is not None:
            print(f"Response status code: {http_err.response.status_code}")
            try:
                error_details = http_err.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"Response content: {http_err.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to query balance: {e}")
    except json.JSONDecodeError:
        error_response_text = "N/A"
        response = 'null'
        if 'response' in locals() and hasattr(response, 'text'):
            error_response_text = response.text
        print(f"Failed to parse balance response, not valid JSON:\n{error_response_text}")
    except Exception as e:
        print(f"Unknown error occurred while querying balance: {e}")

def stream_chat(client, model_id):
    if not client:
        print("Client not initialized.")
        return
    if not model_id or model_id == 'null':
        print("No model selected. Please choose a model first.")
        return
    print(f"\nStarting chat with model '{model_id}' (type '/exit' to end, '/new' for a new conversation)...")
    messages = []
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == '/exit':
                print("Ending conversation.")
                break
            if user_input.lower() == '/new':
                print("Starting new conversation...")
                messages = []
                continue
            messages.append({"role": "user", "content": user_input})
            print("Model: ", end="", flush=True)
            assistant_response_content = ""
            stream = client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                max_tokens=2048,
                temperature=1.1
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    content_piece = chunk.choices[0].delta.content
                    print(content_piece, end="", flush=True)
                    assistant_response_content += content_piece
            print()
            if assistant_response_content:
                messages.append({"role": "assistant", "content": assistant_response_content})
        except Exception as e:
            print(f"\nError during chat: {e}")
            if "Incorrect API key" in str(e) or "authentication" in str(e).lower():
                print("Please check if your API key is correct.")
            print("Try again or type '/exit' or '/new'.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("DeepSeek API client Version 0.2.1")
    api_key = get_api_key()
    if not api_key:
        print("No API key provided, exiting.")
        return
    client = initialize_client(api_key)
    if not client:
        return
    selected_model = None
    print(f"Default model set to: {selected_model}")
    while True:
        clear_screen()
        print("\nPlease select an option:")
        print("1. List and select model")
        print("2. Query account balance")
        print(f"3. Start chat (Current model: {selected_model})")
        print("4. Exit")
        choice = input("Enter your choice (1-4): ")
        if choice == '1':
            clear_screen()
            new_model = list_and_select_model(client)
            if new_model:
                selected_model = new_model
        elif choice == '2':
            clear_screen()
            query_balance(api_key)
            input("\nPress any key to return to the main menu...")
            clear_screen()
        elif choice == '3':
            if not selected_model:
                clear_screen()
                print("Please select a model first (option 1).")
                new_model = list_and_select_model(client)
                if new_model:
                    selected_model = new_model
                else:
                    print("Cannot start chat, no model selected.")
                    continue
            stream_chat(client, selected_model)
        elif choice == '4':
            break
        elif choice == '/clear':
            clear_screen()
        else:
            clear_screen()
            print("[error] Invalid option, please try again.")

if __name__ == "__main__":
    main()