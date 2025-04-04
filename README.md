# MealCoach

MealCoach is a personalized meal planning application designed to help users create healthy, balanced, and customized meal plans. By leveraging AI and external APIs, MealCoach provides users with tailored meal suggestions based on their dietary preferences, restrictions, and goals.

## Features

- **Personalized Meal Plans**: Generate meal plans based on user preferences, including dietary restrictions, calorie goals, and cuisine types.
- **Recipe Suggestions**: Access a wide variety of recipes sourced from TheMealDB API.
- **Interactive User Interface**: A clean and intuitive web interface for users to easily navigate and plan their meals.
- **AI-Powered Recommendations**: Utilize AI to suggest meals that align with user preferences and nutritional goals.

## How It Works

1. **Input Preferences**: Users provide their dietary preferences, restrictions, and goals.
2. **AI Processing**: The application uses AI to analyze the input and generate meal suggestions.
3. **Recipe Integration**: Recipes are fetched from TheMealDB API and displayed to the user.
4. **Meal Plan Generation**: Users can view and customize their meal plans.

## Technologies Used

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS (via templates)
- **API Integration**: TheMealDB API for recipe data
- **AI**: Custom AI logic for meal recommendations
- **Dependencies**: Managed via `requirements.txt`

## Folder Structure

- `mealcoach-app/`: Contains the main application code.
  - `app.py`: The Flask application entry point.
  - `mealcoachai.py`: AI logic for meal recommendations.
  - `themealdbapi.py`: Handles integration with TheMealDB API.
  - `templates/`: HTML templates for the web interface.
    - `index.html`: Homepage of the application.
    - `meal-planner.html`: Meal planning interface.
  - `requirements.txt`: Lists all dependencies required to run the application.

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mealcoach.git
   cd mealcoach/mealcoach-app