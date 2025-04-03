from flask import Flask, render_template
from flask import request
from flask import redirect, url_for
from mealcoachai import (
    get_chat_model_completions,
    is_flagged_text,
    append_message_to_conversation,
    initialize_conversation,
    intent_confirmation,
    extract_python_dictionary
)

app = Flask(__name__)
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
        response = get_chat_model_completions(conversation_log, call_function, themealdb_tools)
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
    response = get_chat_model_completions(conversation_log, call_function, themealdb_tools)
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