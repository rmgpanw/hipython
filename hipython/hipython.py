import json
import ast
import sys
from io import StringIO
from types import SimpleNamespace
import traceback

class Lesson:
    def __init__(self, lesson_file):
        self.lesson_file = lesson_file
        self.lesson_data = self.load_lesson()
        self.current_step = 0
        self.env = SimpleNamespace()

    def load_lesson(self):
        with open(self.lesson_file) as f:
            return json.load(f)

    def display_info(self):
        print("\nAvailable commands:")
        print(" - info() to display this list of options")
        print(" - skip() to skip the current question")
        print(" - main() to return to main menu")
        print(" - bye() to exit")
        print(" - help(object) for Python help\n")

    def skip(self):
        print("Skipping the current question.")
        self.current_step += 1

    def info(self):
        self.display_info()

    def bye(self):
        print("Exiting the lesson.")

    def execute_user_code(self, code):
        """
        Executes user code and captures output/errors.
        Returns (success, output, error, result)
        """
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output

        success = True
        error_msg = None
        result = None

        try:
            # Try eval first for expressions
            try:
                result = eval(compile(code, '<string>', 'eval'), vars(self.env))
            except SyntaxError:
                # If eval fails, try exec for statements
                exec(compile(code, '<string>', 'exec'), vars(self.env))
                result = None
        except Exception as e:
            success = False
            error_msg = f"{type(e).__name__}: {str(e)}"
        finally:
            output = redirected_output.getvalue()
            sys.stdout = old_stdout
            
        return success, output, error_msg, result

    def check_answer(self, user_input, correct_answers):
        user_input = user_input.strip()
        try:
            # Parse user's input
            user_ast = ast.parse(user_input)
            user_ast_str = ast.dump(user_ast)
            
            # Execute the code and show output
            success, output, error, result = self.execute_user_code(user_input)
            
            if output:
                print("Output:", output.rstrip())
            
            if error:
                print("Error:", error)
                return False
            
            # Check against correct answers
            for correct_answer in correct_answers:
                correct_ast = ast.parse(correct_answer)
                correct_ast_str = ast.dump(correct_ast)

                if user_ast_str == correct_ast_str:
                    return True

            if result is not None:
                print("Result:", result)
            return False
            
        except SyntaxError as e:
            print(f"Syntax Error: {str(e)}")
            return False

    def run(self):
        if not self.lesson_data:
            return
            
        print(f"\nStarting lesson: {self.lesson_data['lesson_name']}")
        print(self.lesson_data['description'])
        self.display_info()

        while self.current_step < len(self.lesson_data['steps']):
            step = self.lesson_data['steps'][self.current_step]

            if 'type' not in step:
                print("Error: Step is missing a 'type' key. Skipping this step.")
                self.current_step += 1
                continue

            if step['type'] == 'chunk':
                print("\n" + step['instruction'])
                input("Press Enter to continue...")
                print("...")
                self.current_step += 1

            elif step['type'] == 'input':
                print("\n" + step['instruction'])
                while True:
                    user_input = input(">>> ").strip()
                    
                    if user_input == 'skip()':
                        self.skip()
                        break
                    elif user_input == 'info()':
                        self.info()
                        continue
                    elif user_input == 'bye()':
                        self.bye()
                        return 'exit_lesson'
                    elif user_input == 'main()':
                        print("Returning to the main menu...")
                        return 'main_menu'
                    elif user_input.startswith('help('):
                        try:
                            eval(user_input, vars(self.env))
                            continue
                        except Exception as e:
                            print(f"Error: {str(e)}")
                            continue

                    if isinstance(step['answer'], dict):
                        if step['answer']['type'] == 'assignment':
                            variable_name = step['answer']['variable']
                            expected_value = step['answer']['value']
                            
                            success, output, error, _ = self.execute_user_code(user_input)
                            
                            if output:
                                print("Output:", output.rstrip())
                                
                            if error:
                                print("Error:", error)
                                continue
                                
                            actual_value = getattr(self.env, variable_name, None)
                            if actual_value == expected_value:
                                print(f"Correct! {variable_name} = {actual_value}")
                                self.current_step += 1
                                break
                            else:
                                if actual_value is None:
                                    print(f"Variable '{variable_name}' was not assigned.")
                                else:
                                    print(f"The value of {variable_name} is {actual_value}, but should be {expected_value}")
                                    
                        elif step['answer']['type'] == 'expression':
                            correct_expressions = step['answer']['value'] if isinstance(step['answer']['value'], list) else [step['answer']['value']]
                            if self.check_answer(user_input, correct_expressions):
                                print("Correct!")
                                self.current_step += 1
                                break
                            else:
                                print("Not quite. Try again.")
                    else:
                        correct_answers = step['answer'] if isinstance(step['answer'], list) else [step['answer']]
                        if self.check_answer(user_input, correct_answers):
                            print("Correct!")
                            self.current_step += 1
                            break
                        else:
                            print("Not quite. Try again.")

            else:
                print(f"Unknown step type {step['type']}")
                self.current_step += 1
                
        print("\nLesson complete! Congratulations!\n")
        print("Returning to main menu...\n")
        return 'main_menu'

def display_menu():
    """Displays a list of available lessons and allows the user to select one."""
    lessons = {
        1: 'hipython/lessons/basics.json',
        2: 'hipython/lessons/functions.json',
    }
    
    while True:
        print("Welcome to HiPython!")
        print("\nAvailable lessons:")
        for idx, lesson in lessons.items():
            print(f"{idx}. {lesson.split('/')[-1].replace('.json', '').title()}")
        print("0. Quit")

        try:
            selection = int(input("\nEnter lesson number (0 to quit): "))
            if selection == 0:
                print("\nGoodbye! Happy coding!")
                break
            elif selection in lessons:
                result = run_lesson(lessons[selection])
                if result == "exit_lesson":
                    break
            else:
                print("\n**Invalid selection**\n")
        except ValueError:
            print("\n**Please enter a number**\n")

def run_lesson(lesson_file):
    """Runs the selected lesson and handles returning to the main menu."""
    try:
        lesson = Lesson(lesson_file)
        return lesson.run()
    except FileNotFoundError:
        print(f"\nError: Lesson file '{lesson_file}' not found.")
        return "main_menu"
    except json.JSONDecodeError:
        print(f"\nError: Invalid JSON in lesson file '{lesson_file}'.")
        return "main_menu"
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        return "main_menu"

def start():
    """Start the HiPython program."""
    display_menu()

if __name__ == "__main__":
    start()
    