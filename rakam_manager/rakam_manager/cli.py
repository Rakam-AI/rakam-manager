import click
import json
from rakam_manager.project_manager import ProjectManager
import os


@click.group()
def cli():
    """Rakam Manager CLI - Manage your projects easily."""
    pass


@cli.command()
@click.option("--name", required=True, help="Name of the project to create.")
def create_project(name):
    """Create a new project based on the base template."""
    pm = ProjectManager()
    # pm.project_path = project_path
    try:
        pm.create_project(name)
        click.echo(f"Project '{name}' created successfully.")
    except Exception as e:
        click.echo(f"Error creating project '{name}': {e}")


@cli.command()
@click.option("--name", required=True, help="Name of the component to add.")
@click.option(
    "--project-path", required=True, help="Path to the project configuration file."
)
def add_component(name, project_path):
    """Add a new component to the project."""
    pm = ProjectManager()
    pm.CONFIG_FILE = os.path.join(project_path, "system_config.yaml")
    component_path = os.path.join(
        project_path, "application/rakam_systems/rakam_systems/components", name
    )
    init_component_path = os.path.join(project_path, "application/engine/components.py")
    try:
        if pm.add_component(name):
            click.echo(f"Component '{name}' added successfully.")
            pm.generate_component_package(name, component_path)  # Generate the package
            pm.update_components_file(
                name, init_component_path
            )  # Update the components.py file
            click.echo(f"Component '{name}' added and package generated successfully.")
        else:
            click.echo(f"Component '{name}' already exists.")
    except Exception as e:
        click.echo(f"Error adding component '{name}': {e}")


import click
import json
import os
from typing import get_type_hints, Any, Union, List, Dict, Tuple, Optional
from typeguard import check_type


def is_valid_type(type_name: str) -> bool:
    """
    Validate if the given type name corresponds to a valid Python type.
    """
    try:
        # Try to evaluate the type
        eval(type_name, globals(), locals())
        return True
    except Exception:
        return False


def add_function(component, project_path):
    """Add a new function to a component interactively."""
    try:
        # Ask user for function details
        function_name = click.prompt("Enter the function name", type=str)

        # Validate output type
        while True:
            output_type = click.prompt(
                "Enter the output type of the function", type=str
            )
            if is_valid_type(output_type):
                break
            click.echo(
                f"Invalid output type: '{output_type}'. Please enter a valid Python type."
            )

        parameters = {}
        add_more = True

        while add_more:
            param_name = click.prompt("Enter the parameter name", type=str)

            # Validate parameter type
            while True:
                param_type = click.prompt(
                    f"Enter the type for parameter '{param_name}'", type=str
                )
                if is_valid_type(param_type):
                    break
                click.echo(
                    f"Invalid type: '{param_type}'. Please enter a valid Python type."
                )

            required = click.confirm(f"Is parameter '{param_name}' required?")

            max_length = None
            if param_type.lower() in ["str", "bytes", "list", "tuple", "dict"]:
                max_length = click.prompt(
                    f"Enter the max_length for parameter '{param_name}' (or 0 if not applicable)",
                    type=int,
                    default=0,
                )

            parameters[param_name] = {
                "type": param_type,
                "required": required,
                "max_length": max_length if max_length and max_length > 0 else None,
            }
            add_more = click.confirm("Do you want to add another parameter?")

        # Generate the function structure
        function_structure = {
            "name": function_name,
            "parameters": parameters,
            "output_type": output_type,
        }

        click.echo("Generated Function Details:")
        click.echo(json.dumps(function_structure, indent=4))

        # Add the function to the component
        pm = ProjectManager()
        pm.CONFIG_FILE = os.path.join(project_path, "system_config.yaml")
        component_path = os.path.join(
            project_path,
            "application/rakam_systems/rakam_systems/components",
            component,
        )
        if pm.add_function_to_component(component, function_name, parameters):
            pm.generate_function_skeleton(
                component, component_path, function_name, parameters, output_type
            )
            pm.update_views_and_serializers(
                project_path, component, function_name, parameters, output_type
            )
            click.echo(
                f"Function '{function_name}' added successfully to component '{component}'."
            )
        else:
            click.echo(
                f"Function '{function_name}' already exists in component '{component}'."
            )

    except Exception as e:
        click.echo(f"Error adding function: {e}")


@cli.command()
@click.option("--name", required=True, help="Name of the component to delete.")
@click.option(
    "--project-path", required=True, help="Path to the project configuration file."
)
def delete_component(name, project_path):
    """Delete a component from the project."""
    pm = ProjectManager()
    pm.CONFIG_FILE = os.path.join(project_path, "system_config.yaml")
    try:
        pm.delete_component(name)
        click.echo(f"Component '{name}' deleted successfully.")
    except Exception as e:
        click.echo(f"Error deleting component '{name}': {e}")


@cli.command()
@click.option(
    "--component",
    required=True,
    help="Name of the component to delete the function from.",
)
@click.option("--function", required=True, help="Name of the function to delete.")
@click.option(
    "--project-path", required=True, help="Path to the project configuration file."
)
def delete_function(component, function, project_path):
    """Delete a function from a component."""
    pm = ProjectManager()
    pm.CONFIG_FILE = os.path.join(project_path, "system_config.yaml")
    try:
        pm.delete_function_from_component(component, function)
        click.echo(
            f"Function '{function}' deleted from component '{component}' successfully."
        )
    except Exception as e:
        click.echo(f"Error deleting function '{function}': {e}")


@cli.command()
@click.option(
    "--component",
    required=True,
    help="Name of the component to modify the function in.",
)
@click.option("--function", required=True, help="Name of the function to modify.")
@click.option(
    "--parameters",
    required=True,
    help=(
        "New parameters for the function as a JSON string. "
        'Example: \'{"param1": {"required": true, "max_length": 128}}\'.'
    ),
)
@click.option(
    "--project-path", required=True, help="Path to the project configuration file."
)
def modify_function(component, function, parameters, project_path):
    """Modify an existing function in a component."""
    pm = ProjectManager()
    pm.CONFIG_FILE = os.path.join(project_path, "system_config.yaml")
    try:
        params_dict = json.loads(parameters)
        if not isinstance(params_dict, dict):
            raise ValueError(
                "Parameters must be a JSON object of parameter definitions."
            )

        pm.modify_function_in_component(component, function, params_dict)
        click.echo(
            f"Function '{function}' in component '{component}' modified successfully."
        )
    except json.JSONDecodeError:
        click.echo("Error: The 'parameters' option must be a valid JSON string.")
    except Exception as e:
        click.echo(f"Error modifying function '{function}': {e}")


@cli.command()
@click.option(
    "--project-path", required=True, help="Path to the project configuration file."
)
def deploy(project_path):
    """Deploy the project."""
    pm = ProjectManager()
    pm.CONFIG_FILE = os.path.join(project_path, "system_config.yaml")
    try:
        pm.deploy()
        click.echo("Project deployed successfully.")
    except Exception as e:
        click.echo(f"Error deploying project: {e}")


if __name__ == "__main__":
    cli()
