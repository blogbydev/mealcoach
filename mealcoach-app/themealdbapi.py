import requests

class TheMealDBAPI:
    def __init__(self, api_key):
        # self.base_url = f"https://www.themealdb.com/api/json/v2/{api_key}"
        self.base_url = f"https://www.themealdb.com/api/json/v1/1"
    
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
# with open('./MEALDB_API_KEY.txt') as file:
    # mealdb_api_key = file.readline()
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