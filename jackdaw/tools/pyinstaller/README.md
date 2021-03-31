
Steps:
0. clone the project and install it, preferably to a venv. Venv is preferred not to have colliding module versions.
1. python lib folder: decompress sqlalchemy folder from the sqlalchemy's ".egg" to the same folder where the egg file is. This is needed as pyinstaller only works with non-compressed modules
2. make sure that the bundle.js file is present in the the jackdaw/nest/site/nui/dist/ folder! If it isn't then you'd need to compile it as described in the main readme.
3. ```pyinstaller -F jackdaw\tools\pyinstaller\__main__.spec```
4. executable will appear in the ./dist/ folder
