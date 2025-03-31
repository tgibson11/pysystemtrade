import os

from syscore.interactive.menus import interactiveMenu, print_menu_and_get_desired_option_index
from sysdata.config.private_directory import PRIVATE_CONFIG_DIR_ENV_VAR


class Account:
    def __init__(self, name: str, config_subdir: str):
        self.name = name
        self.config_subdir = config_subdir

    def use(self):
        set_config_subdir(self.config_subdir)


class Accounts:
    LLC = Account(name="LLC account", config_subdir="llc")
    PERSONAL = Account(name="Personal account", config_subdir="personal")


def use_account_interactive():
    top_menu = {
        0: Accounts.LLC.name,
        1: Accounts.PERSONAL.name,
    }

    functions = {
        0: Accounts.LLC.use,
        1: Accounts.PERSONAL.use,
    }

    menu = UseAccountMenu(top_menu, functions)
    menu.run_menu()


def set_config_subdir(config_subdir: str):
    private_config_base_dir = os.environ[PRIVATE_CONFIG_DIR_ENV_VAR]
    private_config_subdir = config_subdir
    os.environ[PRIVATE_CONFIG_DIR_ENV_VAR] = \
        f"{private_config_base_dir}\\{private_config_subdir}"


class UseAccountMenu(interactiveMenu):
    def __init__(
        self,
        top_level_menu_of_options: dict,
        dict_of_functions: dict,
        *args,
        **kwargs,
    ):
        nested_menu = {}
        super().__init__(
            top_level_menu_of_options,
            nested_menu,
            dict_of_functions,
            *args,
            **kwargs,
        )

    def run_menu(self):
        option_chosen = self.propose_options_and_get_input()
        method_chosen = self._dict_of_functions[option_chosen]
        method_chosen(*self._args, **self._kwargs)

    def propose_options_and_get_input(self):
        option_chosen = print_menu_and_get_desired_option_index(
            self.top_level_menu,
            default_option_index=0,
        )
        return option_chosen
