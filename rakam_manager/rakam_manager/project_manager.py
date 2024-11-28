import os
import yaml
import shutil
from typing import Any, List, Dict, Tuple, Union, Optional


class ProjectManager:
    COMPONENTS_DIR = "components"
    BASE_TEMPLATE_DIR = os.path.join(
        os.path.dirname(__file__), "templates", "base_template"
    )
    CONFIG_FILE = os.path.join(BASE_TEMPLATE_DIR, "system_config.yaml")

    def __init__(self):
        if not os.path.exists(self.CONFIG_FILE):
            raise FileNotFoundError(
                f"Configuration file '{self.CONFIG_FILE}' not found."
            )

    def create_project(self, project_name):
        if not os.path.exists(self.BASE_TEMPLATE_DIR):
            raise FileNotFoundError("Base template directory does not exist.")

        if os.path.exists(project_name):
            raise FileExistsError(f"Project '{project_name}' already exists.")

        shutil.copytree(self.BASE_TEMPLATE_DIR, project_name)
        print(f"Project '{project_name}' created successfully.")

    def generate_component_package(self, component_name, component_path):
        """
        Generate a package for the component with the specified name.
        :param component_name: Name of the component.
        """
        try:

            os.makedirs(component_path, exist_ok=True)

            # Create __init__.py
            init_file_path = os.path.join(component_path, "__init__.py")
            with open(init_file_path, "w") as init_file:
                init_file.write(f"# {component_name} package\n")

            # Create a file for the component with a default class
            functions_file_path = os.path.join(
                component_path, f"{component_name}_functions.py"
            )
            with open(functions_file_path, "w") as functions_file:
                functions_file.write(
                    f"""from rakam_systems.components.component import Component


class {component_name.capitalize()}(Component):
    \"\"\"Default implementation for {component_name.capitalize()} component.\"\"\"

    def call_main(self, **kwargs) -> dict:
        \"\"\"Main method for executing the component's functionality.\"\"\"
        pass

    def test(self, **kwargs) -> bool:
        \"\"\"Method for testing the component.\"\"\"
        pass
"""
                )

            print(
                f"Component package '{component_name}' generated successfully at {component_path}."
            )
        except Exception as e:
            raise Exception(
                f"Error generating package for component '{component_name}': {e}"
            )

    def add_component(self, component_name):
        """
        Add a new component to the YAML file if it does not already exist.
        """
        with open(self.CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)

        # Check if the component already exists
        for server_group in config["ServerGroups"]:
            for component in server_group["components"]:
                if component_name in component:
                    print(f"Component '{component_name}' already exists.")
                    return False

        # Add the new component
        new_component = {component_name: {}}
        if not config["ServerGroups"][0]["components"]:
            config["ServerGroups"][0]["components"] = []
        config["ServerGroups"][0]["components"].append(new_component)

        with open(self.CONFIG_FILE, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False)
        return True

    def delete_component(self, component_name):
        """
        Delete a component from the YAML file.
        :param component_name: Name of the component.
        """
        with open(self.CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)

        component_found = False
        for server_group in config["ServerGroups"]:
            for component in server_group["components"]:
                if component_name in component:
                    server_group["components"].remove(component)
                    component_found = True
                    break
            if component_found:
                break

        if not component_found:
            raise ValueError(
                f"Component '{component_name}' not found in the configuration."
            )

        with open(self.CONFIG_FILE, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False)

    def add_function_to_component(self, component_name, function_name, parameters):
        """
        Add a new function to an existing component in the YAML file if it does not already exist.
        """
        with open(self.CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)

        # Find the component in the ServerGroups
        for server_group in config["ServerGroups"]:
            for component in server_group["components"]:
                if component_name in component:
                    if function_name in component[component_name]:
                        print(
                            f"Function '{function_name}' already exists in component '{component_name}'."
                        )
                        return False
                    # Add the function
                    component[component_name][function_name] = {
                        "path": f"{component_name.lower()}/{function_name}/",
                        "parameters": parameters,
                    }
                    with open(self.CONFIG_FILE, "w") as file:
                        yaml.safe_dump(config, file, default_flow_style=False)
                    return True

        raise ValueError(
            f"Component '{component_name}' not found in the configuration."
        )

    def delete_function_from_component(self, component_name, function_name):
        """
        Delete a function from a component in the YAML file.
        :param component_name: Name of the component.
        :param function_name: Name of the function to delete.
        """
        with open(self.CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)

        component_found = False
        for server_group in config["ServerGroups"]:
            for component in server_group["components"]:
                if component_name in component:
                    if function_name in component[component_name]:
                        del component[component_name][function_name]
                        component_found = True
                        break
            if component_found:
                break

        if not component_found:
            raise ValueError(
                f"Function '{function_name}' not found in component '{component_name}'."
            )

        with open(self.CONFIG_FILE, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False)

    def modify_function_in_component(self, component_name, function_name, parameters):
        """
        Modify a function in a component in the YAML file.
        :param component_name: Name of the component.
        :param function_name: Name of the function to modify.
        :param parameters: New parameters for the function.
        """
        with open(self.CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)

        component_found = False
        for server_group in config["ServerGroups"]:
            for component in server_group["components"]:
                if component_name in component:
                    if function_name in component[component_name]:
                        component[component_name][function_name][
                            "parameters"
                        ] = parameters
                        component_found = True
                        break
            if component_found:
                break

        if not component_found:
            raise ValueError(
                f"Function '{function_name}' not found in component '{component_name}'."
            )

        with open(self.CONFIG_FILE, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False)

    def update_views_and_serializers(
        self, project_path, component_name, function_name, parameters, output_type
    ):
        """
        Update the views.py and serializers.py files for the new component function.
        :param component_name: Name of the component.
        :param function_name: Name of the function.
        :param parameters: Parameters of the function.
        :param output_type: Return type of the function.
        """
        SERIALIZERS_FILE = os.path.join(project_path, "application/serializers.py")
        VIEWS_FILE = os.path.join(project_path, "application/views.py")
        try:
            # Generate serializer
            serializer_class = f"{function_name.capitalize()}Serializer"
            serializer_code = f"\n\nclass {serializer_class}(serializers.Serializer):\n"
            for param, details in parameters.items():
                field_type = self._map_type(details["type"])
                if field_type == "CharField" and details.get("max_length"):
                    serializer_code += (
                        f"    {param} = serializers.{field_type}("
                        f"required={details['required']}, max_length={details['max_length']})\n"
                    )
                else:
                    serializer_code += f"    {param} = serializers.{field_type}(required={details['required']})\n"

            with open(SERIALIZERS_FILE, "a") as serializers_file:
                serializers_file.write(serializer_code)
                print(f"Serializer for '{function_name}' added to serializers.py.")

            self._add_serializer_import(serializer_class, VIEWS_FILE)

            # Generate JSON-compatible response schema
            response_schema = self._generate_response_schema(output_type)

            # Generate view
            view_name = function_name.lower()
            description = f"{function_name} function for {component_name.capitalize()}."

            view_code = f"""

    @extend_schema(
        request={serializer_class},
        responses={{
            200: OpenApiResponse(
                response={response_schema}, description="{description}"
            ),
            400: OpenApiResponse(description="Bad Request"),
        }},
        description="{description}",
        tags=["{component_name.capitalize()}"],
    )
    @api_view(["POST"])
    def {view_name}(request):
        serializer = {serializer_class}(data=request.data)
        if serializer.is_valid():
            # Call the component's function with validated data
            try:
                response_data = components.{component_name.lower()}.{function_name}(
                    **serializer.validated_data
                )
                return Response({{"data": response_data}}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({{"error": str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({{"errors": serializer.errors}}, status=status.HTTP_400_BAD_REQUEST)
    """

            with open(VIEWS_FILE, "a") as views_file:
                views_file.write(view_code)
                print(f"View for '{function_name}' added to views.py.")

        except Exception as e:
            raise Exception(
                f"Error updating views and serializers for function '{function_name}': {e}"
            )

    def _map_type(self, param_type):
        """
        Map a parameter type to the appropriate Django Rest Framework serializer field.
        """
        mapping = {
            "str": "CharField",
            "int": "IntegerField",
            "bool": "BooleanField",
            "float": "FloatField",
            "list": "ListField",
            "dict": "JSONField",
        }
        # Default to `CharField` if the type is unknown
        return mapping.get(param_type.lower(), "CharField")

    def _generate_response_schema(self, output_type):
        """
        Generate a JSON-compatible OpenAPI response schema for the output type.
        """
        try:
            # Handle common output types
            type_mapping = {
                "str": "string",
                "int": "integer",
                "bool": "boolean",
                "float": "number",
                "list": {"type": "array", "items": {"type": "object"}},
                "dict": {"type": "object", "additionalProperties": True},
            }
            output_schema = type_mapping.get(output_type.lower(), {"type": "object"})
            return {
                "type": "object",
                "properties": {
                    "data": output_schema,
                },
            }
        except Exception:
            return {
                "type": "object",
                "properties": {
                    "data": {"type": "string"},
                },
            }

    def generate_function_skeleton(
        self, component_name, component_path, function_name, parameters, output_type
    ):
        """
        Add a method skeleton to the component class with a default implementation.
        :param component_name: Name of the component.
        :param function_name: Name of the function.
        :param parameters: Parameters of the function.
        :param output_type: Return type of the function.
        """
        try:
            functions_file_path = os.path.join(
                component_path, f"{component_name}_functions.py"
            )

            # Prepare the parameter string for the function
            param_list = ", ".join(
                f"{param}: {details['type']}" for param, details in parameters.items()
            )
            if param_list:
                param_list = f"self, {param_list}"
            else:
                param_list = "self"

            # Prepare the docstring
            param_docs = "\n".join(
                f"        :param {param}: {details['type']}"
                for param, details in parameters.items()
            )

            # Generate default return value
            default_return_value = self.get_default_value_for_type(output_type)

            # Function skeleton with a default return value
            function_skeleton = f"""
    def {function_name}({param_list}) -> {output_type}:
        \"\"\"{function_name} method for {component_name.capitalize()}.

{param_docs}
        :return: {output_type}
        \"\"\"
        return {default_return_value}
"""

            # Append the skeleton to the class file
            with open(functions_file_path, "a") as functions_file:
                functions_file.write(function_skeleton)

            print(
                f"Function skeleton for '{function_name}' added to {functions_file_path}."
            )
        except Exception as e:
            raise Exception(
                f"Error generating skeleton for function '{function_name}': {e}"
            )

    def get_default_value_for_type(self, type_name: str):
        """
        Return a default value for a given Python type.
        :param type_name: The type as a string.
        :return: A string representing the default value for that type.
        """
        try:
            # Evaluate the type name to validate it
            type_eval = eval(type_name, globals(), locals())
            # Map types to default values
            if type_eval in [int]:
                return "0"
            elif type_eval in [float]:
                return "0.0"
            elif type_eval in [str]:
                return '""'
            elif type_eval in [bool]:
                return "False"
            elif type_eval in [list, List]:
                return "[]"
            elif type_eval in [dict, Dict]:
                return "{}"
            elif type_eval in [tuple, Tuple]:
                return "()"
            elif type_eval in [set]:
                return "set()"
            elif type_eval in [None, type(None)]:
                return "None"
            else:
                return f"{type_name}()"  # Assume it's a class or callable
        except Exception:
            # If the type is unknown or invalid, return None
            return "None"

    def _update_yaml(self, component_name, functions):
        with open(self.CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)

        new_component = {component_name: {}}
        for func in functions:
            func_name = func["name"]
            new_component[component_name][func_name] = {
                "path": f"{component_name.lower()}/{func_name}/",
                "parameters": func["parameters"],
            }

        # Add to the first ServerGroup for simplicity
        config["ServerGroups"][0]["components"].append(new_component)

        with open(self.CONFIG_FILE, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False)

    def update_components_file(self, component_name, init_component_path):
        """
        Update the components.py file to import and initialize the new component.
        :param component_name: Name of the new component.
        """
        try:
            # Prepare import and initialization statements
            import_statement = f"from rakam_systems.components.{component_name}.{component_name}_functions import {component_name.capitalize()}\n"
            init_statement = f"{component_name.lower()} = {component_name.capitalize()}(system_manager=system_manager)\n"

            # Read the existing components file
            with open(init_component_path, "r") as components_file:
                lines = components_file.readlines()

            # Check if the component already exists
            if import_statement in lines or any(
                init_statement.strip() in line for line in lines
            ):
                print(f"Component '{component_name}' already exists in components.py.")
                return

            # Add import statement before the first blank line after the existing imports
            import_index = next(
                (i for i, line in enumerate(lines) if line.strip() == ""), len(lines)
            )
            lines.insert(import_index, import_statement)

            # Add initialization statement before the last blank line
            init_index = next(
                (i for i, line in enumerate(reversed(lines)) if line.strip() == ""), 0
            )
            init_index = len(lines) - init_index - 1
            lines.insert(init_index, init_statement)

            # Write the updated content back to components.py
            with open(init_component_path, "w") as components_file:
                components_file.writelines(lines)

            print(f"Component '{component_name}' added to components.py successfully.")
        except Exception as e:
            raise Exception(
                f"Error updating components.py for component '{component_name}': {e}"
            )

    def _generate_component_shell(self, component_name, functions):
        component_path = os.path.join(self.COMPONENTS_DIR, component_name)
        os.makedirs(component_path, exist_ok=True)

        # Create __init__.py
        with open(os.path.join(component_path, "__init__.py"), "w") as file:
            file.write(f"# {component_name} component\n")

        # Create placeholder files
        files = ["views.py", "serializers.py", "tests.py"]
        for file_name in files:
            with open(os.path.join(component_path, file_name), "w") as file:
                file.write(f"# {file_name} for {component_name}\n")

    def _update_initialization(self, component_name):
        init_file = os.path.join(self.COMPONENTS_DIR, "__init__.py")
        with open(init_file, "a") as file:
            file.write(f"from .{component_name} import *\n")

    def _add_views(self, component_name, functions):
        views_file = os.path.join(self.COMPONENTS_DIR, component_name, "views.py")
        with open(views_file, "a") as file:
            for func in functions:
                func_name = func["name"]
                file.write(
                    f"""
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def {func_name}(request):
    \"\"\"{func_name} view for {component_name}\"\"\"
    # TODO: Implement logic here
    return Response({{"message": "{func_name} executed successfully"}})
"""
                )

    def _add_serializers(self, component_name, functions):
        serializers_file = os.path.join(
            self.COMPONENTS_DIR, component_name, "serializers.py"
        )
        with open(serializers_file, "a") as file:
            for func in functions:
                func_name = func["name"]
                file.write(
                    f"""
from rest_framework import serializers

class {func_name.capitalize()}Serializer(serializers.Serializer):
    \"\"\"Serializer for {func_name} in {component_name}\"\"\"
"""
                )
                for param, details in func["parameters"].items():
                    field_type = "CharField"  # Default to CharField; you can map this dynamically
                    file.write(
                        f"    {param} = serializers.{field_type}(required={details['required']}, max_length={details['max_length']})\n"
                    )

    def _add_unit_tests(self, component_name, functions):
        tests_file = os.path.join(self.COMPONENTS_DIR, component_name, "tests.py")
        with open(tests_file, "a") as file:
            for func in functions:
                func_name = func["name"]
                file.write(
                    f"""
from django.test import TestCase

class {func_name.capitalize()}TestCase(TestCase):
    \"\"\"Unit test for {func_name} in {component_name}\"\"\"

    def test_{func_name}(self):
        # TODO: Implement unit test
        self.assertTrue(True)
"""
                )
