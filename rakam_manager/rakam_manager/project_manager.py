import traceback
from typing import Optional
import ast
import os
import re
import shutil
import subprocess
from typing import Dict, List, Tuple

import yaml

from dotenv import load_dotenv


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

    def load_system_config(self, path: str = None):
        if path is None:
            path = self.BASE_TEMPLATE_DIR
        # Load environment variables from .env file
        dotenv_path = os.path.join(path, '.env')
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)

        # Load and parse the YAML configuration file
        with open(os.path.join(path, 'system_config.yaml'), "r") as file:
            config = yaml.safe_load(os.path.expandvars(file.read()))
        return config

    def generate_build(self, project_path):
        dist = os.path.join(project_path, 'dist')
        if os.path.exists(dist):
            shutil.rmtree(dist)

        shutil.copytree(
            self.BASE_TEMPLATE_DIR,
            dist
        )
        shutil.rmtree(os.path.join(dist, 'application', 'rakam_systems'))
        # Iterate over all items in the current directory
        for item in os.listdir(project_path):
            if item in ['dist', 'venv']:
                continue
            source_path = os.path.join(project_path, item)
            destination_path = os.path.join(
                dist, 'application',  'rakam_systems', item)

            # Copy files and directories
            if os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path,
                                dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, destination_path)
        config = self.load_system_config(project_path)
        # Add the new component
        if not config["ServerGroups"][0]["components"]:
            config["ServerGroups"][0]["components"] = []
        init_component_path = os.path.join(
            dist, "application/engine/components.py")
        views_path = os.path.join(dist, 'application/views.py')
        urls_path = os.path.join(dist, 'application/urls.py')
        serializrs_path = os.path.join(dist, 'application/serializers.py')
        for item in config["ServerGroups"][0]["components"]:
            for i in item:
                if i.islower():
                    component_functions_path = os.path.join(
                        dist,
                        "application/rakam_systems/rakam_systems/components",
                        i,
                        f'{i}_functions.py'
                    )
                    self.update_components_file(
                        i, init_component_path,
                        component_functions_path, project_path
                    )
                    self.update_views(
                        i,
                        component_functions_path,
                        views_path,
                        urls_path,
                        serializrs_path
                    )

        with open(self.CONFIG_FILE, "w") as file:
            yaml.safe_dump(config, file, default_flow_style=False)
        return True

    def create_project(self, project_name):
        if not os.path.exists(self.BASE_TEMPLATE_DIR):
            raise FileNotFoundError("Base template directory does not exist.")

        if os.path.exists(project_name):
            raise FileExistsError(f"Project '{project_name}' already exists.")

        shutil.copytree(
            os.path.join(self.BASE_TEMPLATE_DIR, 'application',
                         'rakam_systems'),
            project_name
        )
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

    def _to_camel_case_class_name(self, input_string: str) -> str:
        """
        Convert a given string to a proper class name in CamelCase convention.

        Args:
            input_string (str): The string to convert.

        Returns:
            str: The converted class name.
        """
        # Remove any non-alphanumeric characters and replace them with spaces
        cleaned_string = re.sub(r'[^a-zA-Z0-9]', ' ', input_string)

        # Split the string into words, capitalize each, and join them
        camel_case_name = ''.join(
            word.capitalize()
            for word in cleaned_string.split()
        )

        return camel_case_name

    def _format_file(self, file_path):
        """
        format file .
        """
    # Redirect output and errors to /dev/null
        with open("/dev/null", "w") as devnull:
            subprocess.run(
                ["black", file_path], stdout=devnull,
                stderr=devnull, check=True
            )

    def _add_url_entry(self, url_file_path, url_route, view_name, url_name):
        """
        Adds a new path entry to a Django `urls.py` file.

        Args:
            file_name (str): Path to the `urls.py` file.
            url_path (str): The URL pattern (e.g., 'new-view/').
            view_name (str): The view function name (e.g., 'views.new_view').
            url_name (str): The name for the URL pattern (e.g., 'new_view').
        """
        # Load the existing `urls.py` file
        with open(url_file_path, "r") as file:
            original_code = file.read()

        # Parse the file into an AST
        tree = ast.parse(original_code)

        # Locate the `urlpatterns` and add the new path
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id == "urlpatterns" and isinstance(node.value, ast.List):
                    # Construct the new path() call
                    new_path = ast.Call(
                        func=ast.Name(id="path", ctx=ast.Load()),
                        args=[
                            ast.Constant(value=url_route),  # URL
                            ast.Attribute(value=ast.Name(id="views", ctx=ast.Load(
                            )), attr=view_name, ctx=ast.Load()),  # View function
                            ast.keyword(arg="name", value=ast.Constant(
                                value=url_name)),  # Name
                        ],
                        keywords=[]
                    )
                    # Append the new path to urlpatterns
                    node.value.elts.append(new_path)
                    break

        # Generate updated code
        # unparse only available py3.9+
        # TODO: discuss if we needd to use astor instead
        updated_code = ast.unparse(tree)

        # Step 5: Save the modified `urls.py` back
        with open(url_file_path, "w") as file:
            file.write(updated_code)
        # Optional instruction for better visibility
        self._format_file(url_file_path)

        print(f"Added URL entry '{url_route}' to {url_file_path}.")

    def _find_component_class(self, file_path) -> Optional[ast.ClassDef]:
        """
        Finds the first class in a Python file that inherits from a class named 'Component'.

        Args:
            file_path (str): The path to the Python file to analyze.

        Returns:
            Optional[ast.ClassDef]: The first class definition node that inherits from 'Component',
            or None if no such class is found.
        """
        # Read and parse the Python file
        with open(file_path, "r") as file:
            tree = ast.parse(file.read())

        # Traverse the AST to find classes that inherit from `Component`
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):  # Check for class definitions
                for base in node.bases:  # Check if the class inherits from `Component`
                    if isinstance(base, ast.Name) and base.id == "Component":
                        return node
        return None

    def _find_public_method_component_classes(self, file_path):
        """
        Finds classes in a Python file that inherit from a class named 'Component'
        and return their public methods.

        Args:
            file_name (str): The path to the Python file to analyze.
        """
        node = self._find_component_class(file_path)
        if node is None:
            return []
        methods: List[ast.FunctionDef] = []
        # Loop through the methods of the class
        for body_item in node.body:
            # Check for function definitions
            if isinstance(body_item, ast.FunctionDef):
                # Public methods are those not starting with an underscore
                # also ignore test methods
                if not body_item.name.startswith("_") and not body_item.name.startswith('test'):
                    methods.append(body_item)

        return methods

    def _create_view_from_component_methods(self, component_name: str, component_methods: List[ast.FunctionDef], views_file_path):
        """
        Creates Django function views in `views.py` using AST, based on public methods
        of classes inheriting from `Component`.

        Args:
            component_name (str): name of thee component.
            component_methods (List[ast.FunctionDef]): public methods from a `Component` class.
            views_file_path (str): The `views.py` file to write the function views to.
        """

        if not component_methods:
            print(
                f"No public methods found."
            )
            return

        # Read the existing target file content
        try:
            with open(views_file_path, "r") as file:
                existing_code = ast.parse(file.read())
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty module
            existing_code = ast.Module(body=[], type_ignores=[])

        # Add necessary imports if not already present
        imports = [
            ast.ImportFrom(module="rest_framework.decorators", names=[
                           ast.alias(name="api_view")], level=0),
            ast.ImportFrom(module="rest_framework.request", names=[
                           ast.alias(name="Request")], level=0),


        ]

        for imp in imports:
            if not any(isinstance(node, ast.ImportFrom) and node.module == imp.module for node in existing_code.body):
                existing_code.body.insert(0, imp)

        # Generate views
        for method in component_methods:

            # Create a function view for the public method
            serializer_name = self._to_camel_case_class_name(
                f"{component_name} {method.name} Serializer"
            )
            view_name = f"{component_name}_{method.name}_view"
            view_func = ast.FunctionDef(
                name=view_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[
                        ast.arg(
                            arg="request",
                            annotation=ast.Name(
                                id="Request", ctx=ast.Load()
                            )
                        )
                    ],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=[

                    # serializer = SerialzierClass(data=request.data)
                    ast.Assign(
                        targets=[ast.Name(id='serializer', ctx=ast.Load())],
                        value=ast.Call(
                            func=ast.Name(id=serializer_name, ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(
                                    arg='data',
                                    value=ast.Attribute(
                                        value=ast.Name(
                                            id="request", ctx=ast.Load()
                                        ),
                                        attr="data",
                                        ctx=ast.Load()
                                    )
                                )
                            ]
                        )
                    ),
                    # if serializer.is_valid():
                    ast.If(
                        test=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="serializer",
                                               ctx=ast.Load()),
                                attr="is_valid",
                                ctx=ast.Load()
                            ),
                            args=[],
                            keywords=[]
                        ),
                        body=[

                            # response = components.data_processor.call_process_file(**serializer.validated_data)
                            ast.Assign(
                                targets=[
                                    ast.Name(id="response", ctx=ast.Store())],
                                value=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Attribute(
                                            value=ast.Name(
                                                id="components", ctx=ast.Load()),
                                            attr=component_name,
                                            ctx=ast.Load()
                                        ),
                                        attr=method.name,
                                        ctx=ast.Load()
                                    ),
                                    args=[

                                    ],
                                    keywords=[
                                        ast.keyword(
                                            arg=None,
                                            value=ast.Attribute(
                                                value=ast.Name(
                                                    id="serializer", ctx=ast.Load()),
                                                attr="validated_data",
                                                ctx=ast.Load()
                                            ),
                                            ctx=ast.Load()

                                        )
                                    ]

                                ),
                            ),
                            # return Response(response, status=status.HTTP_200_OK)
                            ast.Return(
                                value=ast.Call(
                                    func=ast.Name(
                                        id="Response", ctx=ast.Load()),
                                    args=[
                                        ast.Name(id="response", ctx=ast.Load())
                                    ],
                                    keywords=[]
                                )
                            )
                        ],
                        # else block
                        orelse=[
                            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                            ast.Return(
                                value=ast.Call(
                                    func=ast.Name(
                                        id="Response", ctx=ast.Load()),
                                    args=[
                                        ast.Attribute(
                                            value=ast.Name(id="serializer",
                                                           ctx=ast.Load()),
                                            attr="errors",
                                            ctx=ast.Load()
                                        )
                                    ],
                                    keywords=[
                                        ast.keyword(
                                            arg="status",
                                            value=ast.Attribute(
                                                value=ast.Name(
                                                    id="status", ctx=ast.Load()),
                                                attr="HTTP_400_BAD_REQUEST",
                                                ctx=ast.Load()
                                            )
                                        )
                                    ]
                                )
                            )
                        ]
                    )

                ],
                decorator_list=[
                    ast.Call(
                        func=ast.Name(id="api_view", ctx=ast.Load()),
                        args=[
                            ast.List(elts=[ast.Constant(value="POST")], ctx=ast.Load())],
                        keywords=[]
                    )
                ]
            )

            # Avoid duplicate definitions
            if not any(isinstance(node, ast.FunctionDef) and node.name == view_name for node in existing_code.body):
                existing_code.body.append(view_func)

        # Write back the updated code to the target file
        updated_code = ast.unparse(ast.fix_missing_locations(existing_code))
        with open(views_file_path, "w") as file:
            file.write(updated_code)

        print(f"Views added to {views_file_path}.")

    def _create_serializers_from_component_methods(self, component_name: str, methods: List[ast.FunctionDef], serializers_file_path):
        """
        Creates serializers based on method arguments and return types.

        Args:
            methods (list): List of methods with arguments and return types.
            serializers_file_path (str): The `serializers.py` file to write the serializers to.
        """

        if not methods:
            print(
                f"No public methods found."
            )
            return

        # Read the existing target file content
        try:
            with open(serializers_file_path, "r") as file:
                existing_code = ast.parse(file.read())
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty module
            existing_code = ast.Module(body=[], type_ignores=[])

        # Add necessary imports if not already present
        imports = [
            ast.ImportFrom(
                module="rest_framework",
                names=[
                    ast.alias(name="serializer"),
                    # ast.alias(name="Serializer"),
                    # ast.alias(name="CharField"),
                    # ast.alias(name="IntegerField"),
                    # ast.alias(name="DictField")
                ],
                level=0
            ),
        ]

        for imp in imports:
            if not any(isinstance(node, ast.ImportFrom) and node.module == imp.module for node in existing_code.body):
                existing_code.body.insert(0, imp)

        # Generate serializers
        for method in methods:

            method_name = method.name
            serializer_name = self._to_camel_case_class_name(
                f"{component_name} {method.name} Serializer"
            )
            return_type = ast.unparse(
                method.returns
            ) if method.returns else None
            type_hints = {}
            for arg in method.args.args:
                if arg.arg == 'self':
                    continue
                type_hints[arg.arg] = ast.unparse(
                    arg.annotation
                ) if arg.annotation else None

            # Generate fields based on type hints
            fields = []
            for arg_name, arg_type in type_hints.items():
                field_type = "CharField"  # Default to CharField
                if arg_type == 'int':
                    field_type = "IntegerField"
                elif arg_type == 'dict':
                    field_type = "DictField"
                fields.append(
                    ast.Assign(
                        targets=[ast.Name(id=arg_name, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(
                                    id='serializers',
                                    ctx=ast.Load()
                                ),
                                attr=field_type,
                                ctx=ast.Load()
                            ),
                            args=[],
                            keywords=[]
                        )
                        # value=ast.Call(
                        #     func=ast.Name(id=field_type, ctx=ast.Load()),
                        #     args=[],
                        #     keywords=[]
                        # ),
                    )
                )
            # Create the serializer class
            serializer_class = ast.ClassDef(
                name=serializer_name,
                bases=[
                    ast.Attribute(
                        value=ast.Name(
                            id='serializers',
                            ctx=ast.Load()
                        ),
                        attr='Serializer',
                        ctx=ast.Load()
                    ),
                    # ast.Name(id="Serializer", ctx=ast.Load())

                ],
                keywords=[],
                body=fields if fields else [ast.Pass()],
                decorator_list=[],
            )

            # Avoid duplicate definitions
            if not any(isinstance(node, ast.ClassDef) and node.name == serializer_name for node in existing_code.body):
                existing_code.body.append(serializer_class)

        # Write back the updated code to the target file
        updated_code = ast.unparse(ast.fix_missing_locations(existing_code))
        with open(serializers_file_path, "w") as file:
            file.write(updated_code)

        print(f"Serializers added to {serializers_file_path}.")

    def update_views(self, component_name, component_functions_path, view_file_path, url_file_path, serializers_file_path):
        methods = self._find_public_method_component_classes(
            component_functions_path
        )
        self._create_serializers_from_component_methods(
            component_name, methods, serializers_file_path
        )
        self._create_view_from_component_methods(
            component_name, methods, view_file_path
        )
        for method in methods:
            self._add_url_entry(
                url_file_path, f'external/{component_name}/{method.name}/', f"{method.name}_view", f"{method.name}_view"
            )

    def add_component(self, component_name):
        """
        Add a new component to the YAML file if it does not already exist.
        """
        config = self.load_system_config(self.CONFIG_FILE)

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
        config = self.load_system_config(self.CONFIG_FILE)

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
        config = self.load_system_config(self.CONFIG_FILE)

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

        config = self.load_system_config(self.CONFIG_FILE)

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

        config = self.load_system_config(self.CONFIG_FILE)

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
        SERIALIZERS_FILE = os.path.join(
            project_path, "application/serializers.py")
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
                print(
                    f"Serializer for '{function_name}' added to serializers.py.")

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
            output_schema = type_mapping.get(
                output_type.lower(), {"type": "object"})
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

        config = self.load_system_config(self.CONFIG_FILE)

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

    def update_components_file(self, component_name, init_component_path, component_path, project_path):
        """
        Update the components.py file to import and initialize the new component.
        :param component_name: Name of the new component.
        :param init_component_path: Path to the components.py file.
        """
        try:
            config = self.load_system_config(project_path)
            config_envs = config['envs'] if 'envs' in config else {}

            component = self._find_component_class(component_path)
            if component is None:
                raise ValueError(
                    f"Couldn't find {component_name} in {component_path}"
                )

            # Read and parse the existing components.py file
            with open(init_component_path, "r") as components_file:
                file_content = components_file.read()

            # Parse the file content into an AST
            existing_code = ast.parse(file_content)

            # Check if the component already exists
            for node in existing_code.body:
                if isinstance(node, ast.ImportFrom) and node.module == f"rakam_systems.components.{component_name}.{component_name}_functions":
                    print(
                        f"Component '{component_name}' already exists in components.py.")
                    return
                if isinstance(node, ast.Assign) and node.targets[0].id == component_name.lower():
                    print(
                        f"Component '{component_name}' is already initialized in components.py.")
                    return

            # Define the new import and initialization nodes
            import_statement = ast.ImportFrom(
                module=f"rakam_systems.components.{component_name}.{component_name}_functions",
                names=[
                    ast.alias(name=component.name, asname=None)],
                level=0
            )
            # add import statement
            existing_code.body.insert(0, import_statement)
            args = [
                ast.keyword(arg="system_manager", value=ast.Name(
                            id="system_manager", ctx=ast.Load()))
            ]
            # Loop through the methods of the class
            for body_item in component.body:
                # Check for function definitions
                if isinstance(body_item, ast.FunctionDef):
                    # Public methods are those not starting with an underscore
                    # also ignore test methods
                    if body_item.name == '__init__':
                        for arg in body_item.args.args:
                            arg_key = arg.arg
                            if arg_key in ['self', 'system_manager']:
                                continue
                            if arg_key not in config_envs:
                                raise ValueError(
                                    f"Missing {arg_key} from config files.")
                            args.append(
                                ast.keyword(
                                    arg=arg.arg, value=ast.Constant(
                                        value=config_envs[arg_key], ctx=ast.Load(
                                        )
                                    )
                                )
                            )

            init_statement = ast.Assign(
                targets=[ast.Name(id=component_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(
                        id=component.name,
                        ctx=ast.Load()
                    ),
                    args=args,
                    keywords=[]
                )
            )
            # Add the initialization statement at the end of the file
            existing_code.body.append(init_statement)

            updated_code = ast.unparse(
                ast.fix_missing_locations(existing_code))
            with open(init_component_path, "w") as file:
                file.write(updated_code)

            print(
                f"Component '{component_name}' added to components.py successfully.")
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
        views_file = os.path.join(
            self.COMPONENTS_DIR, component_name, "views.py")
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
        tests_file = os.path.join(
            self.COMPONENTS_DIR, component_name, "tests.py")
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
