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
from themealdbapi import themealdbapi, call_function, themealdb_tools

app = Flask(__name__)

# Global variable to store conversation
username = ""
conversation_log = []
meal_details = []

@app.route('/', methods=['GET', 'POST'])
def home_page():
    global username
    if request.method == 'POST':
        username = request.form.get('username')
        conversation_log.append(initialize_conversation(username))
        response = get_chat_model_completions(conversation_log, call_function, themealdb_tools)
        append_message_to_conversation(conversation_log, response, 'assistant')
        return redirect(url_for('meal_planner', method='POST'))
    else:
        username = ""
        conversation_log.clear()
        meal_details.clear()
        return render_template('index.html')

@app.route('/meal-planner')
def meal_planner():
    global username
    global conversation_log
    global meal_details
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
    
    is_intent_confirmed = intent_confirmation(response)
    if(is_intent_confirmed == 'yes'):
        append_message_to_conversation(conversation_log, "Thank you for providing your inputs, let me show you some recipes", 'assistant')
        meals_suggested_by_assistant = extract_python_dictionary(response)
        meals = []

        if isinstance(meals_suggested_by_assistant, dict) and 'meals' in meals_suggested_by_assistant:
            meals_suggested_by_assistant = meals_suggested_by_assistant['meals']

        for meal_suggested in meals_suggested_by_assistant:
            main_ingredient = meal_suggested['main_ingredient']
            meals_available = themealdbapi.filter_meal_by_ingredient([main_ingredient])
            if meals_available['meals'] != None:
                meals.extend(meals_available['meals'])
        meal_ids = [meal['idMeal'] for meal in meals]
        # select top 5 meals
        meal_ids = list(set(meal_ids))[:5]
        for meal_id in meal_ids:
            meal_details.append(themealdbapi.get_meal_details_by_id(meal_id)['meals'][0])
    else:
        append_message_to_conversation(conversation_log, response, 'assistant')
    
    return redirect(url_for('meal_planner', method='POST'))


if __name__ == '__main__':
    app.run(debug=True)