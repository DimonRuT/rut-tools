````markdown
# RuT Tools

RuT Tools is a command-line utility designed for developers and users, offering a user-friendly interface with support for color themes, a modular command system, and automatic dependency installation.

## Features

- Flexible command system with namespaces
- Support for multiple color themes (lime, blue, etc.)
- Automatic installation of dependencies via pip
- Auto-update from GitHub repository
- Logging and developer mode (dev mode)
- Detailed help and command descriptions
- Easy integration of external libraries as modules

## Installation and Usage

1. Make sure you have Python 3.8 or higher installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/your-username/rut-tools.git
````

3. Navigate to the project directory:

   ```bash
   cd rut-tools
   ```
4. Run the program:

   ```bash
   python rut.py
   ```

## Updates

RuT Tools can automatically check for updates from GitHub and update itself with the command:

```bash
rut.core update
```

## Commands

To see the available commands, use:

```bash
help
```

Commands follow the format:

```bash
rut.<namespace> <command> [arguments]
```

## Support and Contacts

Join our Discord server: [dsc.gg/ruttools](https://dsc.gg/ruttools)
