from flask import Flask
from flask import request, escape, render_template, jsonify
from waitress import serve
import project
# Import the code in the modules folder
#from modules. import



app = Flask(__name__,template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def app_home():
    '''Displays the home page.
    '''
    return render_template('index.html', result_text = "", word_d_background = "#fff", example_features="")

@app.route('/myFunction',methods=["GET", 'POST'])
def myFunction():
    '''Apply my function and returns the data as a dictionary.
    '''
    # The data we passed can be retrieved by:
    element = request.form.get("an_element_to_pass_to_python") # an_element_to_pass_to_python is the name we wrote in the html
    simp_sent=project.main(element)
    print("We are in the function.")
    print(f"The value of element is: {element}")
    output = {'an_element_to_pass_to_html': simp_sent}
    
    return jsonify(output)


if __name__ == "__main__":
    if app.config['DEBUG'] == True:
        app.run(debug=True)
    else:
        host = '127.0.0.1'
        port = 5000
        print(f"Launch the app on http://{host}:{port}")
        serve(app, host=host, port=port)

