from flask import Flask, render_template, send_file, request, redirect, url_for
from generate_graph import generate_graph

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate-graph", methods=['POST'])
def graph():
    try:
        start_block = int(request.form.get('start_block'))
        min_edge_val = float(request.form.get('min_edge_val'))
    except (ValueError, TypeError):
        return "Invalid input. Please enter valid numbers.", 400

    generate_graph(start_block, min_edge_val)
    return redirect(url_for('serve_graph'))

@app.route("/graph")
def serve_graph():
    return render_template("graph_wrapper.html")  

if __name__ == '__main__':
    app.run(debug=True)
