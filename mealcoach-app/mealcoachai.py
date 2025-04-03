"""
This file contains the implementation of a meal planning assistant using OpenAI's API. 
The assistant interacts with users to understand their health objectives and dietary preferences, 
and generates meal recommendations based on the input. It also includes utility functions for 
conversation management, moderation, and validation of the generated output.

Functions:
- get_chat_model_completions: Handles interactions with the OpenAI chat model, including tool calls.
- is_flagged_text: Checks if the user input contains flagged content using OpenAI's moderation API.
- append_message_to_conversation: Appends a message to the conversation log with a specified role.
- initialize_conversation: Initializes the conversation with a system prompt for the meal planning assistant.
- intent_confirmation: Validates if the response contains a list of meals with the required structure.
- extract_python_dictionary: Extracts a Python dictionary containing meal details from a given text.
"""

import openai, json

file_path = './OPENAI_API_KEY.txt'
with open(file_path, 'r') as file:
    openai.api_key = file.readline()

def get_chat_model_completions(messages, call_function=None, tools=None):
    """
    Interacts with the OpenAI chat model to generate responses based on the provided messages.
    Handles tool calls if required and recursively processes the conversation.
    
    Args:
        messages (list): The conversation log containing messages exchanged with the model.
        call_function (function): A callback function to handle tool calls (optional).
        tools (list): A list of tools available for the model to use (optional).
    
    Returns:
        str: The content of the response message or the result of recursive processing.
    """
    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        temperature=0,
        tools=tools
    )

    finish_reason = response.choices[0].finish_reason
    response_message = response.choices[0].message
    if finish_reason == 'stop':
        return response_message.content
    if finish_reason == 'tool_calls':
        print('will make tool calls')
        tool_calls = response_message.tool_calls

        if tool_calls:
            messages.append(response_message.model_dump())
        
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_arguments = tool_call.function.arguments
                print(f'Function: {function_name}')
                print(f'Arguments: {function_arguments}')
                function_args = json.loads(function_arguments)
                function_response = call_function(function_name, function_args)
                print(f'Function Response: {function_response}')
        
                messages.append({
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                    "tool_call_id": tool_call.id
                })
        return get_chat_model_completions(messages, call_function, tools)

def is_flagged_text(user_input):
    """
    Checks if the user input contains flagged content using OpenAI's moderation API.
    
    Args:
        user_input (str): The input text to be checked.
    
    Returns:
        bool: True if the input is flagged, False otherwise.
    """
    response = openai.moderations.create(input=user_input)
    flagged = response.results[0].flagged
    return flagged

def append_message_to_conversation(conversation_log, message, role):
    """
    Appends a message to the conversation log with the specified role.
    
    Args:
        conversation_log (list): The conversation log to which the message will be appended.
        message (str): The content of the message.
        role (str): The role of the message (e.g., "user", "assistant", "system").
    """
    conversation_log.append({"role": role, "content": message})

def initialize_conversation(username):
    """
    Initializes the conversation with a system prompt for the meal planning assistant.
    The prompt includes instructions for the assistant and a personalized greeting for the user.
    
    Args:
        username (str): The name of the user.
    
    Returns:
        dict: A dictionary containing the system prompt with the role and content.
    """
    sample_food_categories = "Vegan, Vegetarian, etc."
    sample_food_ingredient = "Tofu, Rice, Chicken, etc."
    
    sample_output = {
           'meal_name': 'Grilled Chicken Quinoa Bowl',
           'nutrients': 'High in protein, fiber, and healthy fats',
           'ingredients': ['Chicken Breast',
            'Quinoa',
            'Avocado',
            'Spinach',
            'Cherry Tomatoes',
            'Olive Oil'],
           'main_ingredient': 'Chicken Breast',
           'food_category': 'Main Course',
           'description': 'This meal is packed with protein from the chicken, which helps in muscle recovery and strength gain. Quinoa provides complex carbohydrates for sustained energy, while spinach and tomatoes add essential vitamins.'
        }
    
    delimiter = "######"
    prompt = f"""

    You are an expert nutritionist, an expert meal planner and an expert health coach.
    Your objective is to interview the user and understand their health objective and present them with relevant meals.

    {delimiter}
    While you are interviewing the user, ask about their food categories.
    Before you ask the user about their food categories, get all food categories. You will be penalized if you start your conversation before getting all the food categories.
    You will add the list of food ingredients in the final output. The final output should contain food ingredients from authentic sources, so get all food ingredients. You will be penalized if you start your conversation before getting all the food ingredients.
    Once you know about all the food categories and food ingredients, keep it to yourself and do not show in the output for the users to choose from. Your conversation should be natural. Pick up a few random food categories and a few random food ingredient to show as an example to the user.conversation_log
    For example, when you show the food categories, you can show like {sample_food_categories}, and when you want to take examples of food ingredient, you can show something like {sample_food_ingredient}. Never show the entire list.
    If the user asks for more options, you can then share a few more varied options. But you will never show the entire list of food categories and food ingredients.

    {delimiter}
    The final output should contain meal name, which nutrients it contains, list of all the ingredients, name of the main ingredient, food category and a description of connection of health objective and the ingredients.
    The ingredient should only be from the list of ingredients that you fetched. The main_ingredient should be from the list of ingredients that you fetched.
    The final output should contain 5 meals only in a json format without any code markers. If you do not show 5 meals, you will be heavily penalized.
    the final output will look like {sample_output}

    {delimiter}
    Start by greeting the user and introducing yourself.
    The user's name is {username}.
    
    """

    prompt_with_role = {"role": "system", "content": prompt}
    return prompt_with_role

def intent_confirmation(response_mealcoach_assistant):
    """
    Validates if the response contains a list of meals with the required structure.
    
    Args:
        response_mealcoach_assistant (str): The response text to be validated.
    
    Returns:
        str: "yes" if the response contains the required structure, "no" otherwise.
    """
    delimiter = "#######"
    prompt = f"""
        You are a senior evaluator and a python expert.
        You will go through the text and find out if it contains a list of meals.
        Each and every meal item should contain the keys meal_name, nutrients, ingredients, main_ingredient, food_category, description.

        {delimiter}
        You all the keys are definitely present, then and only then you will respond with a "yes". Otherwise you will respond with a "no"

        {delimiter}
        Here is your input: {response_mealcoach_assistant}
        
    """

    conversation = [{"role": "system", "content": prompt}]
    response = get_chat_model_completions(conversation)
    return response

def extract_python_dictionary(text):
    """
    Extracts a Python dictionary containing meal details from the given text.
    
    Args:
        text (str): The input text containing meal details.
    
    Returns:
        dict: A Python dictionary containing the list of meals.
    """
    prompt = f"""

    You are a python expert.
    Your job is to extract python dictionary from {text} that contains the list of meals
    Each and every meal item contains the keys meal_name, nutrients, ingredients, main_ingredient, food_category, description.

    The output should be a json string without any code markers
    
    """

    conversation = [{"role": "system", "content": prompt}]
    response = get_chat_model_completions(conversation)
    return json.loads(response)