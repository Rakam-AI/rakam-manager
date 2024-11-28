import pytest
import os
import yaml
import shutil
from unittest.mock import MagicMock, mock_open, patch
from rakam_manager.project_manager import ProjectManager


@pytest.fixture
def project_manager():
    return ProjectManager()


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a temporary mock configuration file."""
    config_file = tmp_path / "system_config.yaml"
    config_data = {
        "ServerGroups": [
            {
                "name": "default",
                "components": [],
            }
        ]
    }
    with open(config_file, "w") as f:
        yaml.safe_dump(config_data, f)
    return config_file


def test_project_manager_init_no_config_file(mocker):
    mocker.patch("os.path.exists", return_value=False)
    with pytest.raises(FileNotFoundError):
        ProjectManager()


def test_project_manager_init_with_config_file(mocker, mock_config_file):
    mocker.patch("os.path.exists", return_value=True)
    pm = ProjectManager()
    assert pm is not None


def test_create_project_success(mocker, mock_config_file, tmp_path):
    # Mock BASE_TEMPLATE_DIR and CONFIG_FILE to use test paths
    mock_base_template_dir = tmp_path / "base_template"
    mock_base_template_dir.mkdir()
    mock_config_file.write_text("ServerGroups: []")

    mocker.patch(
        "rakam_manager.project_manager.ProjectManager.BASE_TEMPLATE_DIR",
        str(mock_base_template_dir),
    )
    mocker.patch(
        "rakam_manager.project_manager.ProjectManager.CONFIG_FILE",
        str(mock_config_file),
    )
    mocker.patch(
        "os.path.exists",
        side_effect=lambda path: path
        in [str(mock_base_template_dir), str(mock_config_file)],
    )
    mocker.patch("shutil.copytree")

    pm = ProjectManager()
    pm.create_project("test_project")

    shutil.copytree.assert_called_with(str(mock_base_template_dir), "test_project")


def test_create_project_already_exists(mocker):
    mocker.patch("os.path.exists", return_value=True)

    pm = ProjectManager()
    with pytest.raises(FileExistsError):
        pm.create_project("test_project")


def test_generate_component_package(mocker):
    mocker.patch("os.makedirs")
    mock_open_init = mock_open()
    mocker.patch("builtins.open", mock_open_init)

    pm = ProjectManager()
    pm.generate_component_package("test_component", "path/to/component")

    os.makedirs.assert_called_with("path/to/component", exist_ok=True)
    mock_open_init.assert_any_call("path/to/component/__init__.py", "w")
    mock_open_init.assert_any_call("path/to/component/test_component_functions.py", "w")


def test_add_component(mocker, mock_config_file):
    mocker.patch("os.path.exists", return_value=True)
    mock_open_file = mock_open(
        read_data=yaml.safe_dump({"ServerGroups": [{"components": []}]})
    )
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.CONFIG_FILE = str(mock_config_file)
    pm.add_component("test_component")

    mock_open_file().write.assert_called()


def test_delete_component_not_found(mocker, mock_config_file):
    mock_open_file = mock_open(
        read_data=yaml.safe_dump({"ServerGroups": [{"components": []}]})
    )
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.CONFIG_FILE = str(mock_config_file)

    with pytest.raises(ValueError):
        pm.delete_component("non_existent_component")


def test_delete_component_success(mocker, mock_config_file):
    mock_open_file = mock_open(
        read_data=yaml.safe_dump(
            {"ServerGroups": [{"components": [{"test_component": {}}]}]}
        )
    )
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.CONFIG_FILE = str(mock_config_file)
    pm.delete_component("test_component")

    mock_open_file().write.assert_called()


def test_add_function_to_component_success(mocker, mock_config_file):
    mock_open_file = mock_open(
        read_data=yaml.safe_dump(
            {"ServerGroups": [{"components": [{"test_component": {}}]}]}
        )
    )
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.CONFIG_FILE = str(mock_config_file)
    pm.add_function_to_component(
        "test_component", "test_function", {"param1": {"type": "str", "required": True}}
    )

    mock_open_file().write.assert_called()


def test_delete_function_from_component(mocker, mock_config_file):
    mock_open_file = mock_open(
        read_data=yaml.safe_dump(
            {
                "ServerGroups": [
                    {"components": [{"test_component": {"test_function": {}}}]}
                ]
            }
        )
    )
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.CONFIG_FILE = str(mock_config_file)
    pm.delete_function_from_component("test_component", "test_function")

    mock_open_file().write.assert_called()


def test_modify_function_in_component_success(mocker, mock_config_file):
    mock_open_file = mock_open(
        read_data=yaml.safe_dump(
            {
                "ServerGroups": [
                    {"components": [{"test_component": {"test_function": {}}}]}
                ]
            }
        )
    )
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.CONFIG_FILE = str(mock_config_file)
    pm.modify_function_in_component(
        "test_component",
        "test_function",
        {"param1": {"type": "int", "required": False}},
    )

    mock_open_file().write.assert_called()


def test_generate_function_skeleton(mocker):
    mock_open_file = mock_open()
    mocker.patch("builtins.open", mock_open_file)

    pm = ProjectManager()
    pm.generate_function_skeleton(
        "test_component",
        "path/to/component",
        "test_function",
        {"param1": {"type": "str"}},
        "str",
    )

    mock_open_file().write.assert_called()
