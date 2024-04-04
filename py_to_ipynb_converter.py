import nbformat

py_name = 'gmaps_api_playground.py'

# Read the .py file
with open(py_name, 'r') as f:
    code = f.read()

# Create a new notebook
nb = nbformat.v4.new_notebook()

# Add the code from the .py file to a code cell in the notebook
nb.cells.append(nbformat.v4.new_code_cell(code))

# Save the notebook to a .ipynb file
nbformat.write(nb, f'{py_name}.ipynb')