import json
import ast
import sys
from io import StringIO
from types import SimpleNamespace
import traceback
from pathlib import Path

class Lesson:
    def __init__(self, lesson_file):
        self.lesson_file = lesson_file
        self.lesson_data = self.load_lesson()
        self.current_step = 0
        self.env = SimpleNamespace()
        self.env.__dict__.update(self.create_safe_env())  # Update namespace with safe builtins
        self.add_hint_system()  # Initialize hint system
        
    def create_safe_env(self):
        """Create a restricted environment for code execution"""
        safe_builtins = {
            'abs': abs, 'all': all, 'any': any, 'ascii': ascii, 
            'bin': bin, 'bool': bool, 'chr': chr, 'dict': dict,
            'dir': dir, 'divmod': divmod, 'enumerate': enumerate, 
            'filter': filter, 'float': float, 'format': format,
            'frozenset': frozenset, 'hash': hash, 'hex': hex, 
            'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
            'len': len, 'list': list, 'map': map, 'max': max, 
            'min': min, 'oct': oct, 'ord': ord, 'pow': pow,
            'print': print, 'range': range, 'repr': repr, 
            'reversed': reversed, 'round': round, 'set': set, 
            'slice': slice, 'sorted': sorted, 'str': str, 
            'sum': sum, 'tuple': tuple, 'type': type, 'zip': zip
        }
        return safe_builtins

    def get_multiline_input(self):
        """Collect multi-line input with editing capabilities"""
        print("Enter your code (press Enter twice when done):")
        print("Use 'show' to see current input")
        print("Use '<<' to remove last line")
        print("Use 'cancel' to start over")
        
        lines = []
        while True:
            prompt = "... " if lines else ">>> "
            line = input(prompt).rstrip()
            
            # Handle special commands
            if not lines and line in ('skip()', 'info()', 'bye()', 'main()', 'hint()'):
                return line
                
            # Special editing commands
            if line == '<<':  # Remove last line
                if lines:
                    removed = lines.pop()
                    print(f"Removed: {removed}")
                continue
            elif line == 'cancel':  # Cancel entire input
                print("Input cancelled")
                lines = []
                continue
            elif line == 'show':  # Show current input
                print("\nCurrent input:")
                for i, l in enumerate(lines, 1):
                    print(f"{i}: {l}")
                print()  # Extra newline for readability
                continue
                
            # Handle empty lines
            if not line:
                if lines:  # Empty line with content means we're done
                    final_code = '\n'.join(lines)
                    print("\nFinal code:")
                    print(final_code)
                    print()  # Extra newline for readability
                    return final_code
                continue  # Empty line without content is ignored
                
            lines.append(line)

    def add_hint_system(self):
        """Add a hint system to the Lesson class"""
        def show_hint():
            current_step = self.lesson_data['steps'][self.current_step]
            if 'hint' in current_step:
                print(f"\nHint: {current_step['hint']}")
            else:
                print("\nNo hint available for this step.")
        
        self.env.hint = show_hint

    def add_progress_tracking(self):
        """Track user progress through lessons"""
        total_steps = len([step for step in self.lesson_data['steps'] 
                        if step['type'] == 'input'])
        current_input_step = len([step for step in self.lesson_data['steps'][:self.current_step] 
                                if step['type'] == 'input'])
        print(f"\nProgress: {current_input_step}/{total_steps} exercises completed")

    def load_lesson(self):
        lesson_path = Path(__file__).parent / self.lesson_file
        print(f"Loading lesson from {lesson_path}")
        with open(lesson_path, 'r') as f:
            return json.load(f)

    def display_info(self):
        print("\nAvailable commands:")
        print(" - info() to display this list of options")
        print(" - skip() to skip the current question")
        print(" - main() to return to main menu")
        print(" - bye() to exit")
        print(" - hint() to get a hint for the current question")
        print(" - help(object) for Python help")
        print("\nMulti-line input commands:")
        print(" - Enter blank line to finish input")
        print(" - << to remove the last line")
        print(" - show to display current input")
        print(" - cancel to start over\n")

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
            
            if error:
                print("Error:", error)
                return False

            # Handle output like REPL
            if output:
                print("Output:")
                print(output.rstrip())
                print("\n-----------\n")
            
            # Print result like REPL if it's an expression that returns a value
            if result is not None and isinstance(user_ast.body[0], ast.Expr):
                print("Output:")
                if isinstance(result, str):
                    print(f"'{result}'")
                else:
                    print(repr(result))
                print("\n-----------\n")
            
            # Check against correct answers
            for correct_answer in correct_answers:
                # First try direct AST comparison
                correct_ast = ast.parse(correct_answer)
                correct_ast_str = ast.dump(correct_ast)
                
                if user_ast_str == correct_ast_str:
                    return True
                    
                # If AST comparison fails, try evaluating and comparing results
                try:
                    correct_result = eval(compile(correct_answer, '<string>', 'eval'), vars(self.env))
                    # Compare type and value
                    if result is not None:
                        expected_type = type(correct_result)
                        if isinstance(result, expected_type):
                            # Convert to list for sequence comparison, or direct compare for other types
                            if isinstance(correct_result, (list, tuple, set)):
                                if list(result) == list(correct_result):
                                    return True
                            elif isinstance(correct_result, dict):
                                if dict(result) == correct_result:
                                    return True
                            else:
                                if result == correct_result:
                                    return True
                        else:
                            print(f"Expected {expected_type.__name__}, but got {type(result).__name__}")
                except:
                    continue

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
                self.add_progress_tracking()  # Show progress
                while True:
                    user_input = self.get_multiline_input()  # Use multi-line input
                    
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
                    elif user_input == 'hint()':  # Add hint command handler
                        self.env.hint()
                        continue
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
                                print("Correct!")
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
        1: 'lessons/basics.json',
        2: 'lessons/datatypes.json',
        3: 'lessons/conditionals.json',
        4: 'lessons/functions.json',
        5: 'lessons/loops.json',
        6: 'lessons/exceptions.json'
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
                return
            elif selection in lessons:
                result = run_lesson(lessons[selection])
                if result == "exit_lesson":
                    return
            else:
                print("\n**Invalid selection**\n")
        except ValueError:
            print("\n**Please enter a number**\n")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Happy coding!")
            return

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