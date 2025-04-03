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

def validate_message(message):
    if is_flagged_text(message):
        conversation_log.clear()
        meal_details.clear()
        append_message_to_conversation(conversation_log, "Your message was flagged for inappropriate content.", 'assistant')
        append_message_to_conversation(conversation_log, "Let's start over", 'assistant')
        conversation_log.append(initialize_conversation(username))
        response = get_chat_model_completions(conversation_log, call_function, themealdb_tools)
        append_message_to_conversation(conversation_log, response, 'assistant')
        
        raise ValueError("Message flagged for inappropriate content.")

def validate_username(username):
    if is_flagged_text(username):
        raise ValueError("Username flagged for inappropriate content.")

@app.route('/', methods=['GET', 'POST'])
def home_page():
    global username
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            validate_username(username)

            conversation_log.clear()
            meal_details.clear()
            conversation_log.append(initialize_conversation(username))
            response = get_chat_model_completions(conversation_log, call_function, themealdb_tools)
            validate_message(response)

            append_message_to_conversation(conversation_log, response, 'assistant')
            return redirect(url_for('meal_planner', method='POST'))
        except ValueError as e:
            print(f'Error: {e}')
            return render_template('index.html', error=str(e))
        except Exception as e:
            print(f'Error: {e}')
            return render_template('index.html', error="An unexpected error occurred.")
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
    try:
        message = request.form.get('message')
        validate_message(message)
        
        conversation_log.append({"role": "user", "content": message})
        response = get_chat_model_completions(conversation_log, call_function, themealdb_tools)
        validate_message(response)
        
        is_intent_confirmed = intent_confirmation(response)
        validate_message(is_intent_confirmed)

        if is_intent_confirmed == 'yes':
            append_message_to_conversation(conversation_log, "Thank you for providing your inputs, let me show you some recipes", 'assistant')
            meals_suggested_by_assistant = extract_python_dictionary(response)

            if isinstance(meals_suggested_by_assistant, dict) and 'meals' in meals_suggested_by_assistant:
                meals_suggested_by_assistant = meals_suggested_by_assistant['meals']

            meal_details = get_meals(meals_suggested_by_assistant)
        else:
            meal_details.clear()
            append_message_to_conversation(conversation_log, response, 'assistant')
    except ValueError as e:
        print(f'Error: {e}')
    except Exception as e:
        print(f'Error: {e}')
    
    return redirect(url_for('meal_planner', method='POST'))


def get_meals(meals_suggested_by_assistant):
    meals = []
    meal_details = []
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
    return meal_details

if __name__ == '__main__':
    app.run(debug=True)