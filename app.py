import binascii
from datetime import datetime
from flask import Flask, render_template, flash, request, redirect, url_for
import logging
import os
import pathlib
import re
from werkzeug.utils import secure_filename

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ['FLASK_SECRET_KEY'],
    UPLOAD_FOLDER=os.path.join(basedir, 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024    # set maximum file size to 16 MiB
)

sid_validator = re.compile('^[0-9]{11}$', re.ASCII)


@app.route('/', methods=['GET', 'POST'])
def handle_form():
    if request.method == 'POST':
        if not request.form.get('student-id'):
            flash('No student ID')
            return redirect(request.url)
        sid = request.form.get('student-id')

        if not sid_validator.fullmatch(sid):
            flash('Student ID is not an 11-digit number')
            return redirect(request.url)

        # check if the post request has the file part
        if 'submission' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['submission']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        personal_folder = os.path.join(
            app.config['UPLOAD_FOLDER'],
            datetime.today().strftime('%Y-%m-%d'),
            sid
        )

        # save file to local file system
        pathlib.Path(personal_folder).mkdir(parents=True, exist_ok=True)
        filename = secure_filename(file.filename)
        file.save(os.path.join(personal_folder, filename))

        # calculate CRC32 checksum
        file.seek(0)
        checksum = binascii.crc32(file.read())

        # logging
        app.logger.info(f'Student [[{sid}]] submitted [[{filename}]] at [[{datetime.now()}]], CRC32 [[{checksum & 0xFFFFFFFF:#010X}]]')
        flash(f'CRC32({filename[:20] + (filename[20:] and "[...]")}) = {checksum & 0xFFFFFFFF:#010X}.')

        return redirect(url_for('handle_form'))

    return render_template('index.html')


if __name__ == '__main__':
    file_handler = logging.FileHandler('submission.log')
    app.logger.addHandler(file_handler)

    app.run(host='0.0.0.0', port=80, debug=True)
