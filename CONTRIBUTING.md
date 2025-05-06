# Contributing to Smart Orb

First off, thank you for considering contributing to Smart Orb! It's people like you that make this project a great tool for health and wellness enhancement.

## Important Intellectual Property Notice

Before contributing to the Smart Orb project, please be aware of the following intellectual property considerations:

- The Smart Orb technology is owned by Ucaretron Inc. and is protected under Patent Application No. KR10-2024-0071235 ("Electrochemical Impedance and TENS-based Multi-Sensory Integrated Neuro-Modulation Wearable Smart Device and System").
- While the **software code** in this repository is released under the MIT License, the **core technology, methodologies, and processes** described are proprietary to Ucaretron Inc.
- By contributing to this project, you acknowledge that your contributions to the software code will be licensed under the MIT License, but you do not acquire any rights to the proprietary technology.
- Any contributions that significantly extend or modify the core proprietary technology may require a Contributor License Agreement (CLA) with Ucaretron Inc.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

**Before Submitting A Bug Report**

* Check the issues section to see if the bug has already been reported.
* Make sure your software is up to date.
* Collect information about your environment (OS, Python version, package versions).

**How Do I Submit A Good Bug Report?**

Bugs are tracked as GitHub issues. Create an issue and provide the following information:

* Use a clear and descriptive title.
* Describe the exact steps to reproduce the problem.
* Describe the behavior you observed after following the steps.
* Explain which behavior you expected to see instead and why.
* Include screenshots or animated GIFs if possible.
* Include details about your configuration and environment.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

**How Do I Submit A Good Enhancement Suggestion?**

Enhancement suggestions are tracked as GitHub issues. Create an issue and provide the following information:

* Use a clear and descriptive title.
* Provide a detailed description of the suggested enhancement.
* Describe the current behavior and explain why the suggested enhancement would be useful.
* Include mockups or diagrams of the proposed functionality if possible.
* Explain why this enhancement would be useful to most Smart Orb users.

### Pull Requests

* Fill in the required template.
* Follow the Python style guide.
* Include appropriate tests.
* End all files with a newline.
* Update the documentation to reflect changes.
* **Important**: Ensure your contributions respect the intellectual property boundaries described above.

## Development Environment Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/Smart-Orb.git`
3. Create a branch for your feature: `git checkout -b feature/my-new-feature`
4. Install development dependencies: `pip install -r requirements-dev.txt`
5. Make your changes and ensure tests pass
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to the branch: `git push origin feature/my-new-feature`
8. Submit a pull request to the `main` branch

## Styleguides

### Python Styleguide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/).
* Use 4 spaces for indentation (not tabs).
* Use docstrings for functions, classes, and modules.
* Use type hints for function parameters and return values.
* Keep line length to a maximum of 100 characters.
* Run `pylint` and `black` before submitting your changes.

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature").
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
* Limit the first line to 72 characters or less.
* Reference issues and pull requests after the first line.
* Consider starting the commit message with an applicable emoji:
  * 🎨 `:art:` when improving the format/structure of the code
  * 🐎 `:racehorse:` when improving performance
  * 🔒 `:lock:` when dealing with security
  * 📝 `:memo:` when writing docs
  * 🐛 `:bug:` when fixing a bug
  * 🔥 `:fire:` when removing code or files
  * 💚 `:green_heart:` when fixing the CI build
  * ✅ `:white_check_mark:` when adding tests
  * ⬆️ `:arrow_up:` when upgrading dependencies
  * ⬇️ `:arrow_down:` when downgrading dependencies

## Special Notes on Hardware Contributions

When contributing hardware design changes, please:

* Ensure all designs are compatible with common 3D printing technologies
* Include detailed documentation of component specifications
* Consider accessibility and ergonomics in all physical designs
* Test designs with actual prototypes when possible
* Note that hardware designs may be more closely tied to Ucaretron Inc.'s proprietary technology; consult before making significant changes

## Intellectual Property and Legal Boundaries

To ensure that contributions respect Ucaretron Inc.'s intellectual property:

1. Focus contributions on improving the software implementation, user interface, documentation, and testing.
2. Avoid modifying or extending the core algorithms and methodologies that constitute the proprietary technology.
3. If you're unsure whether your contribution might affect the proprietary technology, please ask for guidance by opening an issue or contacting the maintainers.

## Code of Conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

Feel free to contact the project maintainers if you have any questions. We're here to help!

For intellectual property or licensing questions, please contact Ucaretron Inc. directly.
