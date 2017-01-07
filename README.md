# morphling
Morphling is a convenient tool that converts Markdown to HTML.
---

## Usage

- **Command Line Mode**

    ```shell
    python -m morphling <markdown file> [options...]
    ```
- **Use morphling in your code**
    ```python
    from morphling import mdp

    mdp.parse(content)
    html = mdp.output
    ```