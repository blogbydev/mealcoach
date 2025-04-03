import openai, json

file_path = './OPENAI_API_KEY.txt'
with open(file_path, 'r') as file:
    openai.api_key = file.readline()

def get_chat_model_completions(messages, call_function = None, tools=None):
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
        return get_chat_model_completions(messages, call_function, tools)

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
    return response