from helper import gen_constituents, gen_tag_counts
from flask import Flask, render_template, request, send_file
import io
import zipfile


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def upload():
        return render_template('index.html')
    
    @app.route('/output', methods=['POST'])
    def get_outputs():
        c_input = request.files.get("c_input")
        e_input = request.files.get("e_input")
        dh_input = request.files.get("dh_input")
        c_df = gen_constituents(c_input, e_input, dh_input)
        t_df = gen_tag_counts(c_df)
        c_buffer = io.StringIO()
        t_buffer = io.StringIO()
        c_df.to_csv(c_buffer, index=False)
        t_df.to_csv(t_buffer, index=False)
        c_buffer.seek(0)
        t_buffer.seek(0)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            z.writestr('cuebox_constituents.csv', c_buffer.getvalue())
            z.writestr('cuebox_tags.csv', t_buffer.getvalue())
        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='cuebox_output.zip')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)