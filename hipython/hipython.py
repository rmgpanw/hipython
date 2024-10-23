import json
import ast

class Lesson:
    def __init__(self, lesson_file):
        self.lesson_file = lesson_file
        self.lesson_data = self.load_lesson()
        self.current_step = 0
        self.variables = {}  # Dictionary to hold variable assignments

    def load_lesson(self):
        with open(self.lesson_file) as f:
            return json.load(f)

    def display_info(self):
        print("Available commands:")
        print(" - info() to display this list of options.")
        print(" - skip() to skip the current question.")
        print(" - main() to return to main menu.")
        print(" - bye() to exit.")

    def skip(self):
        print("Skipping the current question.")
        self.current_step += 1

    def info(self):
        self.display_info()

    def bye(self):
        print("Exiting the lesson. Your progress has been saved.")

    def check_answer(self, user_input, correct_answers):
        try:
            # Use ast.literal_eval to safely evaluate the user's input
            evaluated_input = ast.literal_eval(user_input.strip())
            # Check if the evaluated input matches any of the correct answers
            return evaluated_input in correct_answers
        except (ValueError, SyntaxError):
            return False

    def run(self):
        if not self.lesson_data:
            return
        print(f"Starting lesson: {self.lesson_data['lesson_name']}")
        print(self.lesson_data['description'])
        self.display_info()

        while self.current_step < len(self.lesson_data['steps']):
            step = self.lesson_data['steps'][self.current_step]

            # Ensure 'type' key exists
            if 'type' not in step:
                print("Error: Step is missing a 'type' key. Skipping this step.")
                self.current_step += 1
                continue

            # Handle chunk steps (instructional text with `...`)
            if step['type'] == 'chunk':
                print(step['instruction'])
                input("Press Enter to continue...")  # Wait for user to press Enter
                print("...")  # Print "..." to mimic swirl
                self.current_step += 1

            # Handle input steps (where user must type something)
            elif step['type'] == 'input':
                print(step['instruction'])

                # Prompt for user input with options to use commands
                user_input = input("> ").strip()

                # Check for special commands
                if user_input == 'skip()':
                    self.skip()
                    continue
                elif user_input == 'info()':
                    self.info()
                    continue
                elif user_input == 'bye()':
                    self.bye()
                    return 'exit_lesson'
                elif user_input == 'main()':
                    print("Returning to the main menu...")
                    return 'main_menu'  # Return to signal that we should return to the main menu

                if isinstance(step['answer'], dict) and step['answer']['type'] == 'assignment':
                    # Handle variable assignment
                    variable_name = step['answer']['variable']
                    expected_value = step['answer']['value']
                    assignment_input = f"{variable_name} = {user_input.strip()}"
                    try:
                        exec(assignment_input, {}, self.variables)
                        # Check if the assigned value is correct
                        if self.variables.get(variable_name) == expected_value:
                            print(f"Assigned {self.variables[variable_name]} to '{variable_name}'.")
                            self.current_step += 1
                        else:
                            print(f"Assigned value is incorrect. Expected {expected_value}. Try again.")
                    except Exception as e:
                        print(f"Error in assignment: {e}. Try again.")

                elif isinstance(step['answer'], dict) and step['answer']['type'] == 'check_variable':
                    # Handle variable checking
                    variable_name = step['answer']['variable']
                    if user_input.strip() == variable_name:
                        # Display the value of the variable
                        print(self.variables.get(variable_name, "Variable not found."))
                        self.current_step += 1
                    else:
                        print("Wrong variable name, try again.")

                else:
                    correct_answers = step['answer'] if isinstance(step['answer'], list) else [step['answer']]
                    if self.check_answer(user_input, correct_answers):
                        print("Correct!")
                        self.current_step += 1
                    else:
                        print("Wrong, try again.")

            else:
                print("Unknown step type.")
                
        print("Lesson complete! Congratulations!")

def display_menu():
    """Displays a list of available lessons and allows the user to select one."""
    lessons = {
        1: 'hipython/lessons/lesson.json',  # Add more lessons here if needed
    }
    print("Welcome to HiPython!")
    print("Select a lesson to start:")
    for idx, lesson in lessons.items():
        print(f"{idx}. Lesson {idx}")
    
    try:
        selection = int(input("Enter the number of the lesson you want to start: "))
        if selection in lessons:
            run_lesson(lessons[selection])
        else:
            print("Invalid selection. Returning to menu...")
            display_menu()  # Call the menu again on invalid input
    except ValueError:
        print("Invalid input. Please enter a number.")
        display_menu()


def run_lesson(lesson_file):
    """Runs the selected lesson and handles returning to the main menu."""
    lesson = Lesson(lesson_file)
    result = lesson.run()

    if result == "main_menu":
        display_menu()
    elif result == "exit_lesson":
        print("Goodbye!")


def start():
    """Start the HiPython program."""
    display_menu()
