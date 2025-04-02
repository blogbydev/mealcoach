from flask import Flask, render_template
from flask import request
from flask import redirect, url_for
import json, openai

app = Flask(__name__)

#########################################################################
file_path = './OPENAI_API_KEY.txt'
with open(file_path, 'r') as file:
    openai.api_key = file.readline()

def get_chat_model_completions(messages, tools=None):
    response = openai.chat.completions.create(
        model = 'gpt-4o-mini',
        messages = messages,
        temperature = 0,
        tools = tools
    )

    finish_reason = response.choices[0].finish_reason
    response_message = response.choices[0].message
    if(finish_reason == 'stop'):
        return response_message.content
    if(finish_reason == 'tool_calls'):
        print('will make tool calls')
        tool_calls = response_message.tool_calls

        if(tool_calls):
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
        return get_chat_model_completions(messages, tools)

def is_flagged_text(user_input):
    response = openai.moderations.create(input=user_input)
    flagged = response.results[0].flagged
    return flagged

def append_message_to_conversation(conversation_log, message, role):
    conversation_log.append({"role": role, "content": message})

def initialize_conversation(username):
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
    prompt = f"""

    You are a python expert.
    Your job is to extract python dictionary from {text} that contains the list of meals
    Each and every meal item contains the keys meal_name, nutrients, ingredients, main_ingredient, food_category, description.

    The output should be a json string without any code markers
    
    """

    conversation = [{"role": "system", "content": prompt}]
    response = get_chat_model_completions(conversation)
    return json.loads(response)
#########################################################################

#########################################################################
import requests

class TheMealDBAPI:
    def __init__(self, api_key):
        self.base_url = f"https://www.themealdb.com/api/json/v2/{api_key}"
    
    def get_all_food_categories(self):
        response = requests.get(f'{self.base_url}/list.php?c=list').json()
        categories = [item['strCategory'] for item in response['meals']]
        return categories

    def get_all_food_ingredients(self):
        response = requests.get(f'{self.base_url}/list.php?i=list').json()
        ingredients = [item['strIngredient'] for item in response['meals']]
        return ingredients

    def filter_meal_by_ingredient(self, ingredients):
        response = requests.get(f'{self.base_url}/filter.php?i={",".join(ingredients)}').json()
        return response

    def get_meal_details_by_id(self, meal_id):
        response = requests.get(f'{self.base_url}/lookup.php?i={meal_id}').json()
        return response

mealdb_api_key = None
with open('./MEALDB_API_KEY.txt') as file:
    mealdb_api_key = file.readline()
themealdbapi = TheMealDBAPI(mealdb_api_key)

# create function map
def call_function(name, args):

    if(name == "get_all_food_categories"):
        return themealdbapi.get_all_food_categories()
    if(name == "get_all_food_ingredients"):
        return themealdbapi.get_all_food_ingredients()

def get_function_schema(name):
    function_schema_map = {
        "get_all_food_categories": {
            "name": "get_all_food_categories",
            "description": "get all food categories, like vegetarian, non-vegetarian, etc.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
              }
        },
        "get_all_food_ingredients": {
            "name": "get_all_food_ingredients",
            "description": "get a list of food ingredients to be used to prepare a meal",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        }
    }
    return function_schema_map[name]

themealdb_tools = []
themealdb_tools.append({
    "type": "function",
    "function": get_function_schema("get_all_food_categories")
})
themealdb_tools.append({
    "type": "function",
    "function": get_function_schema("get_all_food_ingredients")
})
#########################################################################

# Global variable to store conversation
username = ""
conversation_log = []
meal_details = []

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/meal-planner', methods=['GET', 'POST'])
def meal_planner():
    global username
    global conversation_log
    global meal_details
    if request.method == 'POST':
        username = request.form.get('username')
        conversation_log = []
        meal_details = []
        conversation_log.append(initialize_conversation(username))
        response = get_chat_model_completions(conversation_log, themealdb_tools)
        append_message_to_conversation(conversation_log, response, 'assistant')
    print('############conversation log')
    print(conversation_log)
    return render_template('meal-planner.html',username=username, conversation_log=conversation_log, meal_details=meal_details)


@app.route('/conversation-handler', methods=['POST'])
def conversation_handler():
    global conversation_log
    global meal_details
    message = request.form.get('message')
    if is_flagged_text(message):
        append_message_to_conversation(conversation_log, "Your message was flagged for inappropriate content.", 'assistant')
        return redirect(url_for('meal_planner', method='POST'))
    
    conversation_log.append({"role": "user", "content": message})
    response = get_chat_model_completions(conversation_log, themealdb_tools)
    append_message_to_conversation(conversation_log, response, 'assistant')

    is_intent_confirmed = intent_confirmation(response)
    if(is_intent_confirmed == 'yes'):
        print('Intent confirmed')
        conversation_log.pop()
        append_message_to_conversation(conversation_log, "Thank you for providing your inputs, let me show you some recipes", 'assistant')
        meals_suggested_by_assistant = extract_python_dictionary(response)
        meals = []

        if isinstance(meals_suggested_by_assistant, dict) and 'meals' in meals_suggested_by_assistant:
            meals_suggested_by_assistant = meals_suggested_by_assistant['meals']

        for meal_suggested in meals_suggested_by_assistant:
            main_ingredient = meal_suggested['main_ingredient']
            print(main_ingredient)
            meals_available = themealdbapi.filter_meal_by_ingredient([main_ingredient])
            if meals_available['meals'] != None:
                meals.extend(meals_available['meals'])
        meal_ids = [meal['idMeal'] for meal in meals]
        # select top 5 meals
        meal_ids = list(set(meal_ids))[:5]
        for meal_id in meal_ids:
            meal_details.append(themealdbapi.get_meal_details_by_id(meal_id)['meals'][0])
    
    return redirect(url_for('meal_planner', method='POST'))


if __name__ == '__main__':
    app.run(debug=True)