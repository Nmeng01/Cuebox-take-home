from helper import gen_constituents, gen_tag_counts, validate_data
from flask import Flask, render_template, request, send_file
import pandas as pd
import io
import zipfile
import logging


def create_app():
    '''
    Initialize Flask app and relevant functions

    Routes:
        / (GET): renders home page
        /output (POST): processes input files and generates ZIP file containing the relevant output files
    
    Returns:
        Flask: instance of flask app
    '''
    app = Flask(__name__)

    @app.route('/')
    def upload():
        '''Render app home page'''
        return render_template('index.html')
    
    @app.route('/output', methods=['POST'])
    def get_outputs():
        '''
        Process input CSV files and send the outputs back to the user as a ZIP file attachment

        Returns:
            flask.Response: response object containing ZIP file attachment of the output data,
            or error message if data transformation fails
        '''
        # Read the input csv files into dataframes
        constituents_df = pd.read_csv(request.files.get("c_input"))
        emails_df = pd.read_csv(request.files.get("e_input"))
        dhist_df = pd.read_csv(request.files.get("dh_input"))
        # Ensure data is correctly formatted
        valid, msg = validate_data(constituents_df, emails_df, dhist_df)
        if not valid:
            return f'Error detected: {msg}'
        # Perform data transformation
        c_df = gen_constituents(constituents_df, emails_df, dhist_df)
        t_df = gen_tag_counts(c_df)
        # Read the output dataframes into string buffers
        c_buffer = io.StringIO()
        t_buffer = io.StringIO()
        c_df.to_csv(c_buffer, index=False)
        t_df.to_csv(t_buffer, index=False)
        c_buffer.seek(0)
        t_buffer.seek(0)
        # Compress the string buffers into one zip buffer
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as z:
            z.writestr('cuebox_constituents.csv', c_buffer.getvalue())
            z.writestr('cuebox_tags.csv', t_buffer.getvalue())
        zip_buffer.seek(0)

        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='cuebox_output.zip')

    return app

if __name__ == "__main__":
    '''Code entry point'''
    # Initialize global logger
    logging.basicConfig(
        filename='error_log.txt',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.ERROR
    )
    # Exclude flask messages from logger so that user can see them easily in the terminal
    flask_logger = logging.getLogger('werkzeug')
    flask_logger.propagate = False

    app = create_app()
    app.run(host="0.0.0.0", port=5000)