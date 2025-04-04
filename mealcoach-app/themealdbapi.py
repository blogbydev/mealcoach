"""
This file defines a Python class `TheMealDBAPI` that provides an interface to interact with TheMealDB API. 
It includes methods to fetch food categories, ingredients, filter meals by ingredients, and get meal details by ID. 
Additionally, it provides a function map and schema definitions for specific API functions.
"""

import requests

class TheMealDBAPI:
    def __init__(self, api_key):
        """
        Initialize the API client with the base URL.
        :param api_key: API key for TheMealDB (currently unused in the base URL).
        """
        # self.base_url = f"https://www.themealdb.com/api/json/v2/{api_key}"
        self.base_url = f"https://www.themealdb.com/api/json/v1/1"
    
    def get_all_food_categories(self):
        """
        Fetch all food categories from TheMealDB API.
        :return: A list of food categories (e.g., vegetarian, non-vegetarian).
        """
        response = requests.get(f'{self.base_url}/list.php?c=list').json()
        categories = [item['strCategory'] for item in response['meals']]
        return categories

    def get_all_food_ingredients(self):
        """
        Fetch all food ingredients from TheMealDB API.
        :return: A list of food ingredients used to prepare meals.
        """
        response = requests.get(f'{self.base_url}/list.php?i=list').json()
        ingredients = [item['strIngredient'] for item in response['meals']]
        return ingredients

    def filter_meal_by_ingredient(self, ingredients):
        """
        Filter meals based on a list of ingredients.
        :param ingredients: A list of ingredient names to filter meals by.
        :return: A JSON response containing meals that match the ingredients.
        """
        response = requests.get(f'{self.base_url}/filter.php?i={",".join(ingredients)}').json()
        return response

    def get_meal_details_by_id(self, meal_id):
        """
        Get detailed information about a meal by its ID.
        :param meal_id: The ID of the meal to fetch details for.
        :return: A JSON response containing meal details.
        """
        response = requests.get(f'{self.base_url}/lookup.php?i={meal_id}').json()
        return response

mealdb_api_key = None
# with open('./MEALDB_API_KEY.txt') as file:
    # mealdb_api_key = file.readline()
themealdbapi = TheMealDBAPI(mealdb_api_key)

# create function map
def call_function(name, args):
    """
    Call a specific function from the API client based on its name.
    :param name: The name of the function to call.
    :param args: Arguments for the function (currently unused).
    :return: The result of the function call.
    """
    if(name == "get_all_food_categories"):
        return themealdbapi.get_all_food_categories()
    if(name == "get_all_food_ingredients"):
        return themealdbapi.get_all_food_ingredients()

def get_function_schema(name):
    """
    Get the schema definition for a specific function.
    :param name: The name of the function to get the schema for.
    :return: A dictionary representing the function schema.
    """
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